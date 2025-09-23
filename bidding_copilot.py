# SAM.gov AI Automation System - Phase 3, Version 3: AI Bidding Co-pilot
# This version activates the "Find Local Partners" feature with live web search
# using the duckduckgo-search library.

import streamlit as st
from pathlib import Path
import fitz  # PyMuPDF for PDFs
from docx import Document # python-docx for DOCX
from sentence_transformers import SentenceTransformer
import faiss # For the vector database
import numpy as np
from ctransformers import AutoModelForCausalLM
import re
# --- NEW LIBRARY FOR WEB SEARCH ---
from duckduckgo_search import DDGS

# --- CONFIGURATION ---
# 1. Path where you have saved the downloaded Large Language Model (LLM).
MODEL_PATH = "PATH_TO_YOUR_SAVED_LLM_FILE/mistral-7b-instruct-v0.1.Q4_K_M.gguf"
# 2. Name of the sentence transformer model for creating embeddings.
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'

# --- CORE AI & DOCUMENT PROCESSING FUNCTIONS (No changes here) ---

@st.cache_data
def load_document_text(file_uploader):
    if file_uploader is None:
        return None, "Please upload a document."
    documents = {}
    try:
        file_name = file_uploader.name
        file_extension = Path(file_name).suffix.lower()
        if file_extension == ".pdf":
            with fitz.open(stream=file_uploader.read(), filetype="pdf") as doc:
                text = "".join(page.get_text() for page in doc)
                documents[file_name] = text
        elif file_extension == ".docx":
            doc = Document(file_uploader)
            text = "\n".join([para.text for para in doc.paragraphs])
            documents[file_name] = text
        else:
            return None, "Unsupported file type. Please upload a PDF or DOCX file."
        if not documents:
             return None, "Could not read text from the document."
        return documents, None
    except Exception as e:
        return None, f"An error occurred while loading the document: {e}"

@st.cache_resource
def create_vector_store(documents):
    if not documents:
        return None
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    all_chunks = []
    doc_references = []
    for doc_name, text in documents.items():
        words = re.split(r'\s+', text)
        for i in range(0, len(words), 200):
            chunk = " ".join(words[i:i+250])
            all_chunks.append(chunk)
            doc_references.append(doc_name)
    st.info(f"Created {len(all_chunks)} text chunks from the document.")
    embeddings = model.encode(all_chunks, show_progress_bar=True)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings, dtype=np.float32))
    return index, all_chunks, doc_references, model

@st.cache_resource
def setup_llm():
    try:
        llm = AutoModelForCausalLM.from_pretrained(MODEL_PATH, model_type="mistral", gpu_layers=0)
        return llm
    except Exception as e:
        st.error(f"Failed to load language model at {MODEL_PATH}. Error: {e}")
        return None

def get_context(index, model, query, chunks):
    query_embedding = model.encode([query])
    _, top_k_indices = index.search(np.array(query_embedding, dtype=np.float32), k=8)
    context = "\n\n---\n\n".join([chunks[i] for i in top_k_indices[0]])
    return context

def execute_ai_task(llm, prompt):
    return llm(prompt, max_new_tokens=2048, temperature=0.4)

# --- STREAMLIT UI (Only Tab 3 is significantly changed) ---
st.set_page_config(layout="wide", page_title="AI Bidding Co-pilot")
st.title("AI Bidding Co-pilot for Government Contracts")

if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None
if 'sow_analysis' not in st.session_state:
    st.session_state.sow_analysis = None
if 'doc_name' not in st.session_state:
    st.session_state.doc_name = ""

with st.sidebar:
    st.header("1. Upload Document")
    uploaded_file = st.file_uploader("Upload a Statement of Work (PDF or DOCX)", type=["pdf", "docx"])
    if st.button("Process Document"):
        if uploaded_file:
            with st.spinner("Reading and analyzing document..."):
                docs, error = load_document_text(uploaded_file)
                if error:
                    st.error(error)
                else:
                    st.session_state.vector_store = create_vector_store(docs)
                    st.session_state.doc_name = uploaded_file.name
                    st.session_state.sow_analysis = None
                    st.success(f"Successfully processed '{st.session_state.doc_name}'!")
        else:
            st.warning("Please upload a document first.")

