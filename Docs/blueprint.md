Technical Blueprint: GovCon Automation SuiteVersion: 1.0Status: Ready for ImplementationPrimary Goal: To provide a detailed, task-oriented guide for an AI coding assistant or developer to build the GovCon Automation Suite.Phase 1: Foundation - The Unified Suite(Target Duration: 2 Months)Objective: Build the core Docker-based, multi-page Streamlit application. This phase focuses on creating a stable, unified platform with the essential manual tools that will be automated in later phases.Task 1.1: Project Scaffolding & Docker SetupAction: Create the project directory with the following files and folders:govcon_suite.py (Main application file)requirements.txtDockerfiledocker-compose.yml.env (for secrets)models/ (folder to store the LLM file)Details: Use the file contents from our previous discussion to populate these files. The docker-compose.yml should define two services: app and db.Task 1.2: Database Schema DefinitionAction: In govcon_suite.py, define the initial database tables using SQLAlchemy.Schema:-- opportunities Table
CREATE TABLE opportunities (
    id SERIAL PRIMARY KEY,
    notice_id VARCHAR(255) UNIQUE NOT NULL,
    title TEXT,
    agency TEXT,
    posted_date TIMESTAMP,
    response_deadline TIMESTAMP,
    naics_code VARCHAR(20),
    set_aside VARCHAR(50),
    raw_data JSONB -- Store the full, raw JSON response from the API
);
Task 1.3: Implement the Core Application Logic in govcon_suite.pyFunction run_scraper():Purpose: Fetch new opportunities from SAM.gov API and insert/update them in the opportunities table.Logic:Read SAM_API_KEY from environment variables.Construct the API request URL with appropriate date ranges.Handle API response, including pagination.For each opportunity, check if notice_id already exists in the database.If not, INSERT the new record. If it exists, UPDATE it.Function page_dashboard():Purpose: Create the UI for the Opportunity Dashboard.UI Components:st.title("Opportunity Dashboard")st.button("Run Scraper Manually") which calls run_scraper().st.data_editor to display the contents of the opportunities table.Add a checkbox column labeled "Analyze" to allow users to select one row.Workflow: When a row's "Analyze" checkbox is ticked, store that row's data in st.session_state.selected_opportunity and display an st.info message prompting the user to navigate to the Co-pilot page.Function page_ai_copilot():Purpose: Create the UI for the AI Bidding Co-pilot.Workflow:Check if st.session_state.selected_opportunity exists.If yes, display the opportunity's title and provide the full Co-pilot UI (initially, this can be the file uploader and analysis tabs). The key is to create a seamless transition from the dashboard.If no, display a message prompting the user to select an opportunity from the dashboard.Background Scheduler:Action: Use APScheduler to schedule run_scraper() to run on a cron schedule (e.g., daily at 3:00 AM).Phase 2: Intelligence & Analysis(Target Duration: 2 Months)Objective: Make the system proactive and intelligent by automating analysis and prioritization.Task 2.1: Implement P-Win ScoringDatabase Schema Changes:ALTER TABLE opportunities ADD COLUMN p_win_score INT;
ALTER TABLE opportunities ADD COLUMN analysis_summary TEXT;
Function calculate_p_win(opportunity_data):Purpose: Analyze an opportunity's raw data and return a "Probability of Win" score (0-100).Logic:Define a list of your company's core NAICS codes.Define a list of positive and negative keywords.Score based on:+50 points if NAICS code is a perfect match.+10 points for each positive keyword found in the title/description.-10 points for each negative keyword.Normalize score to be within 0-100.Workflow: Modify run_scraper() to call calculate_p_win() for each new opportunity and store the result in the p_win_score column.Task 2.2: Implement Proactive Slack NotificationsFunction send_slack_notification(opportunity):Purpose: Send a formatted message to a Slack webhook.Logic:Read SLACK_WEBHOOK_URL from environment variables.Construct a message using Slack's Block Kit format, including the opportunity title, agency, deadline, and P-Win score.Workflow: Modify run_scraper() to call send_slack_notification() for any opportunity where p_win_score is greater than a defined threshold (e.g., 75).Task 2.3: Implement Automated Compliance Matrix GeneratorUI Components (in page_ai_copilot):Add a new tab: st.tabs(["...", "Compliance Matrix"])Add a button: st.button("Generate Compliance Matrix")Add a download button for the generated CSV: st.download_button(...)Function generate_compliance_matrix(sow_text):Purpose: Use the LLM to extract requirements and create a matrix.AI Prompt Engineering:You are a government contract compliance specialist. Analyze the following text from a Statement of Work. Extract every sentence that contains a direct requirement for the contractor (phrases like "the contractor shall," "the offeror must," "the system will," etc.).

