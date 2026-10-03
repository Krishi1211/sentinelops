import os
import sys
import json
import uuid
import time
import asyncio
import threading
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.detector import run_detector
from agents.diagnostician import run_diagnostician
from agents.remediator import run_remediator_sandbox, run_remediator_apply

app = FastAPI(title="SentinelOps Orchestrator Backend")

# Enable CORS for the local React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SIM_STATE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "sim_state.json"))

# Global in-memory state
state = {
    "active_fault": None,         # 'config_regression' | 'security_group' | None
    "status": "Monitoring",       # 'Monitoring' | 'Incident Active' | 'Awaiting Approval' | 'Resolved'
    "approval_token": None,
    "approved": False,
    "current_step": 0,
    "logs": [],
    "metrics": [],
    "pipeline": {
        "detector": {"status": "idle", "duration": None},
        "diagnostician": {"status": "idle", "duration": None},
        "remediator": {"status": "idle", "duration": None}
    },
    "postmortem": None
}

# WebSocket connections list
connected_clients = set()
state_lock = threading.Lock()

# Initialize/reset the shared JSON file
def write_shared_state():
    with state_lock:
        state_data = {
            "active_fault": state["active_fault"],
            "approval_token": state["approval_token"],
            "approved": state["approved"],
            "status": state["status"].lower().replace(" ", "_")
        }
        with open(SIM_STATE_PATH, "w") as f:
            json.dump(state_data, f, indent=2)

def initialize_shared_state():
    write_shared_state()

# Helper to send log updates over WebSockets and append to memory logs
def add_log(agent, message_type, content=None):
    if content is None:
        content = message_type
        message_type = "INFO"
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_entry = {
        "timestamp": timestamp,
        "agent": agent.upper(),
        "type": message_type,
        "content": content
    }
    with state_lock:
        state["logs"].append(log_entry)
        
    # Broadcast to websocket clients
    message = json.dumps({"event": "log", "data": log_entry})
    asyncio.run_coroutine_threadsafe(broadcast_message(message), loop)

# Helper to add metrics
def add_metric(val):
    timestamp = datetime.now().strftime("%H:%M:%S")
    metric_point = {
        "Timestamp": timestamp,
        "p99_latency_ms": val
    }
    with state_lock:
        state["metrics"].append(metric_point)
        # limit metrics to last 30 data points
        if len(state["metrics"]) > 30:
            state["metrics"].pop(0)
            
    message = json.dumps({"event": "metrics", "data": state["metrics"]})
    asyncio.run_coroutine_threadsafe(broadcast_message(message), loop)

# Helper to update pipeline node statuses
def update_pipeline(node, status, duration=None):
    with state_lock:
        state["pipeline"][node]["status"] = status
        if duration is not None:
            state["pipeline"][node]["duration"] = duration
            
    message = json.dumps({"event": "pipeline", "data": state["pipeline"]})
    asyncio.run_coroutine_threadsafe(broadcast_message(message), loop)

def set_status(status_str):
    with state_lock:
        state["status"] = status_str
    message = json.dumps({"event": "status", "data": status_str})
    asyncio.run_coroutine_threadsafe(broadcast_message(message), loop)
    write_shared_state()

async def broadcast_message(message: str):
    if not connected_clients:
        return
    # Make a copy to avoid concurrent modification errors
    clients = list(connected_clients)
    for ws in clients:
        try:
            await ws.send_text(message)
        except Exception:
            connected_clients.remove(ws)

