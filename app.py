# app.py

import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv
import logging
import time

load_dotenv()

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI base URL
FASTAPI_BASE_URL = os.getenv('FASTAPI_URL')

# Set up page configuration
st.set_page_config(layout="wide")


# Initialize session state variables
if 'token' not in st.session_state:
    st.session_state.token = None
if 'page' not in st.session_state:
    st.session_state.page = "login" 
if 'show_register' not in st.session_state:
    st.session_state.show_register = False

# Function to login a user
def login_user(username, password):
    url = f"{FASTAPI_BASE_URL}/token"  # Token endpoint for OAuth2
    retries = 5
    for attempt in range(retries):
        try:
            # Send data as form-encoded
            response = requests.post(url, data={"username": username, "password": password})
            if response.status_code == 200:
                logger.info("Login successful.")
                return response.json()
            elif response.status_code == 400:
                st.error("Invalid credentials. Please try again.")
                return {"error": "Invalid credentials"}
            elif response.status_code == 404:
                st.error("User does not exist. Please register first.")
                return {"error": "User not found"}
            else:
                st.error("Login failed. Please try again.")
                return {"error": "Unknown error"}
        except requests.exceptions.ConnectionError:
            st.warning("Unable to connect to FastAPI. Retrying...")
            logger.warning("Connection error during login. Retrying...")
            time.sleep(5)  # Wait for 5 seconds before retrying
    st.error("Could not connect to FastAPI after multiple attempts.")
    return {"error": "Connection failed"}

# Function to register a user
def register_user(username, password):
    url = f"{FASTAPI_BASE_URL}/register"
    try:
        response = requests.post(url, json={"username": username, "password": password})
        if response.status_code == 200:
            logger.info("Registration successful.")
            return response.json()
        elif response.status_code == 400:
            st.error("User already exists. Please choose a different username.")
            return {"error": "User already exists"}
        else:
            st.error("Registration failed. Please try again.")
            return {"error": "Unknown error"}
    except requests.exceptions.ConnectionError:
        st.error("Unable to connect to FastAPI. Please try again later.")
        logger.error("Connection error during registration.")
        return {"error": "Connection failed"}

# Function to access a protected endpoint (Optional: For demonstration)
def access_protected_endpoint(token):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{FASTAPI_BASE_URL}/protected-endpoint"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Unauthorized access"}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection failed"}

# Logout function to clear the session
def logout():
    if 'token' in st.session_state:
        del st.session_state['token']
    st.session_state.page = "login"  # Reset page to login after logout
    st.rerun()

# Validation function for input fields
def validate_input(username, password):
    if not username or not password:
        st.error("Username and Password are required.")
        return False
    return True

# Page navigation function
def go_to_page(page_name):
    st.session_state.page = page_name
    st.rerun()

# Function to display the login page
def show_login_page():
    st.title("Login")
    with st.form(key='login_form'):
        login_username = st.text_input("Username")
        login_password = st.text_input("Password", type='password')
        login_button = st.form_submit_button(label='Login')

        if login_button:
            # Validate input before making request
            if validate_input(login_username, login_password):
                result = login_user(login_username, login_password)
        
                if 'access_token' in result:
                    st.session_state['token'] = result['access_token']
                    st.success("Login successful!")
                    go_to_page("home")
                elif 'error' in result:
                    st.error(result['error'])

    # Display link to registration page
    st.markdown("---")
    st.write("Don't have an account? Register below:")
    with st.expander("Register"):
        show_register_form()

# Function to display the registration form
def show_register_form():
    with st.form(key='register_form'):
        register_username = st.text_input("Username", key='register_username')
        register_password = st.text_input("Password", type='password', key='register_password')
        register_button = st.form_submit_button(label='Register')

        if register_button:
            # Validate input before registration
            if validate_input(register_username, register_password):
                result = register_user(register_username, register_password)
                if 'id' in result or 'message' in result:
                    st.success("Registration successful! Please login.")
                    go_to_page("login")
                elif 'error' in result:
                    st.error(result['error'])

# Function to add a logout button in protected pages
def add_logout_button():
    st.sidebar.button("Logout", on_click=logout)

