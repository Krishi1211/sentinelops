import json
from agents.agent_helper import run_agent_turn

DIAGNOSTICIAN_SYSTEM_PROMPT = """You are the Diagnostician Agent for SentinelOps.
Your role is to investigate anomalous metrics reported by the Detector Agent and identify the root cause.

You must:
1. Evaluate multiple hypotheses sequentially. Do not jump to conclusions without checking.
2. Hypothesis 1: Git Configuration/Code Regression.
   - Call `get_recent_commits` to view recent code changes.
   - For any suspicious commits, check details using `get_commit_diff`.
3. Hypothesis 2: Network / Security Group modifications.
   - Call `get_recent_security_group_changes` to see if ingress or egress access was modified.
4. For the scenario under test, you will notice one of these is the root cause while the other is healthy. You MUST explicitly state what you checked and why you RULED OUT a wrong hypothesis before confirming the true root cause.
5. Provide a summary of:
   - Root Cause identified.
   - Evidence gathered (including SHAs, filenames, specific values, or CloudTrail event IDs).
   - Recommended remediation action.
"""

def run_diagnostician(anomaly_report, log_callback, model="llama3.2"):
    log_callback("DIAGNOSTICIAN", "Diagnostician Agent initialized. Investigating anomaly...")
    
    messages = [
        {"role": "system", "content": DIAGNOSTICIAN_SYSTEM_PROMPT},
        {"role": "user", "content": f"Investigate this anomaly report and identify the root cause:\n{anomaly_report}"}
    ]
    
    allowed_tools = ["get_recent_commits", "get_commit_diff", "get_recent_security_group_changes"]
    
    try:
        response = run_agent_turn(model, messages, allowed_tools, lambda type, msg: log_callback("DIAGNOSTICIAN", f"{type}: {msg}" if isinstance(msg, str) else f"{type}: {json.dumps(msg)}"))
        return response
    except Exception as e:
        log_callback("SYSTEM", f"Diagnostician Agent failed: {str(e)}")
        return f"Error running diagnostician: {str(e)}"
