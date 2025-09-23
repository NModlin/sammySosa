# DEPRECATED: Phase 2 dashboard is consolidated into govcon_suite.py
# Kept for reference only. Prefer running the unified app via Apollo_GovCon.py

import streamlit as st
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
import json

# --- CONFIGURATION ---
# This connection string MUST match the one in your scraper script (v4).
DB_CONNECTION_STRING = "postgresql://postgres:mysecretpassword@localhost:5434/sam_contracts"

# --- DATABASE FUNCTIONS ---

@st.cache_data(ttl=600) # Cache the data for 10 minutes to avoid constant DB queries
def load_data():
    """
    Connects to the PostgreSQL database and loads the opportunities into a Pandas DataFrame.
    """
    try:
        engine = create_engine(DB_CONNECTION_STRING)
        query = "SELECT * FROM opportunities ORDER BY posted_date DESC;"
        df = pd.read_sql(query, engine)
        
        # The 'raw_data' column is stored as a JSON string. We'll parse it back into a Python dict.
        # We use a lambda with a try-except block to handle potential parsing errors gracefully.
        df['raw_data'] = df['raw_data'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
        
        return df
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        return pd.DataFrame() # Return an empty DataFrame on error

# --- MAIN DASHBOARD UI ---

# Set the page configuration for a wide layout
st.set_page_config(layout="wide")

st.title("SAM.gov Contract Opportunities Dashboard (LEGACY)")
st.write("This dashboard is deprecated. Please use the unified GovCon Suite.")

# Load the data from the database
df = load_data()

if df.empty:
    st.warning("No data found. Please run the unified app to populate the database.")
else:
    # --- SIDEBAR FOR FILTERS ---
    st.sidebar.header("Filter Opportunities")

    # Filter by Agency
    agencies = sorted(df['agency'].dropna().unique())
    selected_agencies = st.sidebar.multiselect("Filter by Agency", agencies)

    # Filter by Set-Aside Type
    set_asides = sorted(df['set_aside'].dropna().unique())
    selected_set_asides = st.sidebar.multiselect("Filter by Set-Aside Type", set_asides)

    # Free text search for Title
    search_title = st.sidebar.text_input("Search by Title")

    # --- APPLY FILTERS ---
    filtered_df = df.copy()

    if selected_agencies:
        filtered_df = filtered_df[filtered_df['agency'].isin(selected_agencies)]
    
    if selected_set_asides:
        filtered_df = filtered_df[filtered_df['set_aside'].isin(selected_set_asides)]

    if search_title:
        filtered_df = filtered_df[filtered_df['title'].str.contains(search_title, case=False, na=False)]

    # --- DISPLAY METRICS AND DATA ---
    
    col1, col2 = st.columns(2)
    col1.metric("Total Opportunities in DB", len(df))
    col2.metric("Matching Opportunities", len(filtered_df))

    st.dataframe(filtered_df[['posted_date', 'title', 'agency', 'naics_code', 'set_aside', 'response_deadline']])

    st.header("View Full Opportunity Details")
    
    # Create a list of titles for the selectbox, handling potential duplicates
    opportunity_options = [f"{row.title} ({row.notice_id[-6:]})" for index, row in filtered_df.iterrows()]
    selected_opportunity_display = st.selectbox("Select an opportunity to see its raw data:", opportunity_options)

    if selected_opportunity_display:
        # Find the notice_id from the selected display string
        selected_notice_id_suffix = selected_opportunity_display.split('(')[-1][:-1]
        
        # Find the full row in the filtered dataframe
        selected_row = filtered_df[filtered_df['notice_id'].str.endswith(selected_notice_id_suffix)].iloc[0]

        st.json(selected_row['raw_data'])

