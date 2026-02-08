"""Streamlit Test UI for Trend Master.

Run with: streamlit run src/advisor/trends/test_trends.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from advisor.trends.trend_master import TrendMaster

st.set_page_config(
    page_title="Trend Master Test",
    page_icon="📈",
    layout="wide",
)


def run_async(coro):
    """Run async function in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def main():
    """Main Streamlit app."""
    st.title("📈 Trend Master Test UI")
    st.markdown("Test the tech stack trend analysis system.")

    # Initialize TrendMaster
    if "trend_master" not in st.session_state:
        st.session_state.trend_master = TrendMaster()

    tm = st.session_state.trend_master

    # Sidebar options
    with st.sidebar:
        st.header("Options")
        force_refresh = st.checkbox(
            "Force refresh",
            help="Bypass cache and collect fresh data",
        )

    # Main input
    col1, col2 = st.columns([3, 1])
    with col1:
        tag = st.text_input(
            "Enter technology tag",
            placeholder="e.g., langchain, react, kubernetes",
        )
    with col2:
        analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)

    # Analysis
    if analyze_btn and tag:
        with st.spinner(f"Analyzing trends for '{tag}'..."):
            try:
                insight = run_async(tm.analyze_tag(tag, force_refresh=force_refresh))
                display_insight(insight)
            except Exception as e:
                st.error(f"Analysis failed: {e}")

    # Query history section
    st.divider()
    st.subheader("📚 Query Historical Data")

    col1, col2 = st.columns([3, 1])
    with col1:
        query_tag = st.text_input(
            "Query tag",
            placeholder="Enter tag to query history",
            key="query_tag",
        )
    with col2:
        query_btn = st.button("📖 Query", use_container_width=True)

    if query_btn and query_tag:
        with st.spinner(f"Querying history for '{query_tag}'..."):
            try:
                insights = run_async(tm.query_trends(query_tag))
                if insights:
                    st.success(f"Found {len(insights)} historical records")
                    for i, insight in enumerate(insights):
                        with st.expander(f"Record {i + 1} - {insight.collected_at}"):
                            display_insight(insight)
                else:
                    st.warning(f"No historical data for '{query_tag}'")
            except Exception as e:
                st.error(f"Query failed: {e}")


def display_insight(insight):
    """Display a TrendInsight in the UI."""
    # Header with momentum indicator
    momentum_colors = {
        "rising": "🟢",
        "stable": "🟡",
        "declining": "🔴",
        "unknown": "⚪",
    }
    momentum_icon = momentum_colors.get(insight.momentum, "⚪")

    st.markdown(f"### {insight.tag.upper()} {momentum_icon} {insight.momentum.title()}")
    st.caption(f"Collected: {insight.collected_at} | Sources: {insight.sources_count}")

    # Direction
    if insight.direction:
        st.info(f"**Direction:** {insight.direction}")

    # Key points
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📌 Key Points")
        for point in insight.key_points:
            st.markdown(f"- {point}")

        if insight.risks:
            st.markdown("#### ⚠️ Risks")
            for risk in insight.risks:
                st.markdown(f"- {risk}")

    with col2:
        if insight.opportunities:
            st.markdown("#### 💡 Opportunities")
            for opp in insight.opportunities:
                st.markdown(f"- {opp}")

    # Sources section with links
    if insight.sources:
        st.divider()
        st.markdown("#### 🔗 Sources")

        source_icons = {"web": "🌐", "github": "⭐", "hn": "📰"}

        for src in insight.sources:
            icon = source_icons.get(src.source_type, "🔗")
            date_str = f" ({src.date})" if src.date else ""
            score_str = f" • {src.score}" if src.score else ""

            if src.url:
                st.markdown(f"- {icon} [{src.title}]({src.url}){date_str}{score_str}")
            else:
                st.markdown(f"- {icon} {src.title}{date_str}{score_str}")


if __name__ == "__main__":
    main()
