# SentinelOps: Autonomous Multi-Agent SRE Control Room Dashboard

SentinelOps is an autonomous incident response platform. Backed by a local tool-calling model (`llama3.2` running on Ollama) and using the Model Context Protocol (MCP), it detects cloud telemetry metrics anomalies, diagnoses the root cause by evaluating multiple hypotheses, tests potential fixes in a Docker sandbox, and executes remediations after secure human validation.

---

## System Architecture

```mermaid
graph TB
    subgraph Client-Side Dashboard
      Dash[React Dashboard]
    end

    subgraph Orchestrator & Backend
      Orch[Python Orchestrator] <--> WS[WebSocket / API Server]
      Orch --> Detector[Detector Agent]
      Orch --> Diagnostician[Diagnostician Agent]
      Orch --> Remediator[Remediator Agent]
      WS <--> Dash
    end

    subgraph MCP Servers / Tools
      Detector & Diagnostician --> Telemetry[aws-telemetry-mcp]
      Diagnostician --> Git[git-mcp]
      Remediator --> CodeBox[codebox-mcp]
      Remediator --> Remediation[remediation-mcp]
    end

    subgraph Target Environment (Real or Simulated)
      Telemetry --> AWS[AWS CloudWatch / EC2]
      Git --> LocalGit[Local Git History]
      CodeBox --> Docker[Docker Sandbox / Process Runner]
      Remediation --> AWS_Remed[AWS EC2 / SG Changes]
    end
```

---

## Features
- **Local LLM Isolation:** Runs all reasoning locally via Ollama. No infrastructure configuration or proprietary credentials leak to public APIs.
- **Strict Approval Gate:** The `remediation-mcp` write-action tools validate a session safety token server-side. Unapproved changes are blocked.
- **Dual-Mode Execution:**
  - **Simulated Mode (Default):** Runs immediately without real AWS credentials or Docker running, using a mock state timeline (`sim_state.json`).
  - **Real Mode (`MODE=real`):** Communicates with live AWS resources (3 EC2 instances behind a Network Load Balancer provisioned via Terraform) and replays traffic in Docker.

---

## Directory Structure

```
sentinelops/
  infra/
    terraform/                # Target app AWS infrastructure, S3, IAM roles
      README.md                # Deploy/destroy commands and Free Tier billing notes
  target-app/                  # Toy monitored HTTP web service
  mcp-servers/
    aws-telemetry-mcp/        # CloudWatch metrics and EC2 telemetry tool
    git-mcp/                  # Git commit analyzer tool
    codebox-mcp/              # Docker code verification tool
    remediation-mcp/          # Safety-gated EC2/Security group rollback execution tool
  agents/
    agent_helper.py           # Ollama tool-calling dispatcher
    detector.py               # Latency anomaly detector agent
    diagnostician.py          # Root-cause analyst agent
    remediator.py             # Sandbox validator and change applier agent
    orchestrator.py           # Pipeline lifecycle coordinator & WebSocket server
  eval/
    fault_injection.py        # Fault injector script (Config timeout / SG block)
    scorer.py                 # Automated benchmark evaluator scoring tool
    results/                  # Markdown benchmark scorecard records
  dashboard/                  # React + Vite + Tailwind CSS frontend
  postmortems/                 # Auto-generated markdown postmortem reports
```

---

## Setup & Running Guide

### Prerequisites
- Node.js (v18+) and npm
- Python (v3.10+)
- Ollama running locally with Llama 3.2:
  ```bash
  ollama run llama3.2
  ```

---

### Step 1: Start the Target Application
```bash
cd target-app
npm install
npm start
```
The target application starts on port `5000`.

---

### Step 2: Start the Orchestrator Backend
Set up the Python environment and run the FastAPI server:
```bash
# In root directory
source venv/bin/activate
python agents/orchestrator.py
```
The orchestrator starts on port `8000`.

---

### Step 3: Run the Dashboard
Open a new terminal, build, and run the React client:
```bash
cd dashboard
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

### Step 4: Inject a Fault & Observe Evaluation Scorer
To trigger an automated trial run and record agent performance metrics, execute the evaluation scorer script:
```bash
# In root directory
source venv/bin/activate
python eval/scorer.py
```
This triggers both the **Config Regression** and **Security Group Lockdown** scenarios, programmatically checks diagnosis reports, submits the safety tokens to execute remediation, and writes results to `eval/results/scorecard.md`.

---

## Safety Enforcement Details
The `remediation-mcp` server exposes write tools (e.g. `apply_config_rollback`, `restore_security_groups`) that require a valid `approval_token`.
On incident detection, the orchestrator generates a random one-time token (`SO-[HEX]`) and sets the system status to `Awaiting Approval`.
- The Remediator Agent cannot execute rolling actions directly; it stops and outputs the token.
- The human operator must input this exact token in the dashboard.
- Upon approval, the orchestrator updates `sim_state.json` (`approved: true`). Only then will subsequent remediation tool executions be authorized server-side.
