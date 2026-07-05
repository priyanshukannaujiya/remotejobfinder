import streamlit as st
import pandas as pd
import sqlite3
import os
import sys
import json
import re
import plotly.express as px

# Add root directory to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from job_hunter.email.sender import EmailSender

# Setup page
st.set_page_config(page_title="Data Engineering Job Hunter", layout="wide")

# Custom CSS for modern, premium dark UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

    /* Global Typography & Background */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif !important;
    }
    
    .stApp {
        background: radial-gradient(circle at top left, #1a1a2e, #16213e, #0f3460) !important;
        color: #e2e8f0 !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* Header text */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-weight: 600 !important;
    }
    
    h1 {
        background: -webkit-linear-gradient(45deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding-bottom: 10px;
    }

    /* Glassmorphic Metrics Cards */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease !important;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2) !important;
        border-color: rgba(79, 172, 254, 0.3) !important;
    }

    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
    }

    [data-testid="stMetricValue"] {
        color: #f8fafc !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
    }

    /* Input fields and buttons */
    .stTextInput>div>div>input {
        background-color: rgba(15, 23, 42, 0.8) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #4facfe !important;
        box-shadow: 0 0 0 1px #4facfe !important;
    }

    .stButton>button {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
    }

    .stButton>button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 0 15px rgba(79, 172, 254, 0.5) !important;
    }

    /* Expander/Dataframes */
    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Data Engineering Job Hunter")

data_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"
)
db_path = os.path.join(data_dir, "jobs.db")


@st.cache_data(ttl=60)
def load_data():
    if not os.path.exists(db_path):
        return pd.DataFrame()
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM jobs", conn)
    conn.close()

    if not df.empty and "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


df = load_data()

if df.empty:
    st.warning("No data found! Run the scraper first.")
    st.stop()

# KPIs
total_jobs = len(df)
jobs_today = len(df[df["timestamp"].dt.date == pd.Timestamp.today().date()])
jobs_week = len(df[df["timestamp"] >= pd.Timestamp.today() - pd.Timedelta(days=7)])
remote_pct = (df["remote"].sum() / total_jobs * 100) if total_jobs > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Jobs", total_jobs)
col2.metric("Jobs Today", jobs_today)
col3.metric("Jobs This Week", jobs_week)
col4.metric("Remote %", f"{remote_pct:.1f}%")

st.markdown("---")

# Filters
st.sidebar.header("Filters")
search_term = st.sidebar.text_input("Search (Title/Company/Skills)")
min_score = st.sidebar.slider("Min Resume Match Score", 0, 100, 0)
show_remote_only = st.sidebar.checkbox("Remote Only")
show_interns_only = st.sidebar.checkbox("Internships Only")

filtered_df = df.copy()

if search_term:
    search_term = search_term.lower()
    filtered_df = filtered_df[
        filtered_df["title"].str.lower().str.contains(search_term, na=False)
        | filtered_df["company"].str.lower().str.contains(search_term, na=False)
        | filtered_df["skills"].str.lower().str.contains(search_term, na=False)
    ]

if min_score > 0:
    filtered_df = filtered_df[filtered_df["resume_match_score"] >= min_score]

if show_remote_only:
    filtered_df = filtered_df[filtered_df["remote"]]

if show_interns_only:
    filtered_df = filtered_df[filtered_df["internship"]]

if "source" in df.columns:
    sources = sorted(df["source"].dropna().unique().tolist())
    selected_sources = st.sidebar.multiselect(
        "Filter by Source", options=sources, default=sources
    )
    if selected_sources:
        filtered_df = filtered_df[filtered_df["source"].isin(selected_sources)]

# Visualizations
col_v1, col_v2 = st.columns(2)

with col_v1:
    st.subheader("Top Companies Hiring")
    if not filtered_df.empty:
        top_companies = filtered_df["company"].value_counts().head(10).reset_index()
        top_companies.columns = ["Company", "Count"]
        fig = px.bar(top_companies, x="Count", y="Company", orientation="h", color_discrete_sequence=['#4facfe'])
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0')
        )
        st.plotly_chart(fig, use_container_width=True)

with col_v2:
    st.subheader("Resume Match Score Distribution")
    if not filtered_df.empty and "resume_match_score" in filtered_df.columns:
        fig2 = px.histogram(filtered_df, x="resume_match_score", nbins=20, color_discrete_sequence=['#00f2fe'])
        fig2.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0')
        )
        st.plotly_chart(fig2, use_container_width=True)

# Job Table
st.subheader("Job Listings")
display_cols = [
    "company",
    "title",
    "location",
    "experience_required",
    "resume_match_score",
    "skills",
    "salary",
    "remote",
    "internship",
    "source",
    "apply_link",
    "summary",
    "match_explanation",
    "missing_skills",
    "resume_improvements",
    "resume_summary",
    "cover_letter",
    "interview_questions",
    "recommended_projects",
]
# Ensure columns exist before displaying
display_cols = [c for c in display_cols if c in filtered_df.columns]

st.dataframe(
    filtered_df[display_cols].sort_values(
        by="resume_match_score", ascending=False, na_position="last"
    ),
    use_container_width=True,
    column_config={
        "apply_link": st.column_config.LinkColumn("Apply Link"),
        "resume_match_score": st.column_config.ProgressColumn(
            "Match Score",
            help="AI generated match score based on resume",
            format="%f",
            min_value=0,
            max_value=100,
        ),
        "remote": st.column_config.CheckboxColumn("Remote"),
        "internship": st.column_config.CheckboxColumn("Internship"),
    },
    hide_index=True,
)

# Subscribe to Alerts
st.sidebar.markdown("---")
st.sidebar.subheader("Subscribe to Daily Alerts")

with st.sidebar.form(key="subscribe_form"):
    email_input = st.text_input("Enter your email address")
    submit_button = st.form_submit_button(label="Subscribe")

    if submit_button:
        if not email_input:
            st.error("Please enter an email address.")
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email_input):
            st.error("Please enter a valid email address.")
        else:
            subscribers_file = os.path.join(data_dir, "subscribers.json")
            subscribers = []
            if os.path.exists(subscribers_file):
                try:
                    with open(subscribers_file, "r") as f:
                        subscribers = json.load(f)
                except Exception:
                    pass

            if email_input in subscribers:
                st.warning("You are already subscribed!")
            else:
                subscribers.append(email_input)
                try:
                    with open(subscribers_file, "w") as f:
                        json.dump(subscribers, f, indent=4)
                    
                    # Send welcome email
                    try:
                        sender = EmailSender()
                        sender.send_welcome_email(email_input)
                    except Exception as e:
                        st.error("Could not send welcome email, but you are subscribed!")
                        
                    st.success("Successfully subscribed! Check your inbox for a welcome email.")
                except Exception as e:
                    st.error("Failed to save subscription. Please try again.")

# Downloads
st.sidebar.markdown("---")
st.sidebar.subheader("Downloads")

csv_path = os.path.join(data_dir, "jobs.csv")
if os.path.exists(csv_path):
    with open(csv_path, "rb") as f:
        st.sidebar.download_button("Download CSV", f, file_name="jobs.csv")

json_path = os.path.join(data_dir, "jobs.json")
if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        st.sidebar.download_button(
            "Download JSON", f.read(), file_name="jobs.json", mime="application/json"
        )
