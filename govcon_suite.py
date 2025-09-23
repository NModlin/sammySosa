# GovCon Suite - Unified App (Scraper + Dashboard + AI Co‑pilot)
# Consolidates Phase 1 (scraper), Phase 2 (dashboard), Phase 3 (AI co-pilot)
# Prepped for future feature expansion with modular functions and env-driven config.

import os
import json
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st
try:
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception:
    BackgroundScheduler = None
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Index, text
from sqlalchemy.dialects.postgresql import JSONB, insert, ARRAY
from sqlalchemy.exc import IntegrityError

# Optional heavy imports are only used on the AI Co‑pilot page
from pathlib import Path
import re
try:
    import fitz  # PyMuPDF
    from docx import Document
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
    from ctransformers import AutoModelForCausalLM
    from duckduckgo_search import DDGS
except Exception:
    # Defer import errors until the AI Co-pilot page is actually used
    fitz = Document = SentenceTransformer = faiss = np = AutoModelForCausalLM = DDGS = None

# ------------------------
# Configuration
# ------------------------

def get_database_url():
    """
    Get database URL with fallback for different environments.
    """
    # Check for explicit database URL first
    if os.getenv("GOVCON_DB_URL"):
        return os.getenv("GOVCON_DB_URL")

    # Check for Streamlit Cloud secrets
    if hasattr(st, 'secrets') and 'database' in st.secrets:
        db_secrets = st.secrets['database']
        return f"postgresql://{db_secrets['username']}:{db_secrets['password']}@{db_secrets['host']}:{db_secrets['port']}/{db_secrets['database']}"

    # Check for individual environment variables
    if all(os.getenv(var) for var in ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']):
        return f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME')}"

    # Local Docker default
    return "postgresql://postgres:mysecretpassword@localhost:5434/sam_contracts"

DB_CONNECTION_STRING = get_database_url()
SAM_API_KEY = os.getenv("SAM_API_KEY", "") or (st.secrets.get("SAM_API_KEY", "") if hasattr(st, 'secrets') else "")
API_KEY_EXPIRATION_DATE = os.getenv("API_KEY_EXPIRATION_DATE", "2025-12-21")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "") or (st.secrets.get("SLACK_WEBHOOK_URL", "") if hasattr(st, 'secrets') else "")
MODEL_PATH = os.getenv("GOVCON_MODEL_PATH", "mistral-7b-instruct-v0.1.Q4_K_M.gguf")

SEARCH_PARAMS = {
    "limit": 100,
    # Expect callers to set date range; default to last 1 day if not set elsewhere
}

# Global singletons (guarded for Streamlit reruns)
def initialize_session_state():
    """Initialize all session state variables to prevent KeyError issues."""
    if "_govcon_engine" not in st.session_state:
        st.session_state._govcon_engine = None
    if "_govcon_scheduler_started" not in st.session_state:
        st.session_state._govcon_scheduler_started = False
    if "selected_opportunity" not in st.session_state:
        st.session_state.selected_opportunity = None
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None
    if "sow_analysis" not in st.session_state:
        st.session_state.sow_analysis = None
    if "doc_name" not in st.session_state:
        st.session_state.doc_name = ""

# Initialize session state
initialize_session_state()

# ------------------------
# Notifications
# ------------------------

def send_slack_notification(webhook_url: str, message: str):
    """Simple text notification to Slack."""
    if not webhook_url:
        return
    try:
        headers = {"Content-Type": "application/json"}
        requests.post(webhook_url, headers=headers, data=json.dumps({"text": message}), timeout=10)
    except Exception:
        pass

def send_opportunity_notification(opportunity_data, p_win_score):
    """
    Send a formatted Slack notification for high P-Win opportunities using Block Kit.
    """
    if not SLACK_WEBHOOK_URL or p_win_score < 75:
        return

    title = opportunity_data.get("title", "N/A")
    agency = opportunity_data.get("fullParentPathName", "N/A")
    deadline = opportunity_data.get("responseDeadLine", "N/A")
    notice_id = opportunity_data.get("noticeId", "N/A")
    naics = opportunity_data.get("naicsCode", "N/A")

    # Slack Block Kit format for rich notifications
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🎯 High P-Win Opportunity ({p_win_score}%)"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Title:*\n{title}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Agency:*\n{agency}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Deadline:*\n{deadline}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*NAICS:*\n{naics}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Notice ID:* {notice_id}\n*P-Win Score:* {p_win_score}%"
            }
        }
    ]

    try:
        headers = {"Content-Type": "application/json"}
        payload = {"blocks": blocks}
        requests.post(SLACK_WEBHOOK_URL, headers=headers, data=json.dumps(payload), timeout=10)
    except Exception:
        pass


def check_api_key_expiration():
    try:
        exp_date = datetime.strptime(API_KEY_EXPIRATION_DATE, "%Y-%m-%d")
        days = (exp_date - datetime.now()).days
        if 0 < days <= 14:
            send_slack_notification(
                SLACK_WEBHOOK_URL,
                f"ALERT: SAM.gov API key expires in {days} days (on {API_KEY_EXPIRATION_DATE}).",
            )
        elif days <= 0:
            send_slack_notification(
                SLACK_WEBHOOK_URL,
                f"CRITICAL: SAM.gov API key has expired (on {API_KEY_EXPIRATION_DATE}).",
            )
    except Exception:
        pass

# ------------------------
# Database
# ------------------------

def get_engine():
    if st.session_state._govcon_engine is None:
        try:
            engine = create_engine(DB_CONNECTION_STRING)
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            st.session_state._govcon_engine = engine
        except Exception as e:
            st.error(f"""
            **Database Connection Error**

            Unable to connect to the database. This could be due to:

            1. **Missing Database Configuration**: If running on Streamlit Cloud, you need to configure database secrets
            2. **Local Docker Not Running**: If running locally, make sure Docker containers are running
            3. **Network Issues**: Check your internet connection and database accessibility

            **Connection String**: `{DB_CONNECTION_STRING.split('@')[0]}@[REDACTED]`

            **Error Details**: {str(e)}

            **To Fix This:**
            - **For Streamlit Cloud**: Add database secrets in your app settings under the "Secrets" tab
            - **For Local Development**: Run `docker compose up -d` in your project directory

            **Demo Mode**: You can continue without database functionality for demonstration purposes.
            """)

            # Offer demo mode
            if st.button("Continue in Demo Mode (No Database)"):
                st.session_state._govcon_engine = "demo_mode"
                st.rerun()
            else:
                st.stop()
    return st.session_state._govcon_engine