# Function to display the registration page (Alternative to expander)
def show_registration_page():
    st.title("Register")
    with st.form(key='register_form_page'):
        register_username = st.text_input("Username")
        register_password = st.text_input("Password", type='password')
        register_button = st.form_submit_button(label='Register')

        if register_button:
            # Validate input before registration
            if validate_input(register_username, register_password):
                result = register_user(register_username, register_password)
                if 'id' in result or 'message' in result:
                    st.success("Registration successful! Please login.")
                    go_to_page("login")
                elif 'error' in result:
                    st.error(result['error'])

    # Display link to login page
    st.markdown("---")
    st.write("Already have an account? Login below:")
    with st.expander("Login"):
        show_login_form()

# Function to display the login form inside the expander (if needed)
def show_login_form():
    with st.form(key='login_form_expander'):
        login_username = st.text_input("Username", key='login_username_expander')
        login_password = st.text_input("Password", type='password', key='login_password_expander')
        login_button = st.form_submit_button(label='Login')

        if login_button:
            # Validate input before making request
            if validate_input(login_username, login_password):
                result = login_user(login_username, login_password)
        
                if 'access_token' in result:
                    st.session_state['token'] = result['access_token']
                    st.success("Login successful!")
                    go_to_page("home")
                elif 'error' in result:
                    st.error(result['error'])

# Function to display the protected content (Document Library)
def show_home_page():
    st.title("Document Library")

    # Add Logout button in sidebar
    add_logout_button()

    # Fetch and display document list in a grid view
    documents = fetch_documents()
    if not documents:
        st.warning("No documents available.")
        return

    # Display documents in a grid with images and titles
    num_columns = 3  # Adjust the number of columns as needed
    cols = st.columns(num_columns)
    for idx, doc in enumerate(documents):
        doc_title = doc.get("TITLE", "No Title")
        doc_image = display_image(doc.get("IMAGELINK", ""))

        # Display image and title in grid
        with cols[idx % num_columns]:
            if doc_image:
                st.image(doc_image, use_column_width=True)
            else:
                st.write("No Image Available")
            st.write(doc_title)

            # Button to select document
            if st.button(f"Select", key=f"select_{doc['DOC_ID']}"):
                logger.info(f"Document selected: {doc_title} (ID: {doc['DOC_ID']})")
                st.session_state.selected_doc = doc
                st.session_state.page = "qna"
                st.session_state.embeddings_initialized = False
                st.session_state.summary = ''
                st.session_state['history'] = []
                st.rerun()

# Fetch document details from FastAPI and cache in session_state
def fetch_documents():
    if 'documents' not in st.session_state:
        try:
            logger.info("Fetching documents from FastAPI...")
            response = requests.get(f"{FASTAPI_BASE_URL}/list_documents_info")
            if response.status_code == 200:
                st.session_state.documents = response.json()
                logger.info(f"Fetched {len(st.session_state.documents)} documents.")
            else:
                st.error("Failed to fetch documents.")
                st.session_state.documents = []
        except Exception as e:
            st.error(f"Error fetching documents: {e}")
            logger.error(f"Error fetching documents: {e}")
            st.session_state.documents = []
    return st.session_state.documents

# Generate summary for a selected document
def generate_summary(document_id):
    try:
        logger.info(f"Generating summary for document ID: {document_id}")
        response = requests.post(
            f"{FASTAPI_BASE_URL}/generate_summary",
            json={"document_id": document_id}
        )
        if response.status_code == 200:
            summary = response.json().get("summary", "Summary generation failed")
            logger.info("Summary generation successful.")
            return summary
        else:
            st.warning("Error fetching summary.")
            logger.warning(f"Summary generation failed with status code {response.status_code}.")
            return "Summary generation failed."
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        logger.error(f"Error generating summary: {e}")
        return "Error generating summary."

# Send query for Q/A interaction
def ask_question(query, document_id):
    try:
        logger.info(f"Sending query to FastAPI: {query}")
        response = requests.post(
            f"{FASTAPI_BASE_URL}/query",
            json={"query": query, "document_id": document_id}
        )
        if response.status_code == 200:
            answer = response.json().get("response", "No response")
            logger.info("Received response from FastAPI.")
            return answer
        else:
            st.warning(f"Error: {response.json().get('detail', 'Unknown error')}")
            logger.warning(f"Query failed with status code {response.status_code}.")
            return "Error with question."
    except Exception as e:
        st.error(f"Error asking question: {e}")
        logger.error(f"Error asking question: {e}")
        return "Error with question."

