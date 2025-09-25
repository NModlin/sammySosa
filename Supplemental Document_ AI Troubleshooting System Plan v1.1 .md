# **Supplemental Document: AI Troubleshooting System Plan v1.1 (Expanded Edition)**

**Objective:** This document provides a granular, in-depth exploration of the architecture, workflow, and agent responsibilities outlined in the "AI-Powered Collaborative Troubleshooting System Plan v1.1." It is intended for architects, developers, and project managers to understand the specific mechanics, technologies, and logic behind each phase of the system.

### **Section 1: Detailed System Architecture Breakdown**

This section dissects the individual components of the system, detailing their technology stacks, internal processes, data models, and security considerations.

#### **1.1 Client (sammySosa)**

The client application serves as the exclusive human-machine interface for the system. Its design philosophy prioritizes clarity, safety, and operational efficiency, ensuring that developers and reviewers can interact with complex backend processes with confidence.

* **Technology Stack & Rationale:**  
  * **UI Framework:** Streamlit. This choice is deliberate for its rapid development cycle, which is ideal for internal tools. Because it is pure Python, it allows backend developers to build and maintain the UI without a dedicated frontend team or context-switching to a JavaScript framework like React or Vue. Its component-based nature is well-suited for the form-based and data-display-centric needs of this application.  
  * **API Communication:** The standard Python requests library will be employed, utilizing requests.Session objects to manage persistent connections and handle cookies or authentication tokens efficiently. All API calls will have explicit timeouts (e.g., 30 seconds) and robust error handling to gracefully manage network issues or backend downtime, presenting user-friendly error messages rather than crashing.  
  * **Configuration:** A config.ini file, parsed using Python's configparser library, will manage environment-specific settings. This file will be structured with sections like \[development\], \[staging\], and \[production\] to hold the respective api\_base\_url. This approach avoids hardcoding URLs and allows for seamless deployment across different environments. The application will determine which section to use based on an environment variable.  
* **Detailed UI/UX Flow for Plan Submission:**  
  1. **Initiation:** The workflow begins in the developer's IDE. The **VS Code Augment Extension** provides a command palette option, "Generate Troubleshooting Plan." Upon invocation, it analyzes the active code file and its directory for context, then presents the developer with a modal window containing a dropdown of potential solutions. The selected solution plan is formatted in clean, copy-paste-ready YAML for structural clarity.  
  2. **Navigation:** Within the sammySosa Streamlit app, the main dashboard will feature a sidebar navigation menu. The developer will click on "Submit New Plan," which will render the main submission view.  
  3. **Form Completion:** The submission form is the primary data entry point.  
     * **Plan Title:** A single-line text input with client-side validation for length (e.g., 150 characters max) and to prevent empty submissions.  
     * **Problem Description:** A multi-line st.text\_area component that supports Markdown for rich text formatting, allowing developers to include code snippets, bullet points, and links for maximum context.  
     * **Plan Steps:** A larger st.text\_area where the YAML from the VS Code extension is pasted. Client-side Python code will attempt to parse the YAML upon entry to provide immediate feedback if the structure is invalid, preventing malformed data from being sent to the backend.  
  4. **Submission Trigger:** The "Submit for Review" button, when clicked, will trigger a function that bundles the form data into a structured JSON payload (e.g., { "title": "...", "description": "...", "steps\_yaml": "..." }).  
  5. **User Feedback:** The system provides immediate, non-blocking feedback. Upon a successful POST request (201 Created), a green "toast" notification appears at the bottom of the screen saying, "Success\! Plan submitted with ID: {plan\_id}." In case of a backend error, a red, more persistent notification will appear with the error details returned from the API (e.g., "Error 422: Invalid input in Plan Steps.").  
