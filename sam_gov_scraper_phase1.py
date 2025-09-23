# SAM.gov AI Automation System - Phase 1: Data Scraper (Version 3)
# This script connects to the SAM.gov Opportunities API, fetches contract data,
# stores it in a PostgreSQL database, and sends an expiration alert to Slack.

import os
import requests
import sqlalchemy
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, text, bindparam
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
import time
from datetime import datetime, timedelta
import json

# --- CONFIGURATION ---
# Replace these values with your actual configuration.

# 1. SAM.gov API Configuration
# Get your API key from https://open.gsa.gov/api/sam-entity-api/
SAM_API_KEY = os.getenv("d57QFEQCIIdegq3Y2nndqD4iyruX5ktwEXSev7MG", "")
# **IMPORTANT**: Find the expiration date in your GSA account and enter it here.
API_KEY_EXPIRATION_DATE = "2025-12-21" # Format: YYYY-MM-DD

# 2. Slack Webhook for Notifications
# Instructions to get a webhook URL are in the project documentation.
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# 3. PostgreSQL Database Configuration
# Example for a local PostgreSQL server: "postgresql://user:password@localhost:5432/dbname"
DB_CONNECTION_STRING = os.getenv("GOVCON_DB_URL", "postgresql://postgres:mysecretpassword@localhost:5434/sam_contracts")

# 4. Search Criteria Configuration
SEARCH_PARAMS = {
    'limit': 100,
    'postedFrom': '09/22/2025',
    'postedTo': '09/23/2025',
    'ptype': 'o',
    'notice_type': 'Original Synopsis',
    'naics': '541511'
}

# --- NOTIFICATION FUNCTIONS ---

def send_slack_notification(webhook_url, message):
    """
    Sends a simple notification message to a Slack channel via a webhook.
    """
    if not webhook_url or webhook_url == "YOUR_SLACK_WEBHOOK_URL_HERE":
        print("Slack webhook URL not configured. Skipping notification.")
        return

    headers = {'Content-Type': 'application/json'}
    # Slack's webhook payload format is simple: {"text": "your message"}
    payload = {
        "text": message
    }
    try:
        response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print("Successfully sent Slack notification.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Slack notification: {e}")

def check_api_key_expiration():
    """
    Checks if the SAM.gov API key is expiring within the next 14 days and sends a notification.
    """
    try:
        exp_date = datetime.strptime(API_KEY_EXPIRATION_DATE, "%Y-%m-%d")
        days_until_expiry = (exp_date - datetime.now()).days

        if 0 < days_until_expiry <= 14:
            message = (f"**ALERT:** The SAM.gov API key is expiring in *{days_until_expiry} days* "
                       f"(on {API_KEY_EXPIRATION_DATE}). Please renew it soon to avoid service interruption.")
            send_slack_notification(SLACK_WEBHOOK_URL, message)
        elif days_until_expiry <= 0:
             message = (f"**CRITICAL ALERT:** The SAM.gov API key *has expired*! "
                       f"The system cannot fetch new opportunities. Please renew it immediately.")
             send_slack_notification(SLACK_WEBHOOK_URL, message)

    except ValueError:
        print("API_KEY_EXPIRATION_DATE is not in the correct 'YYYY-MM-DD' format. Skipping check.")
    except Exception as e:
        print(f"An error occurred during API key expiration check: {e}")


# --- DATABASE SETUP ---

def setup_database():
    """
    Connects to the PostgreSQL database and creates the 'opportunities' table if it doesn't exist.
    """
    # ... existing code ...
    try:
        engine = create_engine(DB_CONNECTION_STRING)
        metadata = MetaData()

        # Define the table structure
        opportunities = Table('opportunities', metadata,
            Column('id', Integer, primary_key=True),
            # The noticeId is the unique identifier from SAM.gov
            Column('notice_id', String, unique=True, nullable=False),
            Column('title', String),
            Column('agency', String),
            Column('posted_date', String),
            Column('response_deadline', String),
            Column('naics_code', String),
            Column('set_aside', String),
            Column('status', String, default='New', nullable=False), # For our internal workflow tracking
            # Store the full, raw API data for future analysis
            Column('raw_data', JSONB)
        )

        metadata.create_all(engine)
        print("Database connection successful and 'opportunities' table is ready.")
        return engine
    except Exception as e:
        print(f"Error connecting to or setting up the database: {e}")
        print("Please ensure PostgreSQL is running and the DB_CONNECTION_STRING is correct.")
        return None