# Send session history to save in S3
def save_session_history(document_id, session_history):
    try:
        logger.info(f"Saving session history for document ID: {document_id}")
        response = requests.post(
            f"{FASTAPI_BASE_URL}/save_session_history",
            json={
                "document_id": document_id,
                "session_history": session_history
            }
        )
        if response.status_code == 200:
            logger.info("Session history saved successfully.")
            return True
        else:
            st.warning("Failed to save session history.")
            logger.warning(f"Failed to save session history with status code {response.status_code}.")
            return False
    except Exception as e:
        st.error(f"Error saving session history: {e}")
        logger.error(f"Error saving session history: {e}")
        return False

# # Initialize embeddings for the selected document
# def initialize_embeddings(document_id):
#     try:
#         logger.info(f"Initializing embeddings for document ID: {document_id}")
#         response = requests.post(
#             f"{FASTAPI_BASE_URL}/initialize_embeddings",
#             json={"document_id": document_id}
#         )
#         if response.status_code == 200:
#             logger.info("Embeddings initialized successfully.")
#             return True
#         else:
#             st.warning("Failed to initialize embeddings.")
#             logger.warning(f"Embeddings initialization failed with status code {response.status_code}.")
#             return False
#     except Exception as e:
#         st.error(f"Error initializing embeddings: {e}")
#         logger.error(f"Error initializing embeddings: {e}")
#         return False

# Constants
DEFAULT_IMAGE_URL = os.getenv('DEFAULT_IMAGE_URL')

# Display an image from a URL with a fallback to a default image
def display_image(url):
    try:
        # Attempt to fetch the image from the provided URL
        logger.info(f"Fetching image from URL: {url}")
        image_response = requests.get(url, timeout=5)
        if image_response.status_code == 200:
            logger.info("Image fetched successfully.")
            return Image.open(BytesIO(image_response.content))
        else:
            logger.warning(f"Image not available at {url}. Fetching default image.")
            # Attempt to fetch the default image
            default_response = requests.get(DEFAULT_IMAGE_URL, timeout=5)
            if default_response.status_code == 200:
                logger.info("Default image fetched successfully.")
                return Image.open(BytesIO(default_response.content))
            else:
                st.error("Default image not available.")
                logger.error(f"Default image not available at {DEFAULT_IMAGE_URL}.")
                return None
    except requests.exceptions.RequestException as e:
        st.warning(f"Error loading image: {e}. Loading default image.")
        logger.warning(f"Error loading image from {url}: {e}. Attempting to load default image.")
        try:
            # Attempt to fetch the default image in case of an exception
            default_response = requests.get(DEFAULT_IMAGE_URL, timeout=5)
            if default_response.status_code == 200:
                logger.info("Default image fetched successfully.")
                return Image.open(BytesIO(default_response.content))
            else:
                st.error("Default image not available.")
                logger.error(f"Default image not available at {DEFAULT_IMAGE_URL}.")
                return None
        except requests.exceptions.RequestException as default_e:
            st.error(f"Error loading default image: {default_e}")
            logger.error(f"Error loading default image: {default_e}")
            return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        logger.error(f"Unexpected error loading image: {e}")
        return None

# # Main function to run Streamlit app
# def main():
#     # Initialize session state
#     if 'page' not in st.session_state:
#         st.session_state.page = "home"
#     if 'selected_doc' not in st.session_state:
#         st.session_state.selected_doc = None
#     if 'embeddings_initialized' not in st.session_state:
#         st.session_state.embeddings_initialized = False
#     if 'summary' not in st.session_state:
#         st.session_state.summary = ''
#     if 'history' not in st.session_state:
#         st.session_state['history'] = []
#     if 'user_input' not in st.session_state:
#         st.session_state['user_input'] = ''

#     if st.session_state.page == "home":
#         show_home_page()
#     elif st.session_state.page == "qna":
#         show_qna_page()