* **Detailed UI/UX Flow for Plan Review:**  
  1. **Accessing the Queue:** The "Review Queue" page is restricted. Streamlit's session state will be used to manage user authentication, ensuring only users with a "reviewer" role can access this page.  
  2. **Fetching Data:** When the page loads, a spinner animation provides visual feedback while the GET request to /plans?status=pending\_human\_review is in progress. The results are cached for a short period (e.g., 1 minute) to improve performance on quick revisits.  
  3. **Displaying Plans:** The list of plans is rendered using st.expander components. Each plan is collapsed by default, showing only the title and submitter.  
     * **Expanded View:** Clicking on a plan expands it to show the full description and the structured plan steps.  
     * **\[CRITICAL\] AI Sanity Check Feedback:** This is the most prominent element in the expanded view. It is rendered inside a visually distinct st.info or st.warning block with a large icon. The feedback is formatted as a list of "Potential Risks" and "Suggestions," making it easily scannable for the human reviewer.  
  4. **Decision Making:**  
     * **Approve:** Clicking this button shows a confirmation modal: "Are you sure you want to approve this plan for execution?" This prevents accidental clicks.  
     * **Reject:** Clicking this button opens a modal with a required text area for the reviewer to provide a justification for the rejection, ensuring feedback is captured.  
  5. **State Update:** The application uses an optimistic UI approach. Upon clicking "Approve" or "Reject" in the modal, the plan is immediately removed from the UI, and the API call is made in the background. If the API call fails, the plan reappears with an error message, ensuring a fluid user experience.

#### **1.2 Backend (GremlinsAI\_backend)**

The backend is the orchestrated brain of the operation, handling API requests, intelligent analysis, sandboxed execution, and knowledge persistence.

* **Technology Stack & Implementation Details:**  
  * **API Framework:** FastAPI. Pydantic models will be used for rigorous input validation and serialization, ensuring data integrity at the edge. The dependency injection system will manage database sessions and other resources, making the code clean and testable.  
  * **AI Orchestration:** CrewAI will be configured with custom Tool definitions that wrap the functions the agents can use (e.g., a run\_git\_command tool, a run\_pytest\_suite tool). These tools are the only way agents can interact with the underlying system, forming a critical security boundary.  
  * **Source Control:** gitpython will be used to interact with a local clone of the server's repository. All operations will be wrapped in try...except blocks to handle specific GitCommandError exceptions, such as authentication failures or merge conflicts.  
  * **Testing:** The subprocess.run command will be used to invoke pytest. The command will be executed within a specific working directory (the newly checked-out branch) and will be configured to capture stdout and stderr completely for logging and reporting purposes.  
  * **Database:** A dual-database approach will be used.  
    * **Primary Database (PostgreSQL):** A relational database will store the structured data for plans. The plans table schema will include fields like id (UUID), title (VARCHAR), description (TEXT), steps\_yaml (TEXT), status (VARCHAR), ai\_feedback (JSONB), execution\_logs (TEXT), created\_at (TIMESTAMPTZ), and updated\_at (TIMESTAMPTZ).  
    * **Vector Database (ChromaDB):** This database will store the generalized knowledge embeddings for semantic search.  
* **Detailed Task Hub API Endpoints (with Models):**  
  * POST /plans:  
    * **Request Body (Pydantic Model):** class PlanCreate(BaseModel): title: str; description: str; steps\_yaml: str  
    * **Success Response:** 201 Created, { "id": "...", "status": "pending\_ai\_review" }  
    * **Error Response:** 422 Unprocessable Entity if YAML parsing fails or validation fails.  
  * GET /plans:  
    * **Query Parameter:** status: Optional\[str\] \= None  
    * **Success Response:** 200 OK, \[{"id": "...", "title": "...", ...}\]  
  * POST /plans/{plan\_id}/approve:  
    * **Success Response:** 202 Accepted, { "message": "Plan approved and queued for execution." }  
    * **Error Response:** 404 Not Found if plan\_id does not exist.  
  * PATCH /plans/{plan\_id}:  
    * **Request Body:** class PlanUpdate(BaseModel): status: Optional\[str\] \= None; execution\_logs: Optional\[str\] \= None  
    * **Success Response:** 200 OK, returns the updated plan object.  
* **Internal Service: "Plan Sanity Check"**  
  1. **Trigger:** Implemented using FastAPI's BackgroundTasks. This allows the API to return an immediate response to the client while the more time-consuming analysis happens asynchronously.  
  2. **Intelligence Layer:** A direct call to an LLM is chosen for simplicity and speed over instantiating a full CrewAI agent for this task. This is a targeted, stateless analysis.  
  3. **Prompt Engineering:** The system prompt will be highly detailed: "You are an AI DevOps and Security SME. Your sole purpose is to analyze the following YAML plan for potential negative impacts on a production system. Identify risks related to data loss, service downtime, security vulnerabilities, or unintended side effects. Provide your feedback in a structured JSON format with 'risks' and 'suggestions' keys. Be concise and direct."  
  4. **Output:** The LLM's JSON output is parsed and stored directly in the ai\_feedback JSONB column of the plans table.  
  5. **State Transition:** A final UPDATE query changes the plan's status from pending\_ai\_review to pending\_human\_review.