# --- API DATA FETCHING ---

def fetch_opportunities(api_key, params):
    """
    Fetches contract opportunities from the SAM.gov API.
    """
    # ... existing code ...
    base_url = "https://api.sam.gov/prod/opportunities/v2/search"
    params['api_key'] = api_key

    print(f"Fetching data from SAM.gov with params: {params}...")

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        print(f"Successfully fetched {len(data.get('opportunitiesData', []))} opportunities.")
        return data.get('opportunitiesData', [])
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.text}")
    except requests.exceptions.RequestException as req_err:
        print(f"A request error occurred: {req_err}")
    except Exception as e:
        print(f"An unexpected error occurred during API fetch: {e}")
    return []

# --- DATA PROCESSING AND STORAGE ---

def store_opportunities(engine, opportunities_data):
    """
    Parses and stores the fetched opportunities in the PostgreSQL database.
    Avoids inserting duplicates based on the unique 'notice_id'.
    """
    # ... existing code ...
    if not opportunities_data:
        print("No new opportunities to store.")
        return

    insert_count = 0
    with engine.connect() as connection:
        # Ensure the connection is not in an aborted transaction state from any prior operation
        try:
            connection.rollback()
        except Exception:
            pass

        metadata = MetaData()
        opportunities_table = Table('opportunities', metadata, autoload_with=engine)

        for item in opportunities_data:
            try:
                # Prepare the data for insertion
                record = {
                    'notice_id': item.get('noticeId'),
                    'title': item.get('title'),
                    'agency': item.get('fullParentPathName'),
                    'posted_date': item.get('postedDate'),
                    'response_deadline': item.get('responseDeadLine'),
                    'naics_code': item.get('naicsCode'),
                    'set_aside': item.get('typeOfSetAside'),
                    'raw_data': item
                }

                # Use SQLAlchemy Core insert with the reflected table to ensure correct typing (JSONB handled automatically)
                stmt = opportunities_table.insert().values(**record)
                connection.execute(stmt)
                insert_count += 1
            except IntegrityError:
                # This error occurs if the notice_id already exists, which is expected.
                # We can safely ignore it and move to the next item.
                pass # print(f"Skipping duplicate record: {item.get('noticeId')}")
            except Exception as e:
                # Roll back this failed insert so subsequent inserts can proceed
                connection.rollback()
                # Provide detailed diagnostics for root cause
                try:
                    import traceback
                    print(f"An error occurred while inserting data for noticeId {item.get('noticeId')}: {repr(e)}")
                    if hasattr(e, 'orig'):
                        print(f"DBAPI original error: {repr(e.orig)}")
                    traceback.print_exc(limit=1)
                except Exception:
                    pass

        # Commit the transaction to save all successful records
        connection.commit()

    print(f"Process complete. Inserted {insert_count} new opportunities into the database.")


# --- MAIN EXECUTION ---

if __name__ == "__main__":
    print("--- Starting SAM.gov Opportunity Scraper ---")

    # Step 0: Check for API Key Expiration and send an alert if needed.
    check_api_key_expiration()

    # Step 1: Set up the database connection and table
    db_engine = setup_database()

    if db_engine:
        # Step 2: Fetch the latest opportunities from the API
        opportunities = fetch_opportunities(SAM_API_KEY, SEARCH_PARAMS)

        # Step 3: Store the new opportunities in the database
        store_opportunities(db_engine, opportunities)

    print("--- Scraper run finished. ---")