def setup_database():
    engine = get_engine()

    # Handle demo mode
    if engine == "demo_mode":
        return engine

    metadata = MetaData()
    opportunities = Table(
        "opportunities",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("notice_id", String, unique=True, nullable=False),
        Column("title", String),
        Column("agency", String),
        Column("posted_date", String),
        Column("response_deadline", String),
        Column("naics_code", String),
        Column("set_aside", String),
        Column("status", String, default="New", nullable=False),
        Column("p_win_score", Integer, default=0),
        Column("analysis_summary", String),
        Column("raw_data", JSONB),
    )

    # Phase 3: Subcontractor Ecosystem Management
    subcontractors = Table(
        "subcontractors",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("company_name", String, nullable=False),
        Column("capabilities", ARRAY(String)),  # Array of NAICS codes or keywords
        Column("contact_email", String),
        Column("contact_phone", String),
        Column("website", String),
        Column("location", String),
        Column("trust_score", Integer, default=50),  # 0-100 scale
        Column("vetting_notes", String),
        Column("created_date", String),
        Column("last_contact", String),
    )

    quotes = Table(
        "quotes",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("opportunity_notice_id", String, nullable=False),
        Column("subcontractor_id", Integer, nullable=False),
        Column("quote_data", JSONB),  # Store submitted price, notes, etc.
        Column("submission_date", String),
        Column("status", String, default="Pending"),  # Pending, Submitted, Accepted, Rejected
    )
    # Helpful indexes for performance and future filtering
    Index("ix_opportunities_posted_date", opportunities.c.posted_date)
    Index("ix_opportunities_naics_code", opportunities.c.naics_code)
    Index("ix_opportunities_agency", opportunities.c.agency)
    Index("ix_opportunities_p_win_score", opportunities.c.p_win_score)
    # GIN index on JSONB for flexible querying in future features
    Index("ix_opportunities_raw_data", opportunities.c.raw_data, postgresql_using="gin")

    # Phase 3 indexes
    Index("ix_subcontractors_company_name", subcontractors.c.company_name)
    Index("ix_subcontractors_trust_score", subcontractors.c.trust_score)
    Index("ix_subcontractors_capabilities", subcontractors.c.capabilities, postgresql_using="gin")
    Index("ix_quotes_opportunity_notice_id", quotes.c.opportunity_notice_id)
    Index("ix_quotes_subcontractor_id", quotes.c.subcontractor_id)
    Index("ix_quotes_status", quotes.c.status)

    metadata.create_all(engine)
    return engine

# ------------------------
# P-Win Scoring (Phase 2)
# ------------------------

# Company's core NAICS codes (customize for your business)
CORE_NAICS_CODES = [
    "541511",  # Custom Computer Programming Services
    "541512",  # Computer Systems Design Services
    "541513",  # Computer Facilities Management Services
    "541519",  # Other Computer Related Services
    "541330",  # Engineering Services
    "541690",  # Other Scientific and Technical Consulting Services
]

# Keywords for P-Win scoring
POSITIVE_KEYWORDS = [
    "software development", "system integration", "cybersecurity", "cloud", "agile",
    "devops", "automation", "artificial intelligence", "machine learning", "data analytics",
    "web development", "mobile app", "database", "network", "infrastructure"
]

NEGATIVE_KEYWORDS = [
    "construction", "manufacturing", "medical", "pharmaceutical", "food service",
    "janitorial", "landscaping", "security guard", "transportation", "logistics"
]

def calculate_p_win(opportunity_data):
    """
    Calculate Probability of Win score (0-100) based on NAICS match and keywords.
    """
    score = 0

    # NAICS code matching (+50 for perfect match)
    naics = opportunity_data.get("naicsCode", "")
    if naics in CORE_NAICS_CODES:
        score += 50

    # Keyword analysis on title and description
    title = (opportunity_data.get("title", "") or "").lower()
    description = (opportunity_data.get("description", "") or "").lower()
    combined_text = f"{title} {description}"

    # Positive keywords (+10 each)
    for keyword in POSITIVE_KEYWORDS:
        if keyword.lower() in combined_text:
            score += 10

    # Negative keywords (-10 each)
    for keyword in NEGATIVE_KEYWORDS:
        if keyword.lower() in combined_text:
            score -= 10

    # Normalize to 0-100 range
    score = max(0, min(100, score))
    return score

def generate_analysis_summary(opportunity_data, p_win_score):
    """
    Generate a brief analysis summary for the opportunity.
    """
    naics = opportunity_data.get("naicsCode", "N/A")

    summary_parts = [f"P-Win: {p_win_score}%"]

    if naics in CORE_NAICS_CODES:
        summary_parts.append("NAICS Match")

    if p_win_score >= 75:
        summary_parts.append("HIGH PRIORITY")
    elif p_win_score >= 50:
        summary_parts.append("Medium Priority")
    else:
        summary_parts.append("Low Priority")

    return " | ".join(summary_parts)

# ------------------------
# Partner Discovery (Phase 3)
# ------------------------