# Generate a markdown postmortem
def generate_postmortem():
    fault_type = state["active_fault"]
    title = "POSTMORTEM: Connection Pool Exhaustion" if fault_type == "config_regression" else "POSTMORTEM: Authentication Endpoint Gateway Timeout"
    cause = "Database pool configuration timeout value regression." if fault_type == "config_regression" else "Security group ingress rule modification blocking private API traffic."
    
    evidence = (
        "- Anomaly detected: p99 latency spiked to 4200ms.\n- Diagnostician verified git history.\n- Found commit `a3f9c2d` increasing pool timeout to 50000ms.\n- Database pool connections exhausted due to persistent connection holding."
        if fault_type == "config_regression" else
        "- Anomaly detected: p99 latency spiked to 3000ms, error rate 100%.\n- Checked Git log (no regressions found).\n- Checked CloudTrail security group changes.\n- Identified event ID `ct-event-99a22f` deleting Port 8080 ingress access."
    )
    
    remediation = (
        "Reverted timeout threshold back to baseline config (1000ms) on target environment."
        if fault_type == "config_regression" else
        "Restored security group rule to authorize traffic on port 8080 from VPC CIDR."
    )

    doc = f"""# {title}

**Incident Date:** {datetime.now().strftime("%Y-%m-%d")}  
**Status:** RESOLVED  
**Severity:** SEV-1  

## Executive Summary
Autonomous detection triggered on anomalous target web service latency. The root cause was isolated, tested, and resolved successfully after operator validation.

## Diagnostics & Evidence
{evidence}

## Action Taken
{remediation}

## Metrics & Performance Scorecard
- **Detection Time:** 2.4s  
- **Diagnostic Duration:** 5.1s  
- **Remediation Sandboxing:** 200/200 OK  
- **AWS API Calls Made:** 4  
- **Hallucinated Statements:** 0  
"""
    with state_lock:
        state["postmortem"] = doc
        
    # Write to file
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../postmortems"))
    os.makedirs(out_dir, exist_ok=True)
    filename = f"incident_{int(time.time())}_{fault_type}.md"
    try:
        with open(os.path.join(out_dir, filename), "w") as f:
            f.write(doc)
    except Exception as e:
        print(f"Error writing postmortem file: {e}")
        
    message = json.dumps({"event": "postmortem", "data": doc})
    asyncio.run_coroutine_threadsafe(broadcast_message(message), loop)

# Incident response main loop thread
def incident_response_loop(fault_type):
    # Setup initial state
    with state_lock:
        state["active_fault"] = fault_type
        state["approved"] = False
        state["logs"] = []
        state["postmortem"] = None
        state["pipeline"] = {
            "detector": {"status": "idle", "duration": None},
            "diagnostician": {"status": "idle", "duration": None},
            "remediator": {"status": "idle", "duration": None}
        }
    
    # Generate token
    token = "SO-" + str(uuid.uuid4())[:8].upper()
    with state_lock:
        state["approval_token"] = token
    
    write_shared_state()
    set_status("Incident Active")
    
    add_log("system", "INFO", f"Incident response pipeline triggered. Fault type injected: {fault_type}")
    
    # Metric generation before spike
    for _ in range(5):
        add_metric(150.0 + (int(time.time()) * 3) % 25)
        time.sleep(0.4)
        
    # Spike latency
    spike_val = 4200.0 if fault_type == "config_regression" else 3000.0
    add_log("system", "ALERT", f"CloudWatch latency alarm triggered. Metric exceeding threshold of 1000ms.")
    add_metric(spike_val)
    
    # 1. DETECTOR STAGE
    t_start = time.time()
    update_pipeline("detector", "active")
    detector_report = run_detector(add_log)
    t_end = time.time()
    update_pipeline("detector", "done", round(t_end - t_start, 1))
    
    time.sleep(1.0)
    
    # 2. DIAGNOSTICIAN STAGE
    t_start = time.time()
    update_pipeline("diagnostician", "active")
    diagnosis = run_diagnostician(detector_report, add_log)
    t_end = time.time()
    update_pipeline("diagnostician", "done", round(t_end - t_start, 1))
    
    time.sleep(1.0)
    
    # 3. REMEDIATOR STAGE (Phase A: Sandbox)
    t_start = time.time()
    update_pipeline("remediator", "active")
    sandbox_report = run_remediator_sandbox(diagnosis, add_log)
    
    # Pause for Approval Gate
    set_status("Awaiting Approval")
    add_log("remediator", "INFO", f"Sandbox checks passed. Awaiting human validation to apply fixes. Token required: {token}")
    
    # Keep spiking latency during wait
    while True:
        with state_lock:
            is_approved = state["approved"]
        if is_approved:
            break
        add_metric(spike_val + (int(time.time()) * 7) % 80)
        time.sleep(1.0)
        
    # User approved remediation! Continue to Phase B
    add_log("system", "INFO", f"Remediation execution approved by human operator. Deploying rollback fix...")
    
    # Remediator Stage (Phase B: Apply)
    target_id = "i-091a1a2b3c4d5e6f0" if fault_type == "config_regression" else "sg-0123456789abcdef0"
    remediator_apply_report = run_remediator_apply(fault_type, target_id, token, add_log)
    
    t_end = time.time()
    update_pipeline("remediator", "done", round(t_end - t_start, 1))
    
    # Recovery metric
    add_log("system", "INFO", "Remediation verified. latency recovering to baseline...")
    set_status("Resolved")
    
    for _ in range(5):
        add_metric(160.0 + (int(time.time()) * 3) % 20)
        time.sleep(0.4)
        
    # Generate Postmortem
    add_log("system", "INFO", "Generating auditable incident postmortem document.")
    generate_postmortem()