if st.session_state.vector_store:
    st.header(f"Analysis for: :blue[{st.session_state.doc_name}]")
    llm = setup_llm()
    if not llm:
        st.stop()
        
    index, chunks, doc_refs, model = st.session_state.vector_store

    tab1, tab2, tab3, tab4 = st.tabs([
        "SOW Analysis", 
        "Draft Subcontractor SOW", 
        "Find Local Partners", 
        "Proposal Outline"
    ])

    # ... Tabs 1 and 2 remain the same ...
    with tab1:
        st.subheader("Extract Key SOW Details")
        if st.button("Extract SOW Details"):
            with st.spinner("AI is analyzing the Statement of Work..."):
                query = "Extract the Scope of Work, Technical Specifications, Performance Metrics, Timeline/Milestones, and Evaluation Criteria from the document."
                context = get_context(index, model, query, chunks)
                prompt = f"""
                You are a government contract analyst. Based ONLY on the following context from a Statement of Work (SOW), extract the requested information. Present the output in clear, well-formatted Markdown.

                CONTEXT:
                {context}

                TASK:
                Extract the following five sections:
                1. Scope of Work (main tasks, objectives, deliverables)
                2. Technical Specifications (equipment, materials, methods, standards)
                3. Performance Metrics (quality standards, expected performance levels)
                4. Timeline and Milestones (schedules, key deadlines)
                5. Evaluation Criteria (how proposals will be judged)
                """
                analysis = execute_ai_task(llm, prompt)
                st.session_state.sow_analysis = analysis
                st.markdown(analysis)
        elif st.session_state.sow_analysis:
            st.markdown(st.session_state.sow_analysis)

    with tab2:
        st.subheader("Generate Statement of Work for Subcontractors")
        if st.button("Draft Subcontractor SOW"):
            if st.session_state.sow_analysis:
                with st.spinner("AI is drafting the subcontractor SOW..."):
                    prompt = f"""
                    You are a prime contractor creating a Statement of Work (SOW) to get a quote from a potential subcontractor. Your analysis of the government's SOW is below. 
                    Rewrite the 'Scope of Work' and 'Technical Specifications' sections into a clear, concise SOW for a subcontractor. Be direct and focus on the work to be performed.

                    GOVERNMENT SOW ANALYSIS:
                    {st.session_state.sow_analysis}

                    TASK:
                    Generate a detailed Statement of Work for a subcontractor.
                    """
                    sub_sow = execute_ai_task(llm, prompt)
                    st.markdown(sub_sow)
            else:
                st.warning("Please run the 'SOW Analysis' on the first tab before generating a subcontractor SOW.")

    # --- MODIFIED TAB 3 ---
    with tab3:
        st.subheader("Identify Potential Subcontracting Partners")
        st.write("First, the AI will identify the type of work. Then, it will perform a live web search for local companies.")
        site_location = st.text_input("Enter the City and State of the work site (e.g., Elkins, WV):")
        
        if st.button("Find Potential Partners"):
            if not site_location:
                st.error("Please enter a site location.")
            elif st.session_state.sow_analysis:
                with st.spinner("AI is identifying work type and searching for companies..."):
                    # Step 1: Identify work type (no change)
                    prompt = f"""
                    Based on the following SOW analysis, what type of service or company is needed to perform the work? Be specific and concise (e.g., 'Commercial HVAC Installation', 'Structural Engineering Services', 'Cybersecurity Compliance Auditing').

                    SOW ANALYSIS:
                    {st.session_state.sow_analysis}

                    COMPANY TYPE:
                    """
                    work_type = execute_ai_task(llm, prompt).strip()
                    st.write(f"**AI Identified Work Type:** {work_type}")

                    # Step 2: Perform live web search
                    search_query = f'"{work_type}" companies in {site_location}'
                    st.write(f"**Performing live web search for:** `{search_query}`")
                    
                    with DDGS() as ddgs:
                        results = [r for r in ddgs.text(search_query, max_results=5)]
                    
                    if not results:
                        st.warning("No search results found. Try a broader location or check the identified work type.")
                    else:
                        st.subheader("Top Search Results:")
                        for result in results:
                            st.markdown(f"**[{result['title']}]({result['href']})**")
                            st.write(result['body'])
                            st.divider()
            else:
                st.warning("Please run the 'SOW Analysis' on the first tab first.")

    # ... Tab 4 remains the same ...
    with tab4:
        st.subheader("Generate Proposal Table of Contents")
        st.write("This tool will create a proposal outline based directly on the government's evaluation criteria to ensure compliance.")
        if st.button("Generate Outline"):
            if st.session_state.sow_analysis:
                with st.spinner("AI is creating the proposal outline..."):
                    prompt = f"""
                    You are a proposal manager. Based ONLY on the "Evaluation Criteria" section from the SOW analysis below, create a formal Table of Contents for a proposal response. Each main criterion should be a main section.

                    SOW ANALYSIS (Evaluation Criteria section):
                    {st.session_state.sow_analysis}

                    TASK:
                    Generate a concise Table of Contents.
                    """
                    toc = execute_ai_task(llm, prompt)
                    st.markdown(toc)
            else:
                st.warning("Please run the 'SOW Analysis' on the first tab first.")
else:
    st.info("Upload a Statement of Work in the sidebar to begin the AI-powered bidding process.")


