import json
from agents.agent_helper import run_agent_turn

DETECTOR_SYSTEM_PROMPT = """You are the Detector Agent for SentinelOps.
Your role is to monitor AWS infrastructure telemetry and flag active anomalies.

You must:
1. Retrieve the list of active running instances using the tool `list_running_instances`.
2. Inspect the latest latency metrics for the running instances using `get_latency_metrics` with `window_minutes=10`.
3. Analyze the metrics. If the p99 latency in the last few data points exceeds a threshold of 1000ms, formulate a structured anomaly report.
4. Output your analysis clearly. If there is an anomaly, explain which instances are affected, what the current latency is compared to baseline, and hand off to the Diagnostician.
"""

def run_detector(log_callback, model="llama3.2"):
    log_callback("DETECTOR", "Detector Agent initialized. Polling telemetry...")
    
    messages = [
        {"role": "system", "content": DETECTOR_SYSTEM_PROMPT},
        {"role": "user", "content": "Check for any active performance anomalies on the running target application instances."}
    ]
    
    allowed_tools = ["list_running_instances", "get_latency_metrics"]
    
    try:
        response = run_agent_turn(model, messages, allowed_tools, lambda type, msg: log_callback("DETECTOR", f"{type}: {msg}" if isinstance(msg, str) else f"{type}: {json.dumps(msg)}"))
        return response
    except Exception as e:
        log_callback("SYSTEM", f"Detector Agent failed: {str(e)}")
        return f"Error running detector: {str(e)}"