# # Function to format session history as research notes
# def format_session_history_as_research_note(history: list) -> str:
#     """
#     Formats the session history into a single research note.
#     """
#     research_note = "## Research Notes\n\n"
#     for message in history:
#         if message["role"] == "user":
#             research_note += f"**User:** {message['content']}\n\n"
#         elif message["role"] == "assistant":
#             research_note += f"**Assistant:** {message['content']}\n\n"
#     return research_note

# Function to save the entire research note
def save_entire_research_note_api(document_id: str, research_note: str) -> bool:
    """
    Calls the FastAPI /save_entire_research_note endpoint to save the entire Q&A session as a research note.
    """
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/save_entire_research_note",
            json={"document_id": document_id, "research_note": research_note}
        )
        if response.status_code == 200:
            return True
        else:
            st.warning(f"Error saving research note: {response.json().get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error saving research note: {e}")
        return False

# Send research note as entire page
def save_entire_research_note(document_id, research_note):
    try:
        logger.info(f"Saving entire research note for document ID: {document_id}")
        response = requests.post(
            f"{FASTAPI_BASE_URL}/save_entire_research_note",
            json={"document_id": document_id, "research_note": research_note}
        )
        if response.status_code == 200:
            st.success("Entire Q&A session saved as a research note successfully.")
            logger.info("Entire Q&A session saved successfully.")
            return True
        else:
            st.warning(f"Failed to save research note: {response.json().get('detail', 'Unknown error')}")
            logger.warning(f"Failed to save research note with status code {response.status_code}.")
            return False
    except Exception as e:
        st.error(f"Error saving research note: {e}")
        logger.error(f"Error saving research note: {e}")
        return False

def show_home_page():
    st.title("Document Library")

    # Fetch and display document list in a grid view
    documents = fetch_documents()
    if not documents:
        st.warning("No documents available.")
        return

    # Display documents in a grid with images and titles
    num_columns = 3  # Adjust the number of columns as needed
    cols = st.columns(num_columns)
    for idx, doc in enumerate(documents):
        doc_title = doc.get("TITLE", "No Title")
        doc_image = display_image(doc.get("IMAGELINK", ""))

        # Display image and title in grid
        with cols[idx % num_columns]:
            if doc_image:
                st.image(doc_image, use_column_width=True)
            else:
                st.write("No Image Available")
            st.write(doc_title)

            # Button to select document
            if st.button(f"Select", key=f"select_{doc['DOC_ID']}"):
                logger.info(f"Document selected: {doc_title} (ID: {doc['DOC_ID']})")
                st.session_state.selected_doc = doc
                st.session_state.page = "qna"
                st.session_state.embeddings_initialized = False
                st.session_state.summary = ''
                st.session_state['history'] = []
                st.rerun()

def generate_report_api(query, document_id):
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/generate_report",
            json={"query": query, "document_id": document_id}
        )
        if response.status_code == 200:
            report = response.json().get("report", "No report generated.")
            return report
        else:
            st.warning(f"Error generating report: {response.json().get('detail', 'Unknown error')}")
            return "Error generating report."
    except Exception as e:
        st.error(f"Error generating report: {e}")
        return "Error generating report."

def save_research_note_api(document_id, research_note):
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/save_research_note",
            json={"document_id": document_id, "research_note": research_note}
        )
        if response.status_code == 200:
            return True
        else:
            st.warning(f"Error saving research note: {response.json().get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error saving research note: {e}")
        return False

# def fetch_research_notes_api(document_id):
#     try:
#         response = requests.get(
#             f"{FASTAPI_BASE_URL}/get_research_notes",
#             params={"document_id": document_id}
#         )
#         if response.status_code == 200:
#             notes = response.json().get("research_notes", [])
#             return notes
#         else:
#             st.warning(f"Error fetching research notes: {response.json().get('detail', 'Unknown error')}")
#             return []
#     except Exception as e:
#         st.error(f"Error fetching research notes: {e}")
#         return []

