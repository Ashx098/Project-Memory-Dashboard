import streamlit as st
import requests
import pandas as pd
import time

# Set FastAPI URL
FASTAPI_URL = "https://project-memory-dashboard.onrender.com"  # REMOVE PORT 10000


# Page Configuration
st.set_page_config(page_title="Project Memory Dashboard", layout="wide")

# Dark Mode Toggle
dark_mode = st.sidebar.toggle("🌙 Dark Mode", value=False)

# Define Theme Colors
if dark_mode:
    theme = {
        "bg_color": "#121212",    # True Dark Mode
        "text_color": "#FFFFFF",   # White Text for Contrast
        "table_bg": "#1E1E1E",     # Dark Gray Table
        "highlight": "#FF5733",    # Orange Highlight for Visibility
    }
else:
    theme = {
        "bg_color": "#F9F9F9",     # Lighter Background
        "text_color": "#222222",   # Dark Gray Text for Readability
        "table_bg": "#FFFFFF",     # White Table Background
        "highlight": "#007BFF",    # Blue Highlight
    }


# Apply Streamlit's Native Theme Styling
st.markdown(
    f"""
    <style>
        body, .stApp {{
            background-color: {theme['bg_color']};
            color: {theme['text_color']};
        }}
        .big-font {{
            font-size: 28px !important;
            font-weight: bold;
            color: {theme['highlight']};
        }}
        .section-title {{
            font-size: 20px !important;
            font-weight: bold;
            color: {theme['text_color']};
            padding-top: 15px;
            border-bottom: 3px solid {theme['highlight']};
            padding-bottom: 5px;
        }}
        .stDataFrame {{
            background-color: {theme['table_bg']};
            border-radius: 10px;
            padding: 10px;
            color: {theme['text_color']};
            animation: fadeIn 0.5s ease-in-out;
        }}
        .error-text {{
            color: {theme['highlight']} !important;
            font-weight: bold;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Dashboard Title
st.title("📌 Project Memory Dashboard")
st.write("This dashboard visualizes projects, execution logs, and Git commits.")

# Sidebar - Select Project
st.sidebar.header("📁 Select a Project")
projects = requests.get(f"{FASTAPI_URL}/projects").json().get("projects", [])

if projects:
    project_options = {p[1]: p[0] for p in projects}
    selected_project = st.sidebar.selectbox("Choose a Project", list(project_options.keys()))
    project_id = project_options[selected_project]

    # Display Project Name
    st.markdown(f"<p class='big-font'>📌 Project: {selected_project}</p>", unsafe_allow_html=True)

    # Fetch Execution Logs
    execution_logs = requests.get(f"{FASTAPI_URL}/execution_logs/{project_id}").json().get("execution_logs", [])
    if execution_logs:
        st.markdown("<p class='section-title'>⚙️ Execution Logs</p>", unsafe_allow_html=True)
        df_exec = pd.DataFrame(execution_logs, columns=["ID", "Project ID", "Step ID", "Command", "Output", "Timestamp"])
        st.dataframe(df_exec.drop(columns=["Project ID", "Step ID"]), use_container_width=True)
    else:
        st.info("No execution logs found.")

    # Fetch Git Commits
    commits = requests.get(f"{FASTAPI_URL}/code_versions/{project_id}").json().get("code_versions", [])
    if commits:
        st.markdown("<p class='section-title'>📝 Git Commit History</p>", unsafe_allow_html=True)
        df_commits = pd.DataFrame(commits, columns=["ID", "Project ID", "File Name", "Version", "Commit Hash", "Timestamp"])
        st.dataframe(df_commits.drop(columns=["Project ID"]), use_container_width=True)
    else:
        st.info("No Git commits found.")

    # Fetch Error Logs
    errors = requests.get(f"{FASTAPI_URL}/errors/{project_id}").json().get("error_logs", [])
    if errors:
        st.markdown("<p class='section-title'>🚨 Error Logs</p>", unsafe_allow_html=True)
        df_errors = pd.DataFrame(errors, columns=["ID", "Project ID", "Step ID", "Error Message", "Fix Suggestion", "Timestamp"])
        df_errors.drop(columns=["Project ID", "Step ID"], inplace=True)
        st.dataframe(df_errors.style.map(lambda x: "color: red;" if isinstance(x, str) else ""), use_container_width=True)
    else:
        st.info("No errors found.")

else:
    st.warning("No projects found. Add a project first.")

# 🛠️ Run Commands Directly from UI
st.sidebar.markdown("### ⚡ Run Command")

command_input = st.sidebar.text_input("Enter command:")
run_command = st.sidebar.button("Run Command")

# Auto-refresh Handling
if "refresh" not in st.session_state:
    st.session_state.refresh = False

if run_command and command_input.strip():
    try:
        response = requests.post(
            f"{FASTAPI_URL}/log_execution/{project_id}/1",
            params={"command": command_input},
        ).json()
        st.sidebar.success(f"✅ Command Executed: {command_input}")
        st.sidebar.text_area("🔹 Output:", response.get("output", "No Output"))

        # 🔄 Auto-refresh dashboard after execution
        st.session_state.refresh = True

    except Exception as e:
        st.sidebar.error(f"⚠️ Error running command: {str(e)}")

if st.session_state.refresh:
    st.session_state.refresh = False
    st.rerun()


FASTAPI_URL = "https://project-memory-dashboard.onrender.com"

# Retry mechanism for waking up FastAPI
def fetch_with_retry(url, retries=5, delay=5):
    for i in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Retry {i+1}/{retries} failed: {e}")
        time.sleep(delay)
    return None  # Return None if all retries fail

# Fetch projects with retry
projects = fetch_with_retry(f"{FASTAPI_URL}/projects")

if projects:
    print("✅ Successfully fetched projects:", projects)
else:
    print("❌ Failed to fetch projects after retries!")

import threading
import requests
import time

FASTAPI_URL = "https://project-memory-dashboard.onrender.com"

# Function to keep API alive
def keep_api_awake():
    while True:
        try:
            requests.get(f"{FASTAPI_URL}/health", timeout=5)  # Send a request to keep API awake
        except requests.exceptions.RequestException:
            pass  # Ignore failures
        time.sleep(300)  # Run every 5 minutes

# Start background thread
threading.Thread(target=keep_api_awake, daemon=True).start()
