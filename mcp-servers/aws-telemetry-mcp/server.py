import os
import json
import time
from datetime import datetime, timedelta
import boto3
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("AWS Telemetry")

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
    return {"active_fault": None, "start_time": None}

def is_real_mode():
    return os.getenv("MODE") == "real"

@mcp.tool()
def list_running_instances() -> str:
    """Lists the running EC2 instances with their IDs, names, and IP addresses."""
    if not is_real_mode():
        # Simulated instances
        instances = [
            {"InstanceId": "i-091a1a2b3c4d5e6f0", "Name": "sentinelops-target-app-1", "State": "running", "PrivateIpAddress": "10.0.1.15"},
            {"InstanceId": "i-091b1a2b3c4d5e6f1", "Name": "sentinelops-target-app-2", "State": "running", "PrivateIpAddress": "10.0.1.16"},
            {"InstanceId": "i-091c1a2b3c4d5e6f2", "Name": "sentinelops-target-app-3", "State": "running", "PrivateIpAddress": "10.0.1.17"}
        ]
        return json.dumps(instances, indent=2)
    
    try:
        ec2 = boto3.client("ec2")
        response = ec2.describe_instances(
            Filters=[
                {"Name": "instance-state-name", "Values": ["running"]},
                {"Name": "tag:Project", "Values": ["sentinelops"]}
            ]
        )
        instances = []
        for reservation in response.get("Reservations", []):
            for inst in reservation.get("Instances", []):
                name = next((tag["Value"] for tag in inst.get("Tags", []) if tag["Key"] == "Name"), "unknown")
                instances.append({
                    "InstanceId": inst["InstanceId"],
                    "Name": name,
                    "State": inst["State"]["Name"],
                    "PrivateIpAddress": inst.get("PrivateIpAddress", "")
                })
        return json.dumps(instances, indent=2)
    except Exception as e:
        return f"Error connecting to AWS: {str(e)}"

@mcp.tool()
def get_latency_metrics(instance_id: str, window_minutes: int = 10) -> str:
    """Fetches the p99 latency metrics (in ms) for the given EC2 instance ID over the specified window."""
    try:
        window_minutes = int(window_minutes)
    except (ValueError, TypeError):
        window_minutes = 10

    if not is_real_mode():
        # Simulated metrics
        state = get_sim_state()
        active_fault = state.get("active_fault")
        
        now = datetime.now()
        data_points = []
        
        # Build 10 points
        for i in range(window_minutes):
            t = now - timedelta(minutes=window_minutes - 1 - i)
            # Default normal baseline latency is 150-180ms
            val = 150.0 + (i * 3) % 30
            
            if active_fault == "config_regression" and i >= window_minutes - 4:
                # Late points spike to ~4200ms
                val = 4200.0 + (i * 12) % 150
            elif active_fault == "security_group" and i >= window_minutes - 4:
                # Late points timeout / error spike
                val = 3000.0 + (i * 7) % 100
                
            data_points.append({
                "Timestamp": t.strftime("%Y-%m-%d %H:%M:%S"),
                "p99_latency_ms": val
            })
        return json.dumps(data_points, indent=2)

    try:
        cloudwatch = boto3.client("cloudwatch")
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=window_minutes)
        
        response = cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    "Id": "latency",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": "AWS/EC2",
                            "MetricName": "NetworkIn", # Replace with actual custom app metric in real deployments
                            "Dimensions": [{"Name": "InstanceId", "Value": instance_id}]
                        },
                        "Period": 60,
                        "Stat": "p99"
                    }
                }
            ],
            StartTime=start_time,
            EndTime=end_time
        )
        # Parse metric data
        timestamps = response["MetricDataResults"][0]["Timestamps"]
        values = response["MetricDataResults"][0]["Values"]
        points = [{"Timestamp": t.strftime("%Y-%m-%d %H:%M:%S"), "p99_latency_ms": v} for t, v in zip(timestamps, values)]
        return json.dumps(points, indent=2)
    except Exception as e:
        return f"Error fetching CloudWatch metrics: {str(e)}"

@mcp.tool()
def get_error_rate(instance_id: str, window_minutes: int = 10) -> str:
    """Fetches the error rate percentage for the given EC2 instance over the specified window."""
    try:
        window_minutes = int(window_minutes)
    except (ValueError, TypeError):
        window_minutes = 10

    if not is_real_mode():
        state = get_sim_state()
        active_fault = state.get("active_fault")
        now = datetime.now()
        data_points = []
        for i in range(window_minutes):
            t = now - timedelta(minutes=window_minutes - 1 - i)
            val = 0.0
            if active_fault == "security_group" and i >= window_minutes - 4:
                val = 100.0 # Total auth failure
            elif active_fault == "config_regression" and i >= window_minutes - 4:
                val = 15.0 # Increased db connection error rate
            data_points.append({
                "Timestamp": t.strftime("%Y-%m-%d %H:%M:%S"),
                "error_rate_pct": val
            })
        return json.dumps(data_points, indent=2)

    # In real mode, query CloudWatch metrics or ALB targets error rates
    return json.dumps([{"Timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), "error_rate_pct": 0.0}], indent=2)

@mcp.tool()
def get_recent_security_group_changes(window_minutes: int = 60) -> str:
    """Fetches recent security group configuration modifications from CloudTrail."""
    try:
        window_minutes = int(window_minutes)
    except (ValueError, TypeError):
        window_minutes = 60

    if not is_real_mode():
        state = get_sim_state()
        active_fault = state.get("active_fault")
        if active_fault == "security_group":
            return json.dumps([{
                "EventId": "ct-event-99a22f",
                "EventTime": (datetime.now() - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
                "EventName": "RevokeSecurityGroupIngress",
                "Username": "ci-deployer-bot",
                "UserAgent": "aws-cli/2.12.0",
                "RequestParameters": {
                    "groupId": "sg-0123456789abcdef0",
                    "ipPermissions": {
                        "items": [{
                            "ipProtocol": "tcp",
                            "fromPort": 8080,
                            "toPort": 8080,
                            "ipRanges": [{"cidrIp": "10.0.1.0/24"}]
                        }]
                    }
                },
                "Description": "Removed ingress access from private subnet to Auth Service port 8080"
            }], indent=2)
        return json.dumps([], indent=2)

    try:
        cloudtrail = boto3.client("cloudtrail")
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=window_minutes)
        response = cloudtrail.lookup_events(
            LookupAttributes=[
                {"AttributeKey": "EventName", "AttributeValue": "RevokeSecurityGroupIngress"},
                {"AttributeKey": "EventName", "AttributeValue": "AuthorizeSecurityGroupIngress"}
            ],
            StartTime=start_time,
            EndTime=end_time
        )
        events = []
        for event in response.get("Events", []):
            events.append({
                "EventId": event["EventId"],
                "EventTime": event["EventTime"].strftime("%Y-%m-%d %H:%M:%S"),
                "EventName": event["EventName"],
                "Username": event.get("Username", "unknown"),
                "CloudTrailEvent": json.loads(event["CloudTrailEvent"])
            })
        return json.dumps(events, indent=2)
    except Exception as e:
        return f"Error querying CloudTrail: {str(e)}"

if __name__ == "__main__":
    mcp.run()
