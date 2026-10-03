import os
import json
import boto3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AWS Remediation Gate")

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
    return {"active_fault": None, "approval_token": None, "approved": False}

def update_sim_state(updates):
    state = get_sim_state()
    state.update(updates)
    try:
        with open(SIM_STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Error updating sim state: {e}")

def validate_token(token: str) -> bool:
    state = get_sim_state()
    expected_token = state.get("approval_token")
    approved = state.get("approved")
    # Verify that a token exists, matches, and the session is approved
    return expected_token is not None and token == expected_token and approved

def is_real_mode():
    return os.getenv("MODE") == "real"

@mcp.tool()
def apply_config_rollback(approval_token: str, target_id: str) -> str:
    """Reverts a recent bad configuration change on the target application host."""
    if not validate_token(approval_token):
        return "ERROR: Access Denied. Invalid or unapproved security token. Action rejected."
    
    if not is_real_mode():
        # Clear mock fault
        update_sim_state({"active_fault": None, "approved": False, "approval_token": None, "status": "resolved"})
        return json.dumps({
            "status": "success",
            "message": f"Successfully rolled back config commit regression on {target_id}",
            "previous_value": "50000ms",
            "new_value": "1000ms",
            "applied_by": "RemediatorAgent"
        }, indent=2)

    try:
        # Real AWS SSM/EC2 remediation
        # e.g., deploy a config file to the instances or restart target-app service
        # For the toy environment, we make a call to our target app on port 5005:
        import requests
        res = requests.post("http://localhost:5005/simulate/clear")
        if res.status_code == 200:
            return json.dumps({
                "status": "success",
                "message": "Successfully rolled back configuration via target app REST API.",
                "details": res.json()
            })
        else:
            return f"Failed to reset config: target app responded with {res.status_code}"
    except Exception as e:
        return f"Error executing rollback on AWS: {str(e)}"

@mcp.tool()
def restart_instance(approval_token: str, instance_id: str) -> str:
    """Reboots/restarts an EC2 instance that is unresponsive or showing high resource exhaustion."""
    if not validate_token(approval_token):
        return "ERROR: Access Denied. Invalid or unapproved security token. Action rejected."

    if not is_real_mode():
        update_sim_state({"active_fault": None, "approved": False, "approval_token": None, "status": "resolved"})
        return json.dumps({
            "status": "success",
            "message": f"Successfully restarted EC2 instance {instance_id}",
            "state": "pending"
        }, indent=2)

    try:
        ec2 = boto3.client("ec2")
        ec2.reboot_instances(InstanceIds=[instance_id])
        return json.dumps({
            "status": "success",
            "message": f"Reboot command issued for instance {instance_id}"
        })
    except Exception as e:
        return f"Error restarting EC2 instance: {str(e)}"

@mcp.tool()
def restore_security_groups(approval_token: str, group_id: str) -> str:
    """Restores the security group rules to their correct, known-good baseline configuration."""
    if not validate_token(approval_token):
        return "ERROR: Access Denied. Invalid or unapproved security token. Action rejected."

    if not is_real_mode():
        update_sim_state({"active_fault": None, "approved": False, "approval_token": None, "status": "resolved"})
        return json.dumps({
            "status": "success",
            "message": f"Successfully restored security group {group_id} ingress rules to allow traffic on port 8080 from the load balancer subnet.",
            "rules_added": 1
        }, indent=2)

    try:
        ec2 = boto3.client("ec2")
        # Add the ingress rule that was removed: allow port 8080 from load balancer CIDR
        # For simplicity, we authorize the standard rule:
        ec2.authorize_security_group_ingress(
            GroupId=group_id,
            IpPermissions=[{
                "IpProtocol": "tcp",
                "FromPort": 8080,
                "ToPort": 8080,
                "IpRanges": [{"CidrIp": "10.0.1.0/24", "Description": "Allow private subnet traffic"}]
            }]
        )
        return json.dumps({
            "status": "success",
            "message": f"Restored ingress rule on security group {group_id}"
        })
    except Exception as e:
        # If it already exists, return success, otherwise throw error
        if "InvalidPermission.Duplicate" in str(e):
            return json.dumps({
                "status": "success",
                "message": f"Ingress rule was already present or resolved on group {group_id}"
            })
        return f"Error restoring security group rules: {str(e)}"

if __name__ == "__main__":
    mcp.run()