# Function to display the Q&A page
def show_qna_page():
    st.title("Q/A Session")

    # Add Logout button in sidebar
    add_logout_button()

    # Display selected document details in sidebar
    selected_doc = st.session_state.selected_doc
    if not selected_doc:
        st.session_state.page = "home"
        st.rerun()
        return

    with st.sidebar:
        st.subheader("Document Summary")
        st.write(f"**Title:** {selected_doc.get('TITLE', 'No Title')}")

        # Button to regenerate summary
        if st.button("Regenerate Summary"):
            logger.info("Regenerate Summary button clicked.")
            st.session_state.summary = ''  # Clear existing summary to trigger regeneration

        # Generate summary
        if not st.session_state.summary:
            with st.spinner('Generating summary...'):
                logger.info("Generating summary...")
                summary = generate_summary(selected_doc["DOC_ID"], st.session_state.token)
                st.session_state.summary = summary
                logger.info("Summary generation completed.")
        else:
            summary = st.session_state.summary

        st.write("**Summary:**")
        st.write(summary)

        # Display PDF link
        pdf_link = selected_doc.get("PDFLINK", "#")
        if pdf_link != "#":
            st.write(f"[View Full Document PDF]({pdf_link})")
        else:
            st.write("PDF link not available.")

    # Initialize embeddings
    if not st.session_state.embeddings_initialized:
        with st.spinner('Initializing embeddings...'):
            logger.info("Initializing embeddings...")
            if initialize_embeddings(selected_doc["DOC_ID"], st.session_state.token):
                st.session_state.embeddings_initialized = True
                logger.info("Embeddings initialized successfully.")
            else:
                st.error("Failed to initialize embeddings for the document.")
                logger.error("Embeddings initialization failed.")
                st.stop()

    # Q/A interaction interface
    st.header("Ask Questions about the Document")

    # Display chat history
    if st.session_state.get('history'):
        for idx, message in enumerate(st.session_state['history']):
            if message["role"] == "user":
                st.markdown(f"**User:** {message['content']}")
            elif message["role"] == "assistant":
                if message.get("is_report"):
                    st.markdown(f"**Generated Report:**\n{message['content']}")
                else:
                    st.markdown(f"**Assistant:** {message['content']}")
                # Display satisfaction status if available
                if "satisfied" in message:
                    satisfaction = "Yes" if message["satisfied"] else "No"
                    st.markdown(f"**User Satisfaction:** {satisfaction}")

    # Use a form to handle user input and submission
    with st.form("qna_form", clear_on_submit=True):
        user_input = st.text_input("Enter your question:", key='user_input')
        # generate_report = st.checkbox("Generate detailed report", value=False)
        submit_button = st.form_submit_button("Submit")

        if submit_button and user_input:
            logger.info(f"User submitted question: {user_input}")
            st.session_state['history'].append({"role": "user", "content": user_input})
            if False:
                # Call the report generation endpoint
                with st.spinner('Generating report...'):
                    report = generate_report_api(user_input, selected_doc["DOC_ID"], st.session_state.token)
                    logger.info(f"Report generated: {report[:100]}...")  # Log first 100 chars
                st.session_state['history'].append({"role": "assistant", "content": report, "is_report": True})
            else:
                # Regular Q/A
                with st.spinner('Fetching response...'):
                    response = ask_question(user_input, selected_doc["DOC_ID"], st.session_state.token)
                    logger.info(f"Assistant response: {response[:100]}...")
                st.session_state['history'].append({"role": "assistant", "content": response})
                st.rerun()

    # After appending assistant response, prompt for satisfaction
    if st.session_state.get('history'):
        last_message = st.session_state['history'][-1]
        if last_message["role"] == "assistant" and "satisfied" not in last_message:
            with st.form("satisfaction_form", clear_on_submit=True):
                satisfaction = st.radio("Are you satisfied with the answer?", ("Yes", "No"), key="satisfaction_radio")
                submit_satisfaction = st.form_submit_button("Submit Satisfaction")

                if submit_satisfaction:
                    # Update the last assistant message with satisfaction status
                    st.session_state['history'][-1]["satisfied"] = True if satisfaction == "Yes" else False
                    logger.info(f"User satisfaction: {'Yes' if satisfaction == 'Yes' else 'No'}")
                    st.rerun()  # Refresh to display the satisfaction status

    # Clear chat history
    if st.button("Clear Chat"):
        logger.info("Clear Chat button clicked. Clearing session history.")
        st.session_state['history'] = []

    # Back button to return to home page
    if st.button("Back to Document Library"):
        logger.info("Back to Document Library button clicked. Saving session history.")
        # Save session history to S3
        if save_session_history(st.session_state.selected_doc["DOC_ID"], st.session_state['history'], st.session_state.token):
            st.success("Session history saved.")
            logger.info("Session history saved successfully.")
        else:
            st.error("Failed to save session history.")
            logger.error("Failed to save session history.")

        # Reset session state
        st.session_state.page = "home"
        st.session_state.selected_doc = None
        st.session_state.embeddings_initialized = False
        st.session_state.summary = ''
        st.session_state['history'] = []
        st.rerun()

    # **Add the Global Save Button Here**
    st.markdown("---")  # Separator

    with st.expander("Save Entire Q&A as Research Note"):
        if st.button("Save Q&A as Research Note"):
            if not st.session_state['history']:
                st.warning("No Q&A history to save.")
            else:
                # Format the session history into a single research note
                formatted_research_note = format_session_history_as_research_note(st.session_state['history'])
                # Call the backend API to save the research note
                success = save_entire_research_note_api(st.session_state.selected_doc["DOC_ID"], formatted_research_note, st.session_state.token)
                if success:
                    st.success("Entire Q&A session saved as a research note successfully.")
                else:
                    st.error("Failed to save the Q&A session as a research note.")

    # **Add the "View Saved Research Notes" Button Here**
    st.markdown("---")  # Separator

    with st.expander("View Saved Research Notes"):
        if st.button("View Saved Research Notes"):
            with st.spinner('Fetching saved research notes...'):
                research_notes = fetch_research_notes_api(st.session_state.selected_doc["DOC_ID"], st.session_state.token)
            if research_notes:
                st.write("## Saved Research Notes")
                for idx, note in enumerate(research_notes, 1):
                    st.markdown(f"### Research Note {idx}")
                    st.markdown(note)
            else:
                st.write("No research notes saved for this document.")