def find_partners(keywords, location="", max_results=10):
    """
    Search public sources for companies matching keywords and location.
    Uses DuckDuckGo search to find potential subcontractors.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return []

    partners = []

    # Construct search queries
    if location:
        search_queries = [
            f"{keyword} companies in {location}" for keyword in keywords
        ]
    else:
        search_queries = [
            f"{keyword} contractors" for keyword in keywords
        ]

    try:
        with DDGS() as ddgs:
            for query in search_queries[:3]:  # Limit to 3 queries to avoid rate limits
                results = list(ddgs.text(query, max_results=max_results//len(search_queries[:3])))

                for result in results:
                    # Extract company info from search results
                    title = result.get('title', '')
                    body = result.get('body', '')
                    href = result.get('href', '')

                    # Simple heuristics to identify company names
                    company_name = title.split(' - ')[0].split(' | ')[0].strip()

                    # Skip if it looks like a generic result
                    if any(skip_word in company_name.lower() for skip_word in
                           ['wikipedia', 'linkedin', 'indeed', 'glassdoor', 'facebook']):
                        continue

                    partner_info = {
                        'company_name': company_name,
                        'website': href,
                        'description': body[:200] + '...' if len(body) > 200 else body,
                        'source_query': query,
                        'capabilities': keywords  # Inferred from search keywords
                    }

                    # Avoid duplicates
                    if not any(p['company_name'].lower() == company_name.lower() for p in partners):
                        partners.append(partner_info)

                        if len(partners) >= max_results:
                            break

                if len(partners) >= max_results:
                    break

    except Exception as e:
        st.error(f"Partner search error: {str(e)}")
        return []

    return partners[:max_results]

def add_subcontractor_to_db(company_name, capabilities, contact_email="", contact_phone="",
                           website="", location="", trust_score=50, vetting_notes=""):
    """
    Add a new subcontractor to the database.
    """
    try:
        engine = setup_database()
        metadata = MetaData()
        metadata.reflect(bind=engine)

        if 'subcontractors' not in metadata.tables:
            # Create tables if they don't exist
            metadata.create_all(engine)

        subcontractors_table = metadata.tables['subcontractors']

        with engine.connect() as conn:
            # Check if company already exists
            existing = conn.execute(
                subcontractors_table.select().where(
                    subcontractors_table.c.company_name == company_name
                )
            ).fetchone()

            if existing:
                return False, "Company already exists in database"

            # Insert new subcontractor
            conn.execute(
                subcontractors_table.insert().values(
                    company_name=company_name,
                    capabilities=capabilities if isinstance(capabilities, list) else [capabilities],
                    contact_email=contact_email,
                    contact_phone=contact_phone,
                    website=website,
                    location=location,
                    trust_score=trust_score,
                    vetting_notes=vetting_notes,
                    created_date=datetime.now().strftime("%Y-%m-%d"),
                    last_contact=""
                )
            )
            conn.commit()
            return True, "Subcontractor added successfully"

    except Exception as e:
        return False, f"Database error: {str(e)}"

def generate_rfq(sow_text, opportunity_title, deadline):
    """
    Generate an RFQ document using LLM based on SOW text.
    """
    try:
        # This would use the LLM if available
        # For now, return a template
        rfq_template = f"""
REQUEST FOR QUOTE

Project: {opportunity_title}
Response Deadline: {deadline}

PROJECT OVERVIEW:
We are seeking qualified subcontractors to provide services for the above-referenced project.

SCOPE OF WORK:
Based on the provided Statement of Work, the selected subcontractor will be responsible for delivering services that meet all specified requirements and performance standards.

KEY REQUIREMENTS:
- All work must comply with applicable regulations and standards
- Contractor must maintain appropriate security clearances if required
- Regular progress reporting and communication required
- Quality assurance and testing as specified

SUBMISSION REQUIREMENTS:
Please provide:
1. Technical approach and methodology
2. Project timeline and milestones
3. Team qualifications and experience
4. Total project cost breakdown
5. References from similar projects

EVALUATION CRITERIA:
Proposals will be evaluated based on technical merit, past performance, schedule, and cost.