Return the output as a JSON array of objects, where each object has two keys: "requirement_text" and "sow_section".

SOW TEXT:
---
{sow_text}
---
Logic: Parse the JSON response from the LLM and convert it into a Pandas DataFrame with columns: Requirement, SOW Section, and Our Approach (to be completed).Phase 3: Subcontractor Ecosystem Management(Target Duration: 3 Months)Objective: Automate the entire process of finding, vetting, and getting quotes from subcontractors.Task 3.1: Build the Partner Relationship Manager (PRM)Database Schema Changes:CREATE TABLE subcontractors (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    capabilities TEXT[], -- Array of NAICS codes or keywords
    contact_email VARCHAR(255),
    trust_score INT,
    vetting_notes TEXT
);
UI Components:Create a new page: page_prm().Use st.form to add new subcontractors to the database.Use st.data_editor to display and edit existing subcontractors.Task 3.2: Implement Automated Partner DiscoveryFunction find_partners(keywords):Purpose: Search public sources for companies matching a set of keywords.Logic: Use the duckduckgo-search library to search for queries like f"{keyword} companies in Elkins, WV". Scrape the top results (company name, URL).Workflow (in page_ai_copilot):AI analyzes SOW to determine required capabilities (e.g., "Cybersecurity Auditing").User provides a location.The app calls find_partners() with the capabilities and location.Display results with a button "Add to PRM" next to each.Task 3.3: Build the Subcontractor Portal & RFQ SystemDatabase Schema Changes:CREATE TABLE quotes (
    id SERIAL PRIMARY KEY,
    opportunity_notice_id VARCHAR(255),
    subcontractor_id INT REFERENCES subcontractors(id),
    quote_data JSONB, -- Store submitted price, notes, etc.
    submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
Function generate_rfq(sow_text):Purpose: Use the LLM to draft an RFQ document.UI Components (in page_prm):Allow user to select an opportunity and multiple subcontractors.A button "Dispatch RFQ" will trigger an email (using a service like SendGrid) to the selected partners with a unique link.Subcontractor Portal (Separate Streamlit App or Page):A simple, secure page where a partner can view the RFQ and submit their quote via a standardized st.form. The form data is saved directly to the quotes table.Phase 4: Full Proposal & Financial Automation(Target Duration: 3 Months)Objective: Automate the final assembly of the proposal and handle post-award administrative tasks.Task 4.1: Implement AI "Red Team Review"UI Components (in page_ai_copilot):A new tab "Red Team Review".st.text_area for the user to paste their final proposal narrative.st.button("Run AI Red Team Review").AI Prompt Engineering:You are a government Source Selection Authority. The evaluation criteria from the SOW are: {evaluation_criteria}.

The contractor's proposal narrative is below.

Provide a critical review of this proposal. Score each evaluation criterion from 1 (poor) to 5 (excellent). Justify each score and provide specific, actionable feedback for improvement.

PROPOSAL NARRATIVE:
---
{proposal_text}
---
Task 4.2: Implement Automated Proposal AssemblyFunction assemble_proposal():Purpose: Combine various text and data components into a single DOCX file.Logic:Use the python-docx library.Create a new document.Add a title page.Generate a Table of Contents based on the AI-generated outline.Iterate through sections, inserting content (e.g., AI-generated text, past performance write-ups from the DB, subcontractor info).Provide a download link for the final document.Task 4.3: Implement Post-Award Project Plan GenerationFunction generate_poam(sow_text):Purpose: Use the LLM to extract tasks and milestones.AI Prompt Engineering:Analyze the "Timeline and Milestones" section of the following SOW. Extract all key tasks, deliverables, and deadlines.

Return the output as a JSON array of objects, where each object has keys: "task_name", "due_date", and "description".

SOW TEXT:
---
{sow_text}
---