# Function to display an image from a URL with a fallback to a default image
def display_image(url):
    try:
        # Attempt to fetch the image from the provided URL
        logger.info(f"Fetching image from URL: {url}")
        image_response = requests.get(url, timeout=5)
        if image_response.status_code == 200:
            logger.info("Image fetched successfully.")
            return Image.open(BytesIO(image_response.content))
        else:
            logger.warning(f"Image not available at {url}. Fetching default image.")
            # Attempt to fetch the default image
            default_response = requests.get(DEFAULT_IMAGE_URL, timeout=5)
            if default_response.status_code == 200:
                logger.info("Default image fetched successfully.")
                return Image.open(BytesIO(default_response.content))
            else:
                st.error("Default image not available.")
                logger.error(f"Default image not available at {DEFAULT_IMAGE_URL}.")
                return None
    except requests.exceptions.RequestException as e:
        st.warning(f"Error loading image: {e}. Loading default image.")
        logger.warning(f"Error loading image from {url}: {e}. Attempting to load default image.")
        try:
            # Attempt to fetch the default image in case of an exception
            default_response = requests.get(DEFAULT_IMAGE_URL, timeout=5)
            if default_response.status_code == 200:
                logger.info("Default image fetched successfully.")
                return Image.open(BytesIO(default_response.content))
            else:
                st.error("Default image not available.")
                logger.error(f"Default image not available at {DEFAULT_IMAGE_URL}.")
                return None
        except requests.exceptions.RequestException as default_e:
            st.error(f"Error loading default image: {default_e}")
            logger.error(f"Error loading default image: {default_e}")
            return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        logger.error(f"Unexpected error loading image: {e}")
        return None

def fetch_documents():
    if 'documents' not in st.session_state:
        try:
            logger.info("Fetching documents from FastAPI...")
            headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}
            response = requests.get(f"{FASTAPI_BASE_URL}/list_documents_info", headers=headers)
            if response.status_code == 200:
                st.session_state.documents = response.json()
                logger.info(f"Fetched {len(st.session_state.documents)} documents.")
            else:
                st.error("Failed to fetch documents.")
                st.session_state.documents = []
        except Exception as e:
            st.error(f"Error fetching documents: {e}")
            logger.error(f"Error fetching documents: {e}")
            st.session_state.documents = []
    return st.session_state.documents