Please submit your quote by {deadline}.
"""
        return rfq_template
    except Exception as e:
        return f"Error generating RFQ: {str(e)}"

def get_subcontractors_for_opportunity(capabilities_needed):
    """
    Get subcontractors from database that match the needed capabilities.
    """
    try:
        engine = setup_database()

        # Query subcontractors with matching capabilities
        query = """
        SELECT id, company_name, capabilities, contact_email, trust_score, location
        FROM subcontractors
        WHERE trust_score >= 30
        ORDER BY trust_score DESC
        """

        df = pd.read_sql(query, engine)

        if df.empty:
            return []

        # Filter by capabilities if specified
        if capabilities_needed:
            matching_contractors = []
            for _, row in df.iterrows():
                contractor_caps = row['capabilities'] if isinstance(row['capabilities'], list) else []
                # Check if any needed capability matches contractor capabilities
                if any(cap.lower() in ' '.join(contractor_caps).lower() for cap in capabilities_needed):
                    matching_contractors.append(row.to_dict())
            return matching_contractors

        return df.to_dict('records')

    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return []

# ------------------------
# Scraper (Phase 1)
# ------------------------

def fetch_opportunities(api_key: str, params: dict):
    base_url = "https://api.sam.gov/prod/opportunities/v2/search"
    q = dict(params)
    q["api_key"] = api_key
    try:
        r = requests.get(base_url, params=q, timeout=60)
        r.raise_for_status()
        data = r.json()
        return data.get("opportunitiesData", [])
    except Exception as e:
        st.warning(f"Fetch error: {e}")
        return []


def store_opportunities(engine, opportunities_data):
    if not opportunities_data:
        return 0
    inserted = 0
    metadata = MetaData()
    opps = Table("opportunities", metadata, autoload_with=engine)
    with engine.connect() as conn:
        try:
            conn.rollback()
        except Exception:
            pass
        for item in opportunities_data:
            try:
                # Calculate P-Win score and analysis summary
                p_win_score = calculate_p_win(item)
                analysis_summary = generate_analysis_summary(item, p_win_score)

                record = {
                    "notice_id": item.get("noticeId"),
                    "title": item.get("title"),
                    "agency": item.get("fullParentPathName"),
                    "posted_date": item.get("postedDate"),
                    "response_deadline": item.get("responseDeadLine"),
                    "naics_code": item.get("naicsCode"),
                    "set_aside": item.get("typeOfSetAside"),
                    "status": "New",
                    "p_win_score": p_win_score,
                    "analysis_summary": analysis_summary,
                    "raw_data": item,
                }

                # Send Slack notification for high P-Win opportunities
                send_opportunity_notification(item, p_win_score)
                upsert_stmt = insert(opps).values(**record)
                # Update all fields except 'status' to preserve workflow state on existing rows
                update_cols = {
                    "title": upsert_stmt.excluded.title,
                    "agency": upsert_stmt.excluded.agency,
                    "posted_date": upsert_stmt.excluded.posted_date,
                    "response_deadline": upsert_stmt.excluded.response_deadline,
                    "naics_code": upsert_stmt.excluded.naics_code,
                    "set_aside": upsert_stmt.excluded.set_aside,
                    "p_win_score": upsert_stmt.excluded.p_win_score,
                    "analysis_summary": upsert_stmt.excluded.analysis_summary,
                    "raw_data": upsert_stmt.excluded.raw_data,
                }
                do_update = upsert_stmt.on_conflict_do_update(
                    index_elements=["notice_id"],
                    set_=update_cols,
                )
                conn.execute(do_update)
                inserted += 1
            except IntegrityError:
                # duplicate notice_id
                pass
            except Exception:
                conn.rollback()
        conn.commit()
    return inserted


def run_scraper(date_from: str = None, date_to: str = None, naics: str = None):
    check_api_key_expiration()
    params = dict(SEARCH_PARAMS)
    if date_from and date_to:
        params.update({"postedFrom": date_from, "postedTo": date_to})
    else:
        # default: last 1 day window
        today = datetime.now(timezone.utc).date()
        ymd = today.strftime("%m/%d/%Y")
        params.update({"postedFrom": ymd, "postedTo": ymd})
    if naics:
        params["naics"] = naics

    engine = setup_database()
    data = fetch_opportunities(SAM_API_KEY, params)
    n = store_opportunities(engine, data)
    return n

# ------------------------
# Scheduler
# ------------------------

def ensure_scheduler():
    if st.session_state._govcon_scheduler_started:
        return
    try:
        if BackgroundScheduler is None:
            return
        scheduler = BackgroundScheduler()
        # Daily run at 3 AM UTC
        scheduler.add_job(run_scraper, "cron", hour=3, minute=0)
        scheduler.start()
        st.session_state._govcon_scheduler_started = True
    except Exception:
        pass

# ------------------------
# Dashboard (Phase 2)
# ------------------------

def page_dashboard():
    try:
        st.title("Opportunity Dashboard")

        # Check if we're in demo mode
        engine = setup_database()
        if engine == "demo_mode":
            st.warning("**Demo Mode**: Database functionality is disabled. This is a demonstration of the interface only.")
            st.info("To enable full functionality, configure database connection in secrets or run locally with Docker.")

            # Show demo data
            demo_data = {
                "notice_id": ["DEMO001", "DEMO002", "DEMO003"],
                "title": ["Custom Software Development Services", "Cybersecurity Assessment and Implementation", "Cloud Infrastructure Migration"],
                "agency": ["Department of Defense", "Department of Homeland Security", "General Services Administration"],
                "p_win_score": [85, 92, 78],
                "analysis_summary": ["High P-Win: NAICS match + positive keywords", "Excellent P-Win: Perfect capability alignment", "Good P-Win: Strong technical requirements match"],
                "posted_date": ["2025-09-20", "2025-09-21", "2025-09-22"],
                "response_deadline": ["2025-10-20", "2025-10-25", "2025-10-30"],
                "status": ["Active", "Active", "Active"]
            }

            df_demo = pd.DataFrame(demo_data)
            df_demo["Analyze"] = False

            st.subheader("Demo Opportunities")
            st.data_editor(
                df_demo[["Analyze", "notice_id", "title", "agency", "p_win_score", "analysis_summary", "posted_date", "response_deadline", "status"]],
                width="stretch",
                column_config={
                    "Analyze": st.column_config.CheckboxColumn("Select for Analysis"),
                    "p_win_score": st.column_config.NumberColumn("P-Win %", min_value=0, max_value=100),
                    "analysis_summary": st.column_config.TextColumn("Analysis", width="large"),
                },
                hide_index=True,
                disabled=["notice_id", "title", "agency", "p_win_score", "analysis_summary", "posted_date", "response_deadline", "status"]
            )
            return

        ensure_scheduler()

        c1, c2, c3 = st.columns(3)
        with c1:
            date_from = st.text_input("Posted From (MM/DD/YYYY)")
        with c2:
            date_to = st.text_input("Posted To (MM/DD/YYYY)")
        with c3:
            naics = st.text_input("NAICS (optional)")

        if st.button("Run Scraper Now"):
            with st.spinner("Fetching latest opportunities..."):
                inserted = run_scraper(date_from or None, date_to or None, naics or None)
            st.success(f"Scraper run complete. Inserted {inserted} new records.")

        engine = setup_database()
        df = pd.read_sql(
            "SELECT notice_id, title, agency, posted_date, response_deadline, naics_code, set_aside, status, p_win_score, analysis_summary, raw_data FROM opportunities ORDER BY p_win_score DESC, posted_date DESC",
            engine,
        )
        # Normalize raw_data to dict if it came back as JSON string
        if "raw_data" in df.columns:
            df["raw_data"] = df["raw_data"].apply(lambda x: json.loads(x) if isinstance(x, str) else x)

            if not df.empty:
                # Add Analyze checkbox column for opportunity selection
                df_display = df.copy()
                df_display.insert(0, "Analyze", False)

                # Create editable dataframe with checkbox column
                edited_df = st.data_editor(
                    df_display[["Analyze", "notice_id", "title", "agency", "p_win_score", "analysis_summary", "posted_date", "response_deadline", "status"]],
                    width="stretch",
                    column_config={
                        "Analyze": st.column_config.CheckboxColumn("Select for Analysis"),
                        "p_win_score": st.column_config.NumberColumn("P-Win %", min_value=0, max_value=100),
                        "analysis_summary": st.column_config.TextColumn("Analysis"),
                    },
                    hide_index=True,
                )

                # Check for selected opportunities
                selected_rows = edited_df[edited_df["Analyze"] == True]
                if not selected_rows.empty:
                    selected_notice_id = selected_rows.iloc[0]["notice_id"]
                    selected_opportunity = df[df["notice_id"] == selected_notice_id].iloc[0]

                    # Store selected opportunity in session state
                    st.session_state.selected_opportunity = selected_opportunity.to_dict()

                    st.info(f"✅ Selected opportunity: **{selected_opportunity['title']}** (P-Win: {selected_opportunity['p_win_score']}%)\n\nNavigate to the **AI Co-pilot** page to analyze this opportunity.")
            else:
                st.info("No opportunities found. Run the scraper to fetch data.")

            st.header("View Full Opportunity Details")
            if not df.empty:
                options = [f"{row.title} ({row.notice_id[-6:]})" for _, row in df.iterrows()]
                sel = st.selectbox("Select an opportunity:", options)
                if sel:
                    suffix = sel.split("(")[-1][:-1]
                    row = df[df["notice_id"].str.endswith(suffix)].iloc[0]
                    st.json(row["raw_data"])  # type: ignore
            else:
                st.info("No opportunities available to view details.")

    except Exception as e:
        st.error(f"""
        **Dashboard Error**

        An error occurred while loading the dashboard. This could be due to:

        1. **Database Connection Issues**: Check your database connection
        2. **Data Processing Error**: Issue with opportunity data
        3. **Session State Issues**: Try refreshing the page

        **Error Details**: {str(e)}

        **To Fix This:**
        - Try refreshing the page (F5)
        - Check database connection
        - Use Demo Mode if database is unavailable
        """)

        # Show debug information
        with st.expander("Debug Information"):
            st.write("**Error Type:**", type(e).__name__)
            st.write("**Error Message:**", str(e))
            import traceback
            st.code(traceback.format_exc())

# ------------------------
# AI Co‑pilot (Phase 3)
# ------------------------

def _require_ai_libs():
    if None in (fitz, Document, SentenceTransformer, faiss, np, AutoModelForCausalLM, DDGS):
        st.error("AI dependencies are not available. Please install the packages in requirements.txt.")
        st.stop()

@st.cache_data
def load_document_text(file_uploader):
    if file_uploader is None:
        return None, "Please upload a document."
    docs = {}
    try:
        file_name = file_uploader.name
        ext = Path(file_name).suffix.lower()
        if ext == ".pdf":
            with fitz.open(stream=file_uploader.read(), filetype="pdf") as doc:
                text = "".join(page.get_text() for page in doc)
                docs[file_name] = text
        elif ext == ".docx":
            doc = Document(file_uploader)
            text = "\n".join([para.text for para in doc.paragraphs])
            docs[file_name] = text
        else:
            return None, "Unsupported file type. Upload PDF or DOCX."
        if not docs:
            return None, "Could not read text from the document."
        return docs, None
    except Exception as e:
        return None, f"Error loading document: {e}"

@st.cache_resource
def create_vector_store(documents):
    if not documents:
        return None
    model = SentenceTransformer('all-MiniLM-L6-v2')
    chunks, refs = [], []
    for name, text in documents.items():
        words = re.split(r"\s+", text)
        for i in range(0, len(words), 200):
            chunk = " ".join(words[i:i+250])
            chunks.append(chunk)
            refs.append(name)
    embeds = model.encode(chunks, show_progress_bar=False)
    dim = embeds.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeds, dtype=np.float32))
    return index, chunks, refs, model

@st.cache_resource
def setup_llm():
    try:
        return AutoModelForCausalLM.from_pretrained(MODEL_PATH, model_type="mistral", gpu_layers=0)
    except Exception as e:
        st.error(f"Failed to load model at {MODEL_PATH}. Error: {e}")
        return None

def get_context(index, model, query, chunks):
    q_emb = model.encode([query])
    _, idxs = index.search(np.array(q_emb, dtype=np.float32), k=8)
    return "\n\n---\n\n".join([chunks[i] for i in idxs[0]])

def execute_ai_task(llm, prompt):
    return llm(prompt, max_new_tokens=2048, temperature=0.4)


def page_ai_copilot():
    try:
        st.title("AI Bidding Co‑pilot")
        _require_ai_libs()

        # Check for selected opportunity from dashboard
        if 'selected_opportunity' in st.session_state and st.session_state.selected_opportunity:
            opp = st.session_state.selected_opportunity
            st.success(f"🎯 **Analyzing Opportunity:** {opp['title']}")
            st.info(f"**Agency:** {opp['agency']} | **P-Win Score:** {opp['p_win_score']}% | **NAICS:** {opp['naics_code']}")

            if st.button("Clear Selection"):
                del st.session_state.selected_opportunity
                st.rerun()
        else:
            st.warning("⚠️ No opportunity selected. Please go to the **Dashboard** page and select an opportunity to analyze.")
            st.stop()

        if 'vector_store' not in st.session_state:
            st.session_state.vector_store = None
        if 'sow_analysis' not in st.session_state:
            st.session_state.sow_analysis = None
        if 'doc_name' not in st.session_state:
            st.session_state.doc_name = ""

        with st.sidebar:
            st.header("1. Upload Document")
            uploaded = st.file_uploader("Upload a SOW (PDF or DOCX)", type=["pdf", "docx"])
            if st.button("Process Document"):
                if uploaded:
                    with st.spinner("Reading and analyzing document..."):
                        docs, error = load_document_text(uploaded)
                        if error:
                            st.error(error)
                        else:
                            st.session_state.vector_store = create_vector_store(docs)
                            st.session_state.doc_name = uploaded.name
                            st.session_state.sow_analysis = None
                            st.success(f"Processed '{st.session_state.doc_name}'.")
                else:
                    st.warning("Please upload a document first.")

        if st.session_state.vector_store:
            st.header(f"Analysis for: :blue[{st.session_state.doc_name}]")
            llm = setup_llm()
            if not llm:
                st.stop()
            index, chunks, _, model = st.session_state.vector_store

            tab1, tab2, tab3, tab4, tab5 = st.tabs(["SOW Analysis", "Draft Subcontractor SOW", "Find Local Partners", "Proposal Outline", "Compliance Matrix"])

            with tab1:
                st.subheader("Extract Key SOW Details")
                if st.button("Extract SOW Details"):
                    with st.spinner("AI analyzing the SOW..."):
                        query = "Extract Scope, Technical Specs, Performance Metrics, Timeline/Milestones, Evaluation Criteria."
                        context = get_context(index, model, query, chunks)
                        prompt = f"""
