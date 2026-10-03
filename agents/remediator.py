import json
from agents.agent_helper import run_agent_turn

REMEDIATOR_SANDBOX_PROMPT = """You are the Remediator Agent for SentinelOps (Phase 1: Sandbox Verification).
Your role is to propose a fix for the diagnosed root cause and verify it inside the isolated CodeBox sandbox.

You must:
1. Review the Diagnostician's root cause report.
2. Formulate a remediation strategy (e.g. rollback config pool timeout, or restore port 8080 ingress access).
3. Test your proposed fix in the sandbox using the tool `test_fix_in_sandbox`.
4. If the test passes, you MUST output a statement stating that the fix is sandbox-verified, and that you are awaiting human approval to apply to production.
5. Do not call any write operations in remediation-mcp in this stage.
"""

REMEDIATOR_APPLY_PROMPT = """You are the Remediator Agent for SentinelOps (Phase 2: Live Remediation).
A human operator has approved the remediation. You have been provided with a secure `approval_token` and target resource info.

You must:
1. Apply the correct remediation tool based on the action required:
   - For config regressions: `apply_config_rollback(approval_token, target_id)`
   - For security group modifications: `restore_security_groups(approval_token, group_id)`
   - For crashed instances: `restart_instance(approval_token, instance_id)`
2. Ensure you supply the exact `approval_token` provided to you.
3. Confirm that the tool returns a success message and summarize the action taken.
"""

def run_remediator_sandbox(diagnosis_report, log_callback, model="llama3.2"):
    log_callback("REMEDIATOR", "Remediator Agent initialized (Sandbox Phase).")
    
    messages = [
        {"role": "system", "content": REMEDIATOR_SANDBOX_PROMPT},
        {"role": "user", "content": f"Test a fix in the sandbox for the following diagnosis:\n{diagnosis_report}"}
    ]
    
    allowed_tools = ["test_fix_in_sandbox"]
    
    try:
        response = run_agent_turn(model, messages, allowed_tools, lambda type, msg: log_callback("REMEDIATOR", f"{type}: {msg}" if isinstance(msg, str) else f"{type}: {json.dumps(msg)}"))
        return response
    except Exception as e:
        log_callback("SYSTEM", f"Remediator Agent sandbox check failed: {str(e)}")
        return f"Error in remediator sandbox: {str(e)}"

def run_remediator_apply(remediation_type, target_id, approval_token, log_callback, model="llama3.2"):
    log_callback("REMEDIATOR", f"Remediator Agent approved (Execution Phase). Target: {target_id}")
    
    prompt = f"Apply remediation for {remediation_type} on target {target_id} using approval token: '{approval_token}'"
    
    messages = [
        {"role": "system", "content": REMEDIATOR_APPLY_PROMPT},
        {"role": "user", "content": prompt}
    ]
    
    allowed_tools = ["apply_config_rollback", "restart_instance", "restore_security_groups"]
    
    try:
        response = run_agent_turn(model, messages, allowed_tools, lambda type, msg: log_callback("REMEDIATOR", f"{type}: {msg}" if isinstance(msg, str) else f"{type}: {json.dumps(msg)}"))
        return response
    except Exception as e:
        log_callback("SYSTEM", f"Remediator Agent execution failed: {str(e)}")
        return f"Error executing remediation: {str(e)}"
