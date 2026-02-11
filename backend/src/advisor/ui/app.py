"""Streamlit UI for AI Development Advisor.

Frontend interface for repository analysis with download support.
"""

import httpx
import streamlit as st
from datetime import datetime

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"


def init_session_state():
    """Initialize session state variables."""
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "is_analyzing" not in st.session_state:
        st.session_state.is_analyzing = False
    if "error_message" not in st.session_state:
        st.session_state.error_message = None


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="AI Development Advisor",
        page_icon="🧠",
        layout="wide",
    )

    init_session_state()

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; }
    .download-btn { margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.title("🧠 AI Development Advisor")
    st.markdown(
        "Transform codebases into actionable intelligence for "
        "engineers and business leaders."
    )

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        st.markdown("---")
        st.markdown("**API Status**")

        # Check API health
        try:
            # Debug connection info
            st.caption(f"Connecting to: `{API_BASE_URL}`")
            
            with httpx.Client(timeout=30.0) as client:
                response = client.get(f"{API_BASE_URL}/health")
                if response.status_code == 200:
                    st.success("✅ API Connected")
                else:
                    st.error(f"❌ API Error: {response.status_code}")
        except httpx.TimeoutException:
            st.error("❌ API Timed Out")
            st.caption("Server is taking too long to respond.")
        except httpx.ConnectError:
            st.error("❌ Connection Refused")
            st.caption("Server is not running or unreachable.")
        except Exception as e:
            st.error("❌ API Unavailable")
            st.caption(f"Error: {str(e)}")
            st.caption("Start API: `uv run uvicorn advisor.api.endpoints:app`")

    # Main content
    col1, col2 = st.columns([2, 3])

    with col1:
        st.header("📥 Repository Input")

        repo_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/owner/repo",
            help="Enter a public or private GitHub repository URL",
        )

        with st.expander("🔐 Private Repository Access"):
            access_token = st.text_input(
                "GitHub Access Token (optional)",
                type="password",
                help="For private repositories. Never stored.",
            )
            st.caption("Token is used only for this request and never persisted.")

        if st.button(
            "🚀 Analyze Repository",
            disabled=st.session_state.is_analyzing or not repo_url,
            type="primary",
            use_container_width=True,
        ):
            run_analysis(repo_url, access_token if access_token else None)

    with col2:
        if st.session_state.error_message:
            st.error(st.session_state.error_message)

        if st.session_state.analysis_result:
            display_results(st.session_state.analysis_result)

    # Recent analyses (with graceful error handling)
    st.markdown("---")
    st.header("📊 Recent Analyses")
    display_recent_analyses()


def run_analysis(repo_url: str, access_token: str | None):
    """Run repository analysis via API."""
    st.session_state.is_analyzing = True
    st.session_state.error_message = None

    with st.spinner("🔍 Analyzing repository... This may take 5-10 minutes with free models."):
        try:
            # Debug connection info
            st.caption(f"Posting to: `{API_BASE_URL}/analyze`")
            
            # Increased timeout for deep analysis with free LLMs
            with httpx.Client(timeout=1200.0) as client:
                response = client.post(
                    f"{API_BASE_URL}/analyze",
                    json={
                        "repo_url": repo_url,
                        "access_token": access_token,
                    },
                )

                if response.status_code == 202:
                    st.session_state.analysis_result = response.json()
                    st.session_state.analysis_result["repo_url"] = repo_url
                    st.success("✅ Analysis complete!")
                else:
                    error = response.json().get("detail", "Unknown error")
                    st.session_state.error_message = f"Analysis failed: {error}"

        except httpx.TimeoutException:
            st.session_state.error_message = "Analysis timed out (20m limit). The server is busy or models are slow."
        except Exception as e:
            st.session_state.error_message = f"Error: {str(e)}"

    st.session_state.is_analyzing = False
    st.rerun()