You are a government contract analyst. Based ONLY on the following context from a Statement of Work (SOW), extract the requested information in Markdown.\n\nCONTEXT:\n{context}\n\nTASK:\n1. Scope of Work\n2. Technical Specifications\n3. Performance Metrics\n4. Timeline and Milestones\n5. Evaluation Criteria
"""
                        analysis = execute_ai_task(llm, prompt)
                    st.session_state.sow_analysis = analysis
                    st.markdown(analysis)

                if st.session_state.sow_analysis:
                    st.markdown(st.session_state.sow_analysis)

        with tab2:
            st.subheader("Generate Statement of Work for Subcontractors")
            if st.button("Draft Subcontractor SOW"):
                if st.session_state.sow_analysis:
                    with st.spinner("AI drafting subcontractor SOW..."):
                        prompt = f"""
You are a prime contractor creating a Statement of Work (SOW) to get a quote from a subcontractor. Based on the analysis below, rewrite the 'Scope of Work' and 'Technical Specifications' into a concise SOW for a subcontractor.\n\nGOVERNMENT SOW ANALYSIS:\n{st.session_state.sow_analysis}
"""
                        sub_sow = execute_ai_task(llm, prompt)
                        st.markdown(sub_sow)
                else:
                    st.warning("Run 'SOW Analysis' first.")

        with tab3:
            st.subheader("Find Potential Subcontracting Partners")
            st.write("AI identifies required capabilities, then searches for companies with those skills.")

            col1, col2 = st.columns(2)
            with col1:
                site_location = st.text_input("Location (e.g., Elkins, WV)", help="City, State where partners are needed")
            with col2:
                manual_keywords = st.text_input("Manual Keywords (optional)", help="Override AI analysis with specific keywords")

            if st.button("Find Potential Partners"):
                if not site_location:
                    st.error("Please enter a location.")
                else:
                    with st.spinner("Identifying required capabilities and searching for partners..."):
                        # Determine search keywords
                        if manual_keywords:
                            keywords = [kw.strip() for kw in manual_keywords.split(',') if kw.strip()]
                        elif st.session_state.sow_analysis:
                            # Use AI to extract capabilities from SOW analysis
                            prompt = f"""
