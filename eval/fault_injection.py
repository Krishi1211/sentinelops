import os
import json
import argparse
import requests
import boto3

SIM_STATE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../agents/sim_state.json")
)

def get_sim_state():
    if os.path.exists(SIM_STATE_PATH):
        try:
            with open(SIM_STATE_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"active_fault": None}

def update_sim_state(updates):
    state = get_sim_state()
    state.update(updates)
    try:
        with open(SIM_STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Error updating sim state: {e}")

def is_real_mode():
    return os.getenv("MODE") == "real"

def inject_config_regression():
    print("[FAULT INJECTOR] Injecting database pool timeout config regression...")
    if not is_real_mode():
        # Simulated injection
        update_sim_state({"active_fault": "config_regression", "status": "incident_active"})
        print("[FAULT INJECTOR] Simulated config regression fault written to sim_state.json.")
        return True

    try:
        # In real mode, hit the target application to update its internal active fault simulation
        res = requests.post("http://localhost:5005/simulate/fault", json={"type": "config_regression"})
        if res.status_code == 200:
            print("[FAULT INJECTOR] Successfully injected timeout config regression on live target app.")
            return True
        else:
            print(f"[FAULT INJECTOR] Failed to inject: target app returned {res.status_code}")
            return False
    except Exception as e:
        print(f"[FAULT INJECTOR] Real mode connection error to target app: {e}")
        return False

def inject_security_group_lockdown():
    print("[FAULT INJECTOR] Injecting security group ingress lockdown...")
    if not is_real_mode():
        # Simulated injection
        update_sim_state({"active_fault": "security_group", "status": "incident_active"})
        print("[FAULT INJECTOR] Simulated security group fault written to sim_state.json.")
        return True

    try:
        # In real AWS mode, revoke the security group ingress rule for port 8080
        # Retrieve security group ID from terraform output or env
        # For our demonstration, we query the security group named "sentinelops-app-sg"
        ec2 = boto3.client("ec2")
        sgs = ec2.describe_security_groups(Filters=[{"Name": "group-name", "Values": ["sentinelops-app-sg"]}])
        if not sgs["SecurityGroups"]:
            print("[FAULT INJECTOR] Error: sentinelops-app-sg security group not found.")
            return False
        
        group_id = sgs["SecurityGroups"][0]["GroupId"]
        
        # Revoke rule allowing port 8080 from VPC CIDR
        ec2.revoke_security_group_ingress(
            GroupId=group_id,
            IpPermissions=[{
                "IpProtocol": "tcp",
                "FromPort": 8080,
                "ToPort": 8080,
                "IpRanges": [{"CidrIp": "10.0.1.0/24", "Description": "Allow private subnet traffic"}]
            }]
        )
        print(f"[FAULT INJECTOR] Successfully revoked port 8080 ingress on security group {group_id}.")
        
        # Also let target application know to trigger a simulated 503 auth timeout on port 5005
        requests.post("http://localhost:5005/simulate/fault", json={"type": "security_group"})
        return True
    except Exception as e:
        # If it was already revoked, return success
        if "InvalidPermission.NotFound" in str(e):
            print("[FAULT INJECTOR] Security group rule already revoked.")
            return True
        print(f"[FAULT INJECTOR] Real mode AWS error revoking SG rules: {e}")
        return False

def clear_all_faults():
    print("[FAULT INJECTOR] Clearing all active fault injections...")
    if not is_real_mode():
        update_sim_state({"active_fault": None, "status": "monitoring"})
        print("[FAULT INJECTOR] Simulated active fault cleared.")
        return True

    try:
        requests.post("http://localhost:5005/simulate/clear")
        print("[FAULT INJECTOR] Cleared simulated faults on target app.")
        
        # Also authorize the ingress rule back if real mode
        ec2 = boto3.client("ec2")
        sgs = ec2.describe_security_groups(Filters=[{"Name": "group-name", "Values": ["sentinelops-app-sg"]}])
        if sgs["SecurityGroups"]:
            group_id = sgs["SecurityGroups"][0]["GroupId"]
            try:
                ec2.authorize_security_group_ingress(
                    GroupId=group_id,
                    IpPermissions=[{
                        "IpProtocol": "tcp",
                        "FromPort": 8080,
                        "ToPort": 8080,
                        "IpRanges": [{"CidrIp": "10.0.1.0/24", "Description": "Allow private subnet traffic"}]
                    }]
                )
                print(f"[FAULT INJECTOR] Restored ingress rules on SG {group_id}.")
            except Exception as e:
                if "InvalidPermission.Duplicate" not in str(e):
                    print(f"[FAULT INJECTOR] Error authorizing ingress: {e}")
        return True
    except Exception as e:
        print(f"[FAULT INJECTOR] Connection error clearing faults: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelOps Fault Injection Tool")
    parser.add_argument("--action", choices=["inject", "clear"], required=True, help="Action to perform")
    parser.add_argument("--type", choices=["config", "security"], default="config", help="Type of fault to inject (default: config)")
    args = parser.parse_args()

    if args.action == "inject":
        if args.type == "config":
            inject_config_regression()
        elif args.type == "security":
            inject_security_group_lockdown()
    elif args.action == "clear":
        clear_all_faults()
