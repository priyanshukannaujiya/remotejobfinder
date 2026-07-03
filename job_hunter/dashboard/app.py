import streamlit as st
import pandas as pd
import sqlite3
import os
import json
import plotly.express as px

# Setup page
st.set_page_config(page_title="Data Engineering Job Hunter", layout="wide")

st.title("🚀 Data Engineering Job Hunter Dashboard")

data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
db_path = os.path.join(data_dir, 'jobs.db')

@st.cache_data(ttl=60)
def load_data():
    if not os.path.exists(db_path):
        return pd.DataFrame()
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM jobs", conn)
    conn.close()
    
    if not df.empty and 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

df = load_data()

if df.empty:
    st.warning("No data found! Run the scraper first.")
    st.stop()

# KPIs
total_jobs = len(df)
jobs_today = len(df[df['timestamp'].dt.date == pd.Timestamp.today().date()])
jobs_week = len(df[df['timestamp'] >= pd.Timestamp.today() - pd.Timedelta(days=7)])
remote_pct = (df['remote'].sum() / total_jobs * 100) if total_jobs > 0 else 0

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
        filtered_df['title'].str.lower().str.contains(search_term, na=False) |
        filtered_df['company'].str.lower().str.contains(search_term, na=False) |
        filtered_df['skills'].str.lower().str.contains(search_term, na=False)
    ]

if min_score > 0:
    filtered_df = filtered_df[filtered_df['resume_match_score'] >= min_score]

if show_remote_only:
    filtered_df = filtered_df[filtered_df['remote'] == True]

if show_interns_only:
    filtered_df = filtered_df[filtered_df['internship'] == True]

if 'source' in df.columns:
    sources = sorted(df['source'].dropna().unique().tolist())
    selected_sources = st.sidebar.multiselect("Filter by Source", options=sources, default=sources)
    if selected_sources:
        filtered_df = filtered_df[filtered_df['source'].isin(selected_sources)]

# Visualizations
col_v1, col_v2 = st.columns(2)

with col_v1:
    st.subheader("Top Companies Hiring")
    if not filtered_df.empty:
        top_companies = filtered_df['company'].value_counts().head(10).reset_index()
        top_companies.columns = ['Company', 'Count']
        fig = px.bar(top_companies, x='Count', y='Company', orientation='h')
        st.plotly_chart(fig, use_container_width=True)

with col_v2:
    st.subheader("Resume Match Score Distribution")
    if not filtered_df.empty and 'resume_match_score' in filtered_df.columns:
        fig2 = px.histogram(filtered_df, x="resume_match_score", nbins=20)
        st.plotly_chart(fig2, use_container_width=True)

# Job Table
st.subheader("Job Listings")
display_cols = [
    'company', 'title', 'location', 'experience_required', 'resume_match_score', 
    'skills', 'salary', 'remote', 'internship', 'source', 'apply_link', 
    'llm_reasoning', 'full_job_description'
]
# Ensure columns exist before displaying
display_cols = [c for c in display_cols if c in filtered_df.columns]
st.dataframe(filtered_df[display_cols].sort_values(by='resume_match_score', ascending=False, na_position='last'))

# Downloads
st.sidebar.markdown("---")
st.sidebar.subheader("Downloads")

csv_path = os.path.join(data_dir, 'jobs.csv')
if os.path.exists(csv_path):
    with open(csv_path, 'rb') as f:
        st.sidebar.download_button("Download CSV", f, file_name="jobs.csv")

json_path = os.path.join(data_dir, 'jobs.json')
if os.path.exists(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        st.sidebar.download_button("Download JSON", f.read(), file_name="jobs.json", mime="application/json")