Based on the following SOW analysis, identify 2-3 specific technical capabilities or service types needed for subcontracting. Return only the capability names separated by commas (e.g., "cybersecurity services, cloud migration, software development").

SOW ANALYSIS:
{st.session_state.sow_analysis}

CAPABILITIES:
"""
                            ai_response = execute_ai_task(llm, prompt).strip()
                            keywords = [kw.strip() for kw in ai_response.split(',') if kw.strip()]
                        else:
                            st.error("Please run 'SOW Analysis' first or provide manual keywords.")
                            st.stop()

                        st.write(f"🔍 **Searching for:** {', '.join(keywords)}")
                        st.write(f"📍 **Location:** {site_location}")

                        # Use our partner discovery function
                        partners = find_partners(keywords, site_location, max_results=8)

                        if not partners:
                            st.warning("No potential partners found. Try different keywords or a broader location.")
                        else:
                            st.success(f"Found {len(partners)} potential partners:")

                            # Display results with "Add to PRM" buttons
                            for i, partner in enumerate(partners):
                                with st.expander(f"🏢 {partner['company_name']}", expanded=i < 3):
                                    col1, col2 = st.columns([3, 1])

                                    with col1:
                                        st.write(f"**Website:** {partner['website']}")
                                        st.write(f"**Description:** {partner['description']}")
                                        st.write(f"**Capabilities:** {', '.join(partner['capabilities'])}")
                                        st.write(f"**Found via:** {partner['source_query']}")

                                    with col2:
                                        if st.button(f"Add to PRM", key=f"add_partner_{i}"):
                                            success, message = add_subcontractor_to_db(
                                                company_name=partner['company_name'],
                                                capabilities=partner['capabilities'],
                                                website=partner['website'],
                                                location=site_location,
                                                trust_score=30,  # Low initial trust for discovered partners
                                                vetting_notes=f"Discovered via search: {partner['source_query']}"
                                            )

                                            if success:
                                                st.success("✅ Added to PRM!")
                                            else:
                                                st.warning(f"⚠️ {message}")

        with tab4:
            st.subheader("Generate Proposal Table of Contents")
            st.write("Create a proposal outline based on the evaluation criteria.")
            if st.button("Generate Outline"):
                if st.session_state.sow_analysis:
                    with st.spinner("AI creating the proposal outline..."):
                        prompt = f"""
You are a proposal manager. Based ONLY on the 'Evaluation Criteria' from the SOW analysis below, create a formal Table of Contents for a proposal response. Each main criterion should be a main section.\n\nSOW ANALYSIS (Evaluation Criteria section):\n{st.session_state.sow_analysis}\n\nTASK:\nGenerate a concise Table of Contents.
"""
                        toc = execute_ai_task(llm, prompt)
                        st.markdown(toc)
                else:
                    st.warning("Run 'SOW Analysis' first.")

        with tab5:
            st.subheader("Generate Compliance Matrix")
            st.write("Extract requirements from the SOW and create a compliance matrix.")

            if st.button("Generate Compliance Matrix"):
                if st.session_state.vector_store:
                    with st.spinner("AI extracting requirements from SOW..."):
                        # Get full SOW text for requirement extraction
                        context = get_context(index, model, "requirements contractor shall must will", chunks)

                        prompt = f"""You are a government contract compliance specialist. Analyze the following text from a Statement of Work. Extract every sentence that contains a direct requirement for the contractor (phrases like "the contractor shall," "the offeror must," "the system will," etc.).

Return the output as a JSON array of objects, where each object has two keys: "requirement_text" and "sow_section".

