import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

st.set_page_config(page_title="ScriptSpy 🔍", layout="wide")


def apply_dark_theme() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #0f1117;
                color: #f3f3f3;
            }
            .stSidebar {
                background-color: #171a22;
            }
            .card {
                border: 1px solid #2b2f3a;
                border-radius: 14px;
                padding: 1rem;
                margin-bottom: 0.9rem;
                background: #171a22;
            }
            .muted {
                color: #9ba3b4;
                font-size: 0.92rem;
            }
            .timeline-item {
                border-left: 3px solid #4b82f0;
                margin-left: 0.4rem;
                padding-left: 0.9rem;
                margin-bottom: 0.9rem;
            }
            .title {
                font-size: 2rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def detect_db_path() -> str:
    env_path = os.getenv("DATABASE_PATH") or os.getenv("DB_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    candidates = [
        Path("scriptspy.db"),
        Path("database.db"),
        Path("data/scriptspy.db"),
        Path("data/database.db"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    discovered = sorted(Path(".").glob("*.db")) + sorted(Path("data").glob("*.db"))
    if discovered:
        return str(discovered[0])

    return "scriptspy.db"


@st.cache_resource(show_spinner=False)
def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [row[0] for row in rows]


def get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [row[1] for row in rows]


def pick_table(tables: list[str], candidates: list[str]) -> str | None:
    lowered = {name.lower(): name for name in tables}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    for table in tables:
        if any(token in table.lower() for token in candidates):
            return table
    return None


def source_emoji(source: str) -> str:
    s = (source or "").lower()
    if "google" in s:
        return "📈"
    if "news" in s:
        return "📰"
    if "reddit" in s:
        return "💬"
    return "🔎"


def first_present(columns: list[str], options: list[str], default: str | None = None) -> str | None:
    lower_map = {c.lower(): c for c in columns}
    for opt in options:
        if opt.lower() in lower_map:
            return lower_map[opt.lower()]
    return default


def fetch_trends(conn: sqlite3.Connection) -> pd.DataFrame:
    tables = list_tables(conn)
    trend_table = pick_table(tables, ["trends", "trend", "topic_trends"])
    if not trend_table:
        return pd.DataFrame(columns=["topic", "source", "description", "url", "created_at"])

    cols = get_columns(conn, trend_table)
    topic_col = first_present(cols, ["topic", "name", "title", "keyword"], "topic")
    source_col = first_present(cols, ["source", "platform", "origin"], "source")
    desc_col = first_present(cols, ["description", "summary", "details"], "description")
    url_col = first_present(cols, ["url", "link", "source_url"], "url")
    created_col = first_present(cols, ["created_at", "fetched_at", "timestamp", "published_at", "date"])

    select_parts = [
        f"{topic_col} AS topic" if topic_col in cols else "'' AS topic",
        f"{source_col} AS source" if source_col in cols else "'' AS source",
        f"{desc_col} AS description" if desc_col in cols else "'' AS description",
        f"{url_col} AS url" if url_col in cols else "'' AS url",
        f"{created_col} AS created_at" if created_col else "NULL AS created_at",
    ]
    order = f"ORDER BY {created_col} DESC" if created_col else ""
    query = f"SELECT {', '.join(select_parts)} FROM {trend_table} {order}"
    return pd.read_sql_query(query, conn)


def fetch_competitors(conn: sqlite3.Connection) -> tuple[pd.DataFrame, str | None, str | None]:
    tables = list_tables(conn)
    comp_table = pick_table(tables, ["competitors", "competitor", "accounts"])
    posts_table = pick_table(tables, ["posts", "post", "competitor_posts", "content"])

    if not comp_table:
        return pd.DataFrame(columns=["id", "name", "handle", "post_count", "last_posted"]), None, None

    comp_cols = get_columns(conn, comp_table)
    comp_id = first_present(comp_cols, ["id", "competitor_id", "account_id"], "id")
    name_col = first_present(comp_cols, ["name", "competitor_name", "display_name"], "name")
    handle_col = first_present(comp_cols, ["handle", "username", "account_handle"], "handle")

    if posts_table:
        post_cols = get_columns(conn, posts_table)
        post_fk = first_present(post_cols, ["competitor_id", "account_id", "owner_id", "profile_id"])
        post_date = first_present(post_cols, ["posted_at", "created_at", "published_at", "date"])

        if post_fk and post_date:
            query = f"""
                SELECT
                    c.{comp_id} AS id,
                    c.{name_col} AS name,
                    c.{handle_col} AS handle,
                    COUNT(p.{post_fk}) AS post_count,
                    MAX(p.{post_date}) AS last_posted
                FROM {comp_table} c
                LEFT JOIN {posts_table} p
                    ON p.{post_fk} = c.{comp_id}
                GROUP BY c.{comp_id}, c.{name_col}, c.{handle_col}
                ORDER BY last_posted DESC
            """
            return pd.read_sql_query(query, conn), comp_table, posts_table

    query = f"SELECT {comp_id} AS id, {name_col} AS name, {handle_col} AS handle FROM {comp_table}"
    df = pd.read_sql_query(query, conn)
    df["post_count"] = 0
    df["last_posted"] = None
    return df, comp_table, posts_table


def add_competitor(conn: sqlite3.Connection, comp_table: str, name: str, handle: str) -> str:
    cols = get_columns(conn, comp_table)
    name_col = first_present(cols, ["name", "competitor_name", "display_name"])
    handle_col = first_present(cols, ["handle", "username", "account_handle"])
    created_col = first_present(cols, ["created_at", "added_at", "timestamp"])
    if not (name_col and handle_col):
        return "Could not add competitor: required columns are missing."

    values_cols = [name_col, handle_col]
    values = [name.strip(), handle.strip()]

    if created_col:
        values_cols.append(created_col)
        values.append(datetime.utcnow().isoformat(timespec="seconds"))

    placeholders = ", ".join(["?"] * len(values_cols))
    query = f"INSERT INTO {comp_table} ({', '.join(values_cols)}) VALUES ({placeholders})"
    conn.execute(query, values)
    conn.commit()
    return "Competitor added."


def fetch_competitor_posts(conn: sqlite3.Connection, posts_table: str, competitor_id: Any) -> pd.DataFrame:
    cols = get_columns(conn, posts_table)
    fk_col = first_present(cols, ["competitor_id", "account_id", "owner_id", "profile_id"])
    caption_col = first_present(cols, ["caption", "text", "content", "description"], "caption")
    type_col = first_present(cols, ["post_type", "type", "content_type"], "post_type")
    date_col = first_present(cols, ["posted_at", "created_at", "published_at", "date"], "posted_at")
    url_col = first_present(cols, ["url", "link", "post_url", "source_url"], "url")

    if not fk_col:
        return pd.DataFrame(columns=["caption", "post_type", "posted_at", "url"])

    query = f"""
        SELECT
            {caption_col} AS caption,
            {type_col} AS post_type,
            {date_col} AS posted_at,
            {url_col} AS url
        FROM {posts_table}
        WHERE {fk_col} = ?
        ORDER BY {date_col} DESC
        LIMIT 25
    """
    return pd.read_sql_query(query, conn, params=[competitor_id])


def fetch_activity_log(conn: sqlite3.Connection) -> pd.DataFrame:
    tables = list_tables(conn)
    log_table = pick_table(tables, ["activity_log", "events", "event_log", "logs"])
    if log_table:
        cols = get_columns(conn, log_table)
        ts_col = first_present(cols, ["timestamp", "created_at", "time", "event_time"])
        msg_col = first_present(cols, ["description", "message", "event", "details"])
        if ts_col and msg_col:
            q = f"SELECT {ts_col} AS timestamp, {msg_col} AS description FROM {log_table} ORDER BY {ts_col} DESC LIMIT 100"
            return pd.read_sql_query(q, conn)

    entries: list[dict[str, str]] = []
    posts_table = pick_table(tables, ["posts", "post", "competitor_posts", "content"])
    comp_table = pick_table(tables, ["competitors", "competitor", "accounts"])

    if posts_table and comp_table:
        pcols = get_columns(conn, posts_table)
        ccols = get_columns(conn, comp_table)
        fk_col = first_present(pcols, ["competitor_id", "account_id", "owner_id", "profile_id"])
        date_col = first_present(pcols, ["posted_at", "created_at", "published_at", "date"])
        cname_col = first_present(ccols, ["name", "competitor_name", "display_name"])
        cid_col = first_present(ccols, ["id", "competitor_id", "account_id"])
        if fk_col and date_col and cname_col and cid_col:
            q = f"""
                SELECT p.{date_col} AS timestamp, c.{cname_col} AS competitor
                FROM {posts_table} p
                JOIN {comp_table} c ON c.{cid_col} = p.{fk_col}
                ORDER BY p.{date_col} DESC
                LIMIT 40
            """
            for row in conn.execute(q).fetchall():
                entries.append(
                    {
                        "timestamp": row["timestamp"],
                        "description": f"New post detected for {row['competitor']}",
                    }
                )

    trends = fetch_trends(conn)
    if not trends.empty and "created_at" in trends.columns:
        grouped = trends.dropna(subset=["created_at"]).groupby("created_at").size().reset_index(name="count")
        for _, row in grouped.head(20).iterrows():
            entries.append(
                {
                    "timestamp": row["created_at"],
                    "description": f"Fetched {int(row['count'])} new trends",
                }
            )

    if not entries:
        return pd.DataFrame(columns=["timestamp", "description"])

    df = pd.DataFrame(entries)
    return df.sort_values("timestamp", ascending=False)


def render_trending_now(conn: sqlite3.Connection) -> None:
    st.subheader("Trending Now")
    trends = fetch_trends(conn)

    if trends.empty:
        st.info("No trend data found in the database yet.")
        return

    sources = sorted([s for s in trends["source"].dropna().unique() if str(s).strip()])
    selected_source = st.selectbox("Filter by source", ["All"] + list(sources))
    if selected_source != "All":
        trends = trends[trends["source"] == selected_source]

    for _, trend in trends.iterrows():
        emoji = source_emoji(str(trend.get("source", "")))
        topic = trend.get("topic", "(untitled)")
        source = trend.get("source", "Unknown")
        desc = trend.get("description", "No description available.")
        url = trend.get("url", "")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"### {topic}")
        st.markdown(f"**{emoji} {source}**")
        st.markdown(f"<div class='muted'>{desc}</div>", unsafe_allow_html=True)
        if pd.notna(url) and str(url).strip():
            st.markdown(f"[Open source link]({url})")
        st.markdown("</div>", unsafe_allow_html=True)


def render_competitors(conn: sqlite3.Connection) -> None:
    st.subheader("Competitors")
    competitors, comp_table, posts_table = fetch_competitors(conn)

    with st.expander("Add new competitor", expanded=False):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            name = st.text_input("Name", key="new_comp_name")
        with col2:
            handle = st.text_input("@handle", key="new_comp_handle")
        with col3:
            if st.button("Add", use_container_width=True):
                if not comp_table:
                    st.error("No competitors table found in the database.")
                elif not name.strip() or not handle.strip():
                    st.warning("Enter both a name and handle.")
                else:
                    st.success(add_competitor(conn, comp_table, name, handle))
                    st.rerun()

    if competitors.empty:
        st.info("No competitors tracked yet.")
        return

    for _, comp in competitors.iterrows():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"### {comp['name']}")
        st.markdown(f"**@{str(comp['handle']).lstrip('@')}**")
        st.markdown(f"Posts tracked: **{int(comp.get('post_count', 0) or 0)}**")
        st.markdown(f"Last posted: **{comp.get('last_posted') or 'N/A'}**")
        st.markdown("</div>", unsafe_allow_html=True)

    if posts_table:
        options = {
            f"{row['name']} (@{str(row['handle']).lstrip('@')})": row["id"]
            for _, row in competitors.iterrows()
        }
        selected = st.selectbox("View recent posts for", list(options.keys()))
        posts = fetch_competitor_posts(conn, posts_table, options[selected])

        st.markdown("#### Recent posts")
        if posts.empty:
            st.write("No posts found for this competitor.")
        else:
            for _, post in posts.iterrows():
                preview = str(post.get("caption", "")).strip()[:140] or "(No caption)"
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"**{preview}**")
                st.markdown(f"Type: `{post.get('post_type', 'unknown')}`")
                st.markdown(f"Posted: `{post.get('posted_at', 'N/A')}`")
                url = post.get("url", "")
                if pd.notna(url) and str(url).strip():
                    st.markdown(f"[Open original post]({url})")
                st.markdown("</div>", unsafe_allow_html=True)


def render_activity_log(conn: sqlite3.Connection) -> None:
    st.subheader("Activity Log")
    activity = fetch_activity_log(conn)

    if activity.empty:
        st.info("No recent activity found.")
        return

    for _, event in activity.head(100).iterrows():
        ts = event.get("timestamp", "Unknown time")
        desc = event.get("description", "")
        st.markdown(
            f"<div class='timeline-item'><div><strong>{ts}</strong></div><div>{desc}</div></div>",
            unsafe_allow_html=True,
        )


def main() -> None:
    apply_dark_theme()
    st.markdown("<div class='title'>ScriptSpy 🔍</div>", unsafe_allow_html=True)

    db_path = detect_db_path()
    st.sidebar.caption(f"DB: `{db_path}`")

    try:
        conn = get_connection(db_path)
    except sqlite3.Error as err:
        st.error(f"Could not connect to database: {err}")
        return

    page = st.sidebar.radio("Navigate", ["Trending Now", "Competitors", "Activity Log"])

    if page == "Trending Now":
        render_trending_now(conn)
    elif page == "Competitors":
        render_competitors(conn)
    else:
        render_activity_log(conn)


if __name__ == "__main__":
    main()