def display_results(result: dict):
    """Display analysis results with download options."""
    st.header("📈 Analysis Results")

    # Success indicator
    if result.get("success"):
        st.success(result.get("message", "Analysis completed"))
    else:
        st.warning("Analysis completed with warnings")

    # Tab view for different audiences
    # Tab view for different audiences + timeline + trends
    tab1, tab2, tab3, tab4 = st.tabs([
        "👨‍💻 Technical View", "👔 Executive View",
        "⏱️ Analysis Timeline", "🔮 Trend Intelligence",
    ])

    with tab1:
        st.subheader("Technical Summary")
        technical_summary = result.get("technical_summary", "No summary available")
        st.markdown(technical_summary)
        
        st.download_button(
            label="📥 Download Technical Report",
            data=generate_markdown_report(result, "technical"),
            file_name=f"technical_report_{get_timestamp()}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with tab2:
        st.subheader("Executive Summary")
        executive_summary = result.get("executive_summary", "No summary available")
        st.markdown(executive_summary)
        
        st.download_button(
            label="📥 Download Executive Report",
            data=generate_markdown_report(result, "executive"),
            file_name=f"executive_report_{get_timestamp()}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with tab3:
        st.subheader("Analysis Pipeline Timeline")
        timeline = result.get("timeline")
        if timeline and isinstance(timeline, dict):
            total = timeline.get("total_duration_seconds")
            if total:
                st.metric("⏱️ Total Duration", f"{total:.1f}s")

            failed = timeline.get("failed_phases", [])
            if failed:
                st.error(f"❌ Failed phases: {', '.join(failed)}")

            phases = timeline.get("phases", {})
            if phases:
                for name, phase in phases.items():
                    status_icon = {
                        "completed": "✅",
                        "failed": "❌",
                        "running": "🔄",
                    }.get(phase.get("status", ""), "⏳")

                    dur = phase.get("duration_seconds")
                    dur_str = f"{dur:.2f}s" if dur else "—"
                    err = phase.get("error")

                    col_a, col_b, col_c = st.columns([3, 1, 1])
                    with col_a:
                        label = name.replace("_", " ").title()
                        st.markdown(f"{status_icon} **{label}**")
                    with col_b:
                        st.caption(dur_str)
                    with col_c:
                        st.caption(phase.get("status", "unknown"))

                    if err:
                        st.error(f"Error: {err}")
            else:
                st.info("No timeline data available.")
        else:
            st.info("Timeline tracking not available for this analysis.")

    with tab4:
        st.subheader("Technology Trend Intelligence")
        trend_data = result.get("trend_data")
        if trend_data and isinstance(trend_data, dict):
            tags = trend_data.get("tags_searched", [])
            if tags:
                st.markdown(f"**Technologies searched:** {', '.join(tags)}")

            context = trend_data.get("context", "")
            if context:
                st.markdown(context)
            else:
                st.info("Trend search ran but no insights were returned.")
        else:
            st.info(
                "Trend intelligence was not available. "
                "Ensure Serper API key is configured."
            )

    # Analysis metadata
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if result.get("analysis_id"):
            st.caption(f"📋 ID: {result['analysis_id']}")
    with col2:
        st.caption(f"🤖 Model: {result.get('model_used', 'Unknown')}")
    with col3:
        st.caption(f"📁 Repository: {result.get('repo_url', 'Unknown')}")
    with col4:
        timeline = result.get("timeline", {})
        total = timeline.get("total_duration_seconds") if timeline else None
        if total:
            st.caption(f"⏱️ Duration: {total:.1f}s")


def generate_markdown_report(result: dict, report_type: str) -> str:
    """Generate a downloadable markdown report."""
    repo_url = result.get("repo_url", "Unknown Repository")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if report_type == "technical":
        summary = result.get("technical_summary", "No summary available")
        title = "Technical Analysis Report"
    else:
        summary = result.get("executive_summary", "No summary available")
        title = "Executive Intelligence Brief"
    
    report = f"""# {title}

**Repository:** {repo_url}
**Generated:** {timestamp}
**Model:** {result.get('model_used', 'Unknown')}

---

{summary}

---

*Generated by AI Development Advisor*
"""
    return report


def get_timestamp() -> str:
    """Get formatted timestamp for filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def display_recent_analyses():
    """Display list of recent analyses with graceful error handling."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_BASE_URL}/analyses", params={"limit": 5})

            if response.status_code == 200:
                data = response.json()
                analyses = data.get("analyses", [])

                if not analyses:
                    st.info("No analyses yet. Submit a repository above!")
                    return

                for analysis in analyses:
                    with st.expander(
                        f"📁 {analysis.get('repo_name', 'Unknown')} - "
                        f"{analysis.get('analyzed_at', '')[:10]}"
                    ):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Tech Stack:**")
                            tech = analysis.get("tech_stack", {})
                            if tech.get("languages"):
                                st.write(", ".join(tech["languages"]))
                        with col2:
                            st.markdown("**Model Used:**")
                            st.write(analysis.get("model_used", "Unknown"))
            elif response.status_code == 500:
                # Database table might not exist yet
                st.info(
                    "Database not configured. "
                    "Run the migration script to enable history."
                )
            else:
                st.warning("Could not load recent analyses")

    except Exception:
        # Silently handle - recent analyses are not critical
        st.info("Analysis history will appear here after database setup.")


if __name__ == "__main__":
    main()