### **Section 2: The Enhanced Troubleshooting Workflow (Granular Detail)**

This section provides a complete, sequential narrative of a plan's lifecycle, detailing every technical step, state change, and data transformation.

#### **I. Plan (Local Generation)**

The process is initiated within the developer's local environment, a critical design choice to ensure context is not lost. The **VS Code Augment Extension** uses the official VS Code API to access the content of the active text editor and read the file names in the current workspace. This provides immediate, relevant context. It then makes a POST request to a secure, read-only endpoint on the backend (e.g., /knowledge/search), sending the code context and error message. The backend performs a vector similarity search and returns the most relevant historical solutions, which the extension then uses to formulate its suggestions.

#### **II. Review (AI \+ Human-in-the-Loop)**

This phase is the system's core ethical and safety control. Every state transition is recorded in an immutable audit log table, capturing the plan\_id, the old status, the new status, the timestamp, and the user or service that initiated the change. This creates a fully traceable record of the review process. The intentional layering of information for the reviewer is a cognitive offloading technique: by seeing the AI's analysis last, the human first forms their own opinion based on the raw plan, then uses the AI's feedback to challenge or confirm their initial assessment, leading to a more robust final decision.

#### **III. Execute (Safe, Branch-Based Execution)**

This is the automated heart of the system, operating under a strict, non-negotiable protocol.

1. **The Hand-off:** An approved plan is added to a Celery task queue, which provides durability and retry mechanisms. A dedicated CrewAI worker process polls this queue.  
2. **Delegation:** The WorkflowManagerAgent receives the plan ID. Its first task is to fetch the full plan details from the database. It then constructs a new Task for the DevOpsAgent, providing the plan steps as the task description.  
3. **The DevOpsAgent's Precise Protocol:**  
   1. **Initialization:** The agent receives the task and plan data.  
   2. **Repository Connection:** It establishes a Repo object using gitpython.  
   3. **Synchronization:** It runs git.fetch('--prune') to clean up stale remote branches and ensure a current view of the repository.  
   4. **Branch Creation:** It creates a new branch using repo.create\_head().  
   5. **Workspace Setup:** The agent checks out this new branch. The entire execution environment is a short-lived Docker container spawned specifically for this task, ensuring complete filesystem isolation.  
   6. **Step-by-Step Execution:** The agent parses the plan's YAML. For each step, it identifies the action type (e.g., file\_edit, shell\_command). All file paths are sanitized and resolved against the sandboxed root directory to prevent path traversal attacks. All shell commands are logged to the execution\_logs field in the database in real-time.  
   7. **Committing Changes:** After applying all steps, the agent commits the changes.  
   8. **Triggering Validation:** The agent executes the test suite.  
   9. **Result Analysis:** It uses Python's xml.etree.ElementTree to parse the junit.xml output, checking for any \<failure\> or \<error\> tags.  
   10. **Reporting Success:** If no failures are found, it pushes the branch and updates the plan status.  
   11. **Reporting Failure:** If tests fail, it captures the failure details from the XML and includes them in the execution\_logs before deleting the remote branch.

#### **IV. Remember (Knowledge Storage)**

This final phase transforms a single troubleshooting event into reusable institutional knowledge, creating a virtuous cycle of improvement.

1. **Continuous Observation:** The DocumentationAgent subscribes to events during the execution phase. It logs every action and its outcome to a temporary, structured log.  
2. **Compiling the FinalReport:** The report is a detailed JSON object containing the original problem description, the full execution log, the final test results, and the YAML plan itself.  
3. **Generalization via the Knowledge Abstractor:** This agent's prompt is highly engineered. It is explicitly told to *remove* implementation-specific details like server names, file paths, and line numbers. Its goal is to extract the abstract *pattern* of the problem and its solution.  
4. **Storing Knowledge:** The resulting abstract text is passed to an embedding model (e.g., a sentence transformer). The resulting vector is stored in ChromaDB with associated metadata, including a unique ID, the original plan\_id for reference, and keywords for potential filtered searches in the future.