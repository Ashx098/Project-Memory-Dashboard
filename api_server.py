import subprocess
import sqlite3
import os
from fastapi import FastAPI

app = FastAPI()

# Dynamically determine the database path
DB_NAME = "project_memory.db"
DB_PATH = os.path.join(os.getcwd(), DB_NAME)

def connect_db():
    """Connects to SQLite and returns a connection."""
    print(f"DEBUG: Connecting to SQLite at {DB_PATH}")  # Debugging Log
    return sqlite3.connect(DB_PATH)

def get_latest_commit():
    """Gets the latest Git commit hash."""
    try:
        commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        return commit_hash
    except subprocess.CalledProcessError:
        return None

@app.get("/")
def read_root():
    return {"message": "Project Memory API is running!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/projects")
def get_projects():
    """Fetches all projects from the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects;")
    projects = cursor.fetchall()
    conn.close()
    return {"projects": projects}

@app.get("/steps/{project_id}")
def get_steps(project_id: int):
    """Fetches all steps for a specific project."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM steps WHERE project_id = ?;", (project_id,))
    steps = cursor.fetchall()
    conn.close()
    return {"steps": steps}

@app.get("/execution_logs/{project_id}")
def get_execution_logs(project_id: int):
    """Fetches execution logs for a specific project."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM execution_logs WHERE project_id = ?;", (project_id,))
    logs = cursor.fetchall()
    conn.close()
    return {"execution_logs": logs}

@app.get("/errors/{project_id}")
def get_errors(project_id: int):
    """Fetches error logs for a specific project."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM error_logs WHERE project_id = ?;", (project_id,))
    errors = cursor.fetchall()
    conn.close()
    return {"error_logs": errors}

@app.get("/code_versions/{project_id}")
def get_code_versions(project_id: int):
    """Fetches stored Git commit hashes for code tracking."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM code_versions WHERE project_id = ?;", (project_id,))
    versions = cursor.fetchall()
    conn.close()
    return {"code_versions": versions}

@app.post("/log_commit/{project_id}")
def log_commit(project_id: int, file_name: str, version: int):
    """Logs the latest Git commit hash into SQLite."""
    commit_hash = get_latest_commit()
    
    print(f"DEBUG: Retrieved commit hash: {commit_hash}")  # Debugging Log

    if commit_hash:
        conn = connect_db()
        cursor = conn.cursor()
        
        print(f"DEBUG: Inserting into DB - Project: {project_id}, File: {file_name}, Commit: {commit_hash}")  # Debugging Log

        cursor.execute(
            "INSERT INTO code_versions (project_id, file_name, version, commit_hash) VALUES (?, ?, ?, ?)",
            (project_id, file_name, version, commit_hash),
        )
        conn.commit()
        conn.close()
        return {"message": f"Logged commit {commit_hash} for {file_name}"}
    else:
        print("DEBUG: Git commit retrieval failed!")  # Debugging Log
        return {"error": "Failed to get commit hash. Ensure Git is initialized."}

@app.post("/log_execution/{project_id}/{step_id}")
def log_execution(project_id: int, step_id: int, command: str):
    """Executes a system command and logs its output in SQLite."""
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True).strip()
    except subprocess.CalledProcessError as e:
        output = f"ERROR: {e.output}"

    print(f"DEBUG: Executing command: {command}")  # Debugging Log
    print(f"DEBUG: Output: {output}")  # Debugging Log

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO execution_logs (project_id, step_id, command, output) VALUES (?, ?, ?, ?)",
        (project_id, step_id, command, output),
    )
    conn.commit()
    conn.close()
    
    return {"message": f"Logged execution of '{command}'", "output": output}
