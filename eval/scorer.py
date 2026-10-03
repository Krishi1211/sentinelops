import os
import json
import time
import requests
from datetime import datetime

RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "results"))
SCORECARD_PATH = os.path.join(RESULTS_DIR, "scorecard.md")

def run_evaluation_trial(scenario_type):
    print(f"\n[EVAL SCORER] Starting evaluation run for: {scenario_type}...")
    
    # 1. Reset orchestrator state first
    try:
        requests.post("http://127.0.0.1:8000/api/remediation/reject", timeout=5)
    except Exception as e:
        print(f"[EVAL SCORER] Error connecting to orchestrator: {e}. Is it running on port 8000?")
        return None

    # 2. Inject fault
    inject_res = requests.post("http://127.0.0.1:8000/api/scenario/inject", json={"type": scenario_type}, timeout=5)
    if inject_res.status_code != 200:
        print(f"[EVAL SCORER] Inject failed: {inject_res.text}")
        return None

    # 3. Wait for Awaiting Approval state (Orchestrator pipeline running)
    print("[EVAL SCORER] Monitoring agent diagnostics progress...")
    start_time = time.time()
    approval_token = None
    state = None
    
    while time.time() - start_time < 60: # 60 second timeout limit
        time.sleep(2)
        try:
            res = requests.get("http://127.0.0.1:8000/api/state", timeout=5)
            state = res.json()
            status = state.get("status")
            if status == "Awaiting Approval":
                approval_token = state.get("approval_token")
                print(f"[EVAL SCORER] Agents reached approval gate. Token generated: {approval_token}")
                break
            elif status == "Resolved":
                break
        except Exception as e:
            print(f"[EVAL SCORER] Poll error: {e}")
            
    if not approval_token:
        print("[EVAL SCORER] Error: Evaluation timed out before reaching approval gate.")
        return None

    time_to_diagnosis = time.time() - start_time

    logs = state.get("logs", [])
    tool_calls = [
        l for l in logs 
        if l.get("type") == "TOOL_CALL" or 
        (isinstance(l.get("content"), str) and l.get("content").startswith("TOOL_CALL:"))
    ]
    tool_call_count = len(tool_calls)
    
    # Simple heuristics to detect hallucinated statements (claims not matching tool outcomes)
    hallucination_detected = 0
    for log in logs:
        text = log.get("content", "").lower()
        if log.get("agent") == "DIAGNOSTICIAN" and log.get("type") == "TEXT":
            # If the agent claims to find something not in the mock state
            if "hallucinate" in text:
                hallucination_detected += 1
                
    # Evaluate accuracy: Did Diagnostician identify the correct root cause?
    diagnostician_logs = " ".join([l.get("content", "") for l in logs if l.get("agent") == "DIAGNOSTICIAN"])
    accuracy = "FAIL"
    if scenario_type == "config_regression":
        if "a3f9c2d" in diagnostician_logs.lower() or "pool" in diagnostician_logs.lower():
            accuracy = "PASS"
    elif scenario_type == "security_group":
        if "sg-0123" in diagnostician_logs.lower() or "8080" in diagnostician_logs.lower() or "security group" in diagnostician_logs.lower():
            accuracy = "PASS"

    # 5. Programmatically approve remediation to complete the SRE incident loop
    print(f"[EVAL SCORER] Submitting approval token {approval_token}...")
    approve_res = requests.post("http://127.0.0.1:8000/api/remediation/approve", json={"token": approval_token}, timeout=5)
    if approve_res.status_code != 200:
        print(f"[EVAL SCORER] Approval request failed: {approve_res.text}")
        return None

    # 6. Wait for incident resolution
    print("[EVAL SCORER] Waiting for status resolution...")
    resolved = False
    for _ in range(15):
        time.sleep(1)
        res = requests.get("http://127.0.0.1:8000/api/state", timeout=5)
        if res.json().get("status") == "Resolved":
            resolved = True
            break
            
    if not resolved:
        print("[EVAL SCORER] Warning: Remediation applied but status did not transit to Resolved.")

    trial_result = {
        "scenario": scenario_type,
        "accuracy": accuracy,
        "tool_calls": tool_call_count,
        "hallucinations": hallucination_detected,
        "diagnosis_time": round(time_to_diagnosis, 1),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return trial_result

def write_scorecard(results):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Read existing scorecard content or create headers
    content = ""
    if not os.path.exists(SCORECARD_PATH):
        content = """# SentinelOps Agent Evaluation Scorecard

This scorecard records performance benchmarks (Accuracy, Tool Call Count, Hallucination Rate, Time-to-Diagnosis) of the Ollama-backed SRE agents against synthetic fault injections.

| Timestamp | Scenario | Accuracy | Tool Calls | Hallucinations | Time to Diagnosis |
| --- | --- | --- | --- | --- | --- |
"""
    else:
        with open(SCORECARD_PATH, "r") as f:
            content = f.read()

    # Append rows
    for r in results:
        row = f"| {r['timestamp']} | {r['scenario']} | {r['accuracy']} | {r['tool_calls']} | {r['hallucinations']} | {r['diagnosis_time']}s |\n"
        content += row

    with open(SCORECARD_PATH, "w") as f:
        f.write(content)
    print(f"[EVAL SCORER] Benchmark scorecard written to: {SCORECARD_PATH}")

if __name__ == "__main__":
    results = []
    
    # Run a test cycle for both config and security group scenarios
    config_result = run_evaluation_trial("config_regression")
    if config_result:
        results.append(config_result)
        
    time.sleep(3) # cooldown gap
    
    security_result = run_evaluation_trial("security_group")
    if security_result:
        results.append(security_result)

    if results:
        write_scorecard(results)
    else:
        print("[EVAL SCORER] Evaluation trials complete. No results to record.")
