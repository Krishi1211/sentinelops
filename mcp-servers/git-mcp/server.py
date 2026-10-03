import os
import json
import subprocess
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Git Operations")

SIM_STATE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../agents/sim_state.json")
)

def get_sim_state():
    if os.path.exists(SIM_STATE_PATH):
        try:
            with open(SIM_STATE_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"active_fault": None}

def is_real_mode():
    return os.getenv("MODE") == "real"

@mcp.tool()
def get_recent_commits(since_minutes: int = 60) -> str:
    """Fetches list of recent commits in the project repository since the specified number of minutes."""
    try:
        since_minutes = int(since_minutes)
    except (ValueError, TypeError):
        since_minutes = 60

    if not is_real_mode():
        state = get_sim_state()
        active_fault = state.get("active_fault")
        
        # Base commits
        commits = [
            {
                "sha": "9a8b7c6",
                "author": "sre-lead",
                "date": (datetime.now() - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S"),
                "message": "fix: resolve memory leak in health check route"
            }
        ]
        
        if active_fault == "config_regression":
            # Config deployment regression commit
            commits.insert(0, {
                "sha": "a3f9c2d",
                "author": "ci-deployer-bot",
                "date": (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
                "message": "deploy: update connection_pool_timeout_ms setting to 50000ms"
            })
        elif active_fault == "security_group":
            # Normal deployment commit (not a config regression)
            commits.insert(0, {
                "sha": "b5e8d3f",
                "author": "web-dev",
                "date": (datetime.now() - timedelta(minutes=8)).strftime("%Y-%m-%d %H:%M:%S"),
                "message": "docs: update API documentation endpoints readme"
            })
            
        return json.dumps(commits, indent=2)

    try:
        # Run git command against root repo
        repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        since_time = (datetime.now() - timedelta(minutes=since_minutes)).strftime("%Y-%m-%d %H:%M:%S")
        
        result = subprocess.run(
            ["git", "log", f"--since={since_time}", "--pretty=format:%H|%an|%ad|%s", "--date=format:%Y-%m-%d %H:%M:%S"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True
        )
        
        commits = []
        if result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                parts = line.split("|")
                if len(parts) >= 4:
                    commits.append({
                        "sha": parts[0][:7],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    })
        return json.dumps(commits, indent=2)
    except Exception as e:
        return f"Error executing git command: {str(e)}"

@mcp.tool()
def get_commit_diff(sha: str) -> str:
    """Returns the code changes / diff for a given commit SHA hash."""
    if not is_real_mode():
        if sha == "a3f9c2d":
            return """diff --git a/config.json b/config.json
index 8fd7e22..cf33a1e 100644
--- a/config.json
+++ b/config.json
@@ -4,5 +4,5 @@
   "db_host": "db.production.internal",
   "db_port": 5432,
-  "connection_pool_timeout_ms": 1000,
+  "connection_pool_timeout_ms": 50000,
   "max_connections": 20
 }"""
        elif sha == "b5e8d3f":
            return """diff --git a/README.md b/README.md
index ad22fa2..331abfe 100644
--- a/README.md
+++ b/README.md
@@ -10,3 +10,4 @@
-GET /api/v1/health - Check health status
+GET /api/v1/health - Check service status
+GET /api/v1/data - Read user target endpoints
 """
        return "Commit not found or diff empty."

    try:
        repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        result = subprocess.run(
            ["git", "show", sha],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except Exception as e:
        return f"Error fetching git diff: {str(e)}"

if __name__ == "__main__":
    mcp.run()