def generate_summary(document_id, token):
    try:
        logger.info(f"Generating summary for document ID: {document_id}")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.post(
            f"{FASTAPI_BASE_URL}/generate_summary",
            json={"document_id": document_id},
            headers=headers
        )
        if response.status_code == 200:
            summary = response.json().get("summary", "Summary generation failed")
            logger.info("Summary generation successful.")
            return summary
        else:
            st.warning("Error fetching summary.")
            logger.warning(f"Summary generation failed with status code {response.status_code}.")
            return "Summary generation failed."
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        logger.error(f"Error generating summary: {e}")
        return "Error generating summary."

def ask_question(query, document_id, token):
    try:
        logger.info(f"Sending query to FastAPI: {query}")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.post(
            f"{FASTAPI_BASE_URL}/query",
            json={"query": query, "document_id": document_id},
            headers=headers
        )
        if response.status_code == 200:
            answer = response.json().get("response", "No response")
            logger.info("Received response from FastAPI.")
            return answer
        else:
            st.warning(f"Error: {response.json().get('detail', 'Unknown error')}")
            logger.warning(f"Query failed with status code {response.status_code}.")
            return "Error with question."
    except Exception as e:
        st.error(f"Error asking question: {e}")
        logger.error(f"Error asking question: {e}")
        return "Error with question."

def save_session_history(document_id, session_history, token):
    try:
        logger.info(f"Saving session history for document ID: {document_id}")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.post(
            f"{FASTAPI_BASE_URL}/save_session_history",
            json={
                "document_id": document_id,
                "session_history": session_history
            },
            headers=headers
        )
        if response.status_code == 200:
            logger.info("Session history saved successfully.")
            return True
        else:
            st.warning("Failed to save session history.")
            logger.warning(f"Failed to save session history with status code {response.status_code}.")
            return False
    except Exception as e:
        st.error(f"Error saving session history: {e}")
        logger.error(f"Error saving session history: {e}")
        return False

def initialize_embeddings(document_id, token):
    try:
        logger.info(f"Initializing embeddings for document ID: {document_id}")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.post(
            f"{FASTAPI_BASE_URL}/initialize_embeddings",
            json={"document_id": document_id},
            headers=headers
        )
        if response.status_code == 200:
            logger.info("Embeddings initialized successfully.")
            return True
        else:
            st.warning("Failed to initialize embeddings.")
            logger.warning(f"Embeddings initialization failed with status code {response.status_code}.")
            return False
    except Exception as e:
        st.error(f"Error initializing embeddings: {e}")
        logger.error(f"Error initializing embeddings: {e}")
        return False

def format_session_history_as_research_note(history: list) -> str:
    """
    Formats the session history into a single research note.
    """
    research_note = "## Research Notes\n\n"
    for message in history:
        if message["role"] == "user":
            research_note += f"**User:** {message['content']}\n\n"
        elif message["role"] == "assistant":
            research_note += f"**Assistant:** {message['content']}\n\n"
    return research_note

def save_entire_research_note_api(document_id: str, research_note: str, token) -> bool:
    """
    Calls the FastAPI /save_entire_research_note endpoint to save the entire Q&A session as a research note.
    """
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.post(
            f"{FASTAPI_BASE_URL}/save_entire_research_note",
            json={"document_id": document_id, "research_note": research_note},
            headers=headers
        )
        if response.status_code == 200:
            return True
        else:
            st.warning(f"Error saving research note: {response.json().get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error saving research note: {e}")
        return False

def fetch_research_notes_api(document_id: str, token):
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.get(
            f"{FASTAPI_BASE_URL}/get_research_notes",
            params={"document_id": document_id},
            headers=headers
        )
        if response.status_code == 200:
            notes = response.json().get("research_notes", [])
            return notes
        else:
            st.warning(f"Error fetching research notes: {response.json().get('detail', 'Unknown error')}")
            return []
    except Exception as e:
        st.error(f"Error fetching research notes: {e}")
        return []

# Main function to run Streamlit app
def main():
    if st.session_state.page == "login":
        show_login_page()
    elif st.session_state.page == "register":
        show_registration_page()
    elif st.session_state.page == "home" and st.session_state.token:
        show_home_page()
    elif st.session_state.page == "qna" and st.session_state.token:
        show_qna_page()
    else:
        st.error("Invalid page or authentication state.")
        logout()

if __name__ == "__main__":
    main()