SOW TEXT:
---
{context}
---
"""

                        response = execute_ai_task(llm, prompt)

                        try:
                            # Parse JSON response
                            import re
                            json_match = re.search(r'\[.*\]', response, re.DOTALL)
                            if json_match:
                                requirements_json = json.loads(json_match.group())

                                # Convert to DataFrame
                                df_requirements = pd.DataFrame(requirements_json)
                                df_requirements["Our Approach"] = ""  # Empty column for user to fill

                                st.success(f"Extracted {len(df_requirements)} requirements")

                                # Display editable dataframe
                                edited_requirements = st.data_editor(
                                    df_requirements,
                                    width="stretch",
                                    column_config={
                                        "requirement_text": st.column_config.TextColumn("Requirement", width="large"),
                                        "sow_section": st.column_config.TextColumn("SOW Section", width="medium"),
                                        "Our Approach": st.column_config.TextColumn("Our Approach", width="large"),
                                    },
                                    hide_index=True,
                                )

                                # Download button for CSV
                                csv = edited_requirements.to_csv(index=False)
                                st.download_button(
                                    label="Download Compliance Matrix as CSV",
                                    data=csv,
                                    file_name=f"compliance_matrix_{st.session_state.get('doc_name', 'sow')}.csv",
                                    mime="text/csv"
                                )
                            else:
                                st.error("Could not parse requirements from AI response. Please try again.")
                                st.text_area("Raw AI Response:", response, height=200)

                        except Exception as e:
                            st.error(f"Error processing requirements: {str(e)}")
                            st.text_area("Raw AI Response:", response, height=200)
            else:
                st.info("Click the button above to generate a compliance matrix.")

    except Exception as e:
        st.error(f"""
        **AI Co-pilot Error**

        An error occurred while loading the AI Co-pilot. This could be due to:

        1. **Missing AI Libraries**: Some AI/ML dependencies may not be installed
        2. **Model Loading Issues**: AI model files may be missing or corrupted
        3. **Session State Issues**: Try refreshing the page

        **Error Details**: {str(e)}

        **To Fix This:**
        - Try refreshing the page (F5)
        - Check that all AI dependencies are installed
        - Ensure model files are available
        """)

        # Show debug information
        with st.expander("Debug Information"):
            st.write("**Error Type:**", type(e).__name__)
            st.write("**Error Message:**", str(e))
            import traceback
            st.code(traceback.format_exc())

# ------------------------
# Partner Relationship Manager (Phase 3)
# ------------------------

def page_prm():
    try:
        st.title("Partner Relationship Manager")
        st.write("Manage your subcontractor network and partner relationships.")

        tab1, tab2, tab3 = st.tabs(["Manage Partners", "Add New Partner", "RFQ Management"])

        with tab1:
            st.subheader("Current Partners")

            try:
                engine = setup_database()

                # Try to get subcontractors, create table if it doesn't exist
                try:
                    df = pd.read_sql(
                        "SELECT id, company_name, capabilities, contact_email, contact_phone, website, location, trust_score, vetting_notes, created_date FROM subcontractors ORDER BY trust_score DESC, company_name",
                        engine
                    )
                except Exception:
                    # Table doesn't exist, create it
                    metadata = MetaData()
                    metadata.reflect(bind=engine)
                    metadata.create_all(engine)
                    df = pd.DataFrame()  # Empty dataframe

                if not df.empty:
                    # Display editable dataframe
                    edited_df = st.data_editor(
                        df,
                        width="stretch",
                        column_config={
                            "id": st.column_config.NumberColumn("ID", disabled=True),
                            "company_name": st.column_config.TextColumn("Company Name", width="medium"),
                            "capabilities": st.column_config.ListColumn("Capabilities"),
                            "contact_email": st.column_config.TextColumn("Email", width="medium"),
                            "contact_phone": st.column_config.TextColumn("Phone", width="small"),
                            "website": st.column_config.LinkColumn("Website", width="medium"),
                            "location": st.column_config.TextColumn("Location", width="medium"),
                            "trust_score": st.column_config.NumberColumn("Trust Score", min_value=0, max_value=100, width="small"),
                            "vetting_notes": st.column_config.TextColumn("Notes", width="large"),
                            "created_date": st.column_config.DateColumn("Added", disabled=True),
                        },
                        hide_index=True,
                        num_rows="dynamic"
                    )

                if st.button("Save Changes"):
                    # Update database with changes
                    try:
                        metadata = MetaData()
                        metadata.reflect(bind=engine)
                        subcontractors_table = metadata.tables['subcontractors']

                        with engine.connect() as conn:
                            for _, row in edited_df.iterrows():
                                if pd.notna(row['id']):  # Only update existing records
                                    conn.execute(
                                        subcontractors_table.update().where(
                                            subcontractors_table.c.id == int(row['id'])
                                        ).values(
                                            company_name=row['company_name'],
                                            capabilities=row['capabilities'] if isinstance(row['capabilities'], list) else [str(row['capabilities'])],
                                            contact_email=row['contact_email'] or "",
                                            contact_phone=row['contact_phone'] or "",
                                            website=row['website'] or "",
                                            location=row['location'] or "",
                                            trust_score=int(row['trust_score']) if pd.notna(row['trust_score']) else 50,
                                            vetting_notes=row['vetting_notes'] or ""
                                        )
                                    )
                            conn.commit()
                        st.success("Changes saved successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving changes: {str(e)}")
            else:
                st.info("No partners in database yet. Add some partners using the 'Add New Partner' tab.")

        except Exception as e:
            st.error(f"Database error: {str(e)}")

    with tab2:
        st.subheader("Add New Partner")

        with st.form("add_partner_form"):
            col1, col2 = st.columns(2)

            with col1:
                company_name = st.text_input("Company Name*", help="Required field")
                contact_email = st.text_input("Contact Email")
                website = st.text_input("Website URL")
                trust_score = st.slider("Trust Score", 0, 100, 50, help="Initial trust rating (0-100)")

            with col2:
                capabilities = st.text_area("Capabilities", help="Enter capabilities separated by commas (e.g., Software Development, Cybersecurity, Cloud Services)")
                contact_phone = st.text_input("Contact Phone")
                location = st.text_input("Location")
                vetting_notes = st.text_area("Vetting Notes", help="Internal notes about this partner")

            submitted = st.form_submit_button("Add Partner")

            if submitted:
                if not company_name.strip():
                    st.error("Company name is required!")
                else:
                    # Parse capabilities
                    caps_list = [cap.strip() for cap in capabilities.split(',') if cap.strip()] if capabilities else []

                    success, message = add_subcontractor_to_db(
                        company_name=company_name.strip(),
                        capabilities=caps_list,
                        contact_email=contact_email.strip(),
                        contact_phone=contact_phone.strip(),
                        website=website.strip(),
                        location=location.strip(),
                        trust_score=trust_score,
                        vetting_notes=vetting_notes.strip()
                    )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    with tab3:
        st.subheader("RFQ Management")
        st.write("Generate and dispatch RFQs to selected partners for specific opportunities.")

        # Get available opportunities
        try:
            engine = setup_database()
            opportunities_df = pd.read_sql(
                "SELECT notice_id, title, agency, response_deadline, p_win_score FROM opportunities WHERE status != 'Closed' ORDER BY p_win_score DESC LIMIT 20",
                engine
            )

            if not opportunities_df.empty:
                # Select opportunity
                selected_opp = st.selectbox(
                    "Select Opportunity for RFQ",
                    options=opportunities_df['notice_id'].tolist(),
                    format_func=lambda x: f"{opportunities_df[opportunities_df['notice_id']==x]['title'].iloc[0]} (P-Win: {opportunities_df[opportunities_df['notice_id']==x]['p_win_score'].iloc[0]}%)"
                )

                if selected_opp:
                    opp_details = opportunities_df[opportunities_df['notice_id'] == selected_opp].iloc[0]
                    st.info(f"**Selected:** {opp_details['title']}\n**Agency:** {opp_details['agency']}\n**Deadline:** {opp_details['response_deadline']}")

                    # Get matching subcontractors
                    subcontractors = get_subcontractors_for_opportunity([])  # Get all for now

                    if subcontractors:
                        st.subheader("Select Partners for RFQ")

                        # Multi-select for partners
                        partner_options = {f"{sc['company_name']} (Trust: {sc['trust_score']})": sc['id'] for sc in subcontractors}
                        selected_partners = st.multiselect(
                            "Choose partners to send RFQ to:",
                            options=list(partner_options.keys()),
                            help="Select multiple partners to send the RFQ"
                        )

                        if selected_partners:
                            # Generate RFQ preview
                            if st.button("Generate RFQ Preview"):
                                with st.spinner("Generating RFQ..."):
                                    rfq_content = generate_rfq(
                                        sow_text="[SOW content would be extracted from opportunity raw_data]",
                                        opportunity_title=opp_details['title'],
                                        deadline=opp_details['response_deadline']
                                    )

                                    st.subheader("RFQ Preview")
                                    st.text_area("RFQ Content", rfq_content, height=400)

                                    # Simulate sending RFQs
                                    if st.button("Send RFQs to Selected Partners"):
                                        # In a real implementation, this would:
                                        # 1. Save RFQ to database
                                        # 2. Send emails to partners
                                        # 3. Create tracking records

                                        st.success(f"✅ RFQ sent to {len(selected_partners)} partners!")
                                        st.info("📧 Email notifications would be sent to partner contacts")
                                        st.info("🔗 Partners would receive unique links to submit quotes")

                                        # Show what would happen
                                        for partner_name in selected_partners:
                                            partner_id = partner_options[partner_name]
                                            partner_info = next(sc for sc in subcontractors if sc['id'] == partner_id)
                                            st.write(f"• **{partner_info['company_name']}** - {partner_info['contact_email']}")
                    else:
                        st.warning("No partners in database. Add partners first in the 'Add New Partner' tab.")
            else:
                st.info("No active opportunities available for RFQ generation.")

        except Exception as e:
            st.error(f"Error loading opportunities: {str(e)}")

    except Exception as e:
        st.error(f"""
        **Partner Relationship Manager Error**

        An error occurred while loading the PRM. This could be due to:

        1. **Database Connection Issues**: Check your database connection
        2. **Data Processing Error**: Issue with partner data
        3. **Session State Issues**: Try refreshing the page

        **Error Details**: {str(e)}

        **To Fix This:**
        - Try refreshing the page (F5)
        - Check database connection
        - Verify partner data integrity
        """)

        # Show debug information
        with st.expander("Debug Information"):
            st.write("**Error Type:**", type(e).__name__)
            st.write("**Error Message:**", str(e))
            import traceback
            st.code(traceback.format_exc())

# ------------------------
# App Layout
# ------------------------

st.set_page_config(layout="wide", page_title="GovCon Suite")

# Initialize session state on every run
initialize_session_state()

st.sidebar.title("GovCon Suite Navigation")
page = st.sidebar.radio("Go to", ["Opportunity Dashboard", "AI Bidding Co‑pilot", "Partner Relationship Manager"])

# Add error handling for page navigation
try:
    if page == "Opportunity Dashboard":
        page_dashboard()
    elif page == "AI Bidding Co‑pilot":
        page_ai_copilot()
    elif page == "Partner Relationship Manager":
        page_prm()
except Exception as e:
    st.error(f"""
    **Application Error**

    An error occurred while loading the page. This could be due to:

    1. **Missing Dependencies**: Some AI/ML libraries may not be installed
    2. **Database Connection Issues**: Check your database connection
    3. **Session State Issues**: Try refreshing the page

    **Error Details**: {str(e)}

    **To Fix This:**
    - Try refreshing the page (F5)
    - Check the Docker containers are running: `docker compose ps`
    - Check the application logs: `docker compose logs app`
    """)

    # Show debug information
    with st.expander("Debug Information"):
        st.write("**Session State:**")
        st.json(dict(st.session_state))
        st.write("**Error Type:**", type(e).__name__)
        st.write("**Error Message:**", str(e))

        import traceback
        st.write("**Full Traceback:**")
        st.code(traceback.format_exc())