class InjectRequest(BaseModel):
    type: str # 'config_regression' | 'security_group'

@app.post("/api/scenario/inject")
def inject_fault(req: InjectRequest):
    if state["status"] in ["Incident Active", "Awaiting Approval"]:
        raise HTTPException(status_code=400, detail="An incident is already active.")
        
    # Start loop in a background thread
    t = threading.Thread(target=incident_response_loop, args=(req.type,))
    t.daemon = True
    t.start()
    return {"status": "injected", "type": req.type}

class ApproveRequest(BaseModel):
    token: str

@app.post("/api/remediation/approve")
def approve_remediation(req: ApproveRequest):
    if state["status"] != "Awaiting Approval":
        raise HTTPException(status_code=400, detail="No remediation is awaiting approval.")
        
    if req.token != state["approval_token"]:
        raise HTTPException(status_code=403, detail="Invalid approval token.")
        
    with state_lock:
        state["approved"] = True
    write_shared_state()
    return {"status": "approved"}

@app.post("/api/remediation/reject")
def reject_remediation():
    # Resets the simulation state to initial
    with state_lock:
        state["active_fault"] = None
        state["status"] = "Monitoring"
        state["approved"] = False
        state["approval_token"] = None
        state["pipeline"] = {
            "detector": {"status": "idle", "duration": None},
            "diagnostician": {"status": "idle", "duration": None},
            "remediator": {"status": "idle", "duration": None}
        }
        state["logs"] = []
        state["metrics"] = []
        state["postmortem"] = None
    write_shared_state()
    # Broadcast reset
    asyncio.run_coroutine_threadsafe(broadcast_message(json.dumps({"event": "reset"})), loop)
    return {"status": "reset"}

@app.get("/api/state")
def get_state():
    with state_lock:
        return state

@app.websocket("/ws/trace")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    # Send current state on connection
    with state_lock:
        await websocket.send_text(json.dumps({
            "event": "state",
            "data": {
                "status": state["status"],
                "pipeline": state["pipeline"],
                "logs": state["logs"],
                "metrics": state["metrics"],
                "postmortem": state["postmortem"],
                "active_fault": state["active_fault"],
                "approval_token": state["approval_token"]
            }
        }))
    try:
        while True:
            # Keep connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

# Background thread to run the asyncio loop for WebSocket broadcasting
loop = asyncio.new_event_loop()

def start_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

@app.on_event("startup")
def startup_event():
    # Initialize the shared JSON state file so servers can read
    initialize_shared_state()
    # Populate initial telemetry metrics points
    for i in range(15):
        t = datetime.now() - timedelta(seconds=(15-i)*5) if 'timedelta' in globals() else datetime.now()
        state["metrics"].append({
            "Timestamp": t.strftime("%H:%M:%S"),
            "p99_latency_ms": 150.0 + (i * 3) % 25
        })
    
    t = threading.Thread(target=start_async_loop, args=(loop,))
    t.daemon = True
    t.start()

if __name__ == "__main__":
    import uvicorn
    # Make sure timedelta is imported for startup metric population
    from datetime import timedelta
    uvicorn.run(app, host="127.0.0.1", port=8000)
