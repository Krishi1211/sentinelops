import sys
import os
import json
import importlib.util

# Dynamic module loader to handle directory names with hyphens (e.g. mcp-servers/aws-telemetry-mcp)
def load_mcp_server(module_name, relative_path):
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Load MCP modules dynamically
aws_mcp = load_mcp_server("aws_telemetry_mcp", "../mcp-servers/aws-telemetry-mcp/server.py")
git_mcp = load_mcp_server("git_mcp", "../mcp-servers/git-mcp/server.py")
codebox_mcp = load_mcp_server("codebox_mcp", "../mcp-servers/codebox-mcp/server.py")
remediation_mcp = load_mcp_server("remediation_mcp", "../mcp-servers/remediation-mcp/server.py")

# Extract tools
list_running_instances = aws_mcp.list_running_instances
get_latency_metrics = aws_mcp.get_latency_metrics
get_error_rate = aws_mcp.get_error_rate
get_recent_security_group_changes = aws_mcp.get_recent_security_group_changes

get_recent_commits = git_mcp.get_recent_commits
get_commit_diff = git_mcp.get_commit_diff

test_fix_in_sandbox = codebox_mcp.test_fix_in_sandbox

apply_config_rollback = remediation_mcp.apply_config_rollback
restart_instance = remediation_mcp.restart_instance
restore_security_groups = remediation_mcp.restore_security_groups

# Tool schemas matching Ollama's tool structure
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_running_instances",
            "description": "Lists the running EC2 instances with their IDs, names, and IP addresses.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_latency_metrics",
            "description": "Fetches the p99 latency metrics (in ms) for the given EC2 instance ID over the specified window in minutes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "instance_id": {"type": "string", "description": "EC2 instance ID"},
                    "window_minutes": {"type": "integer", "description": "Minutes of history (default 10)"}
                },
                "required": ["instance_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_error_rate",
            "description": "Fetches the error rate percentage for the given EC2 instance over the specified window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "instance_id": {"type": "string", "description": "EC2 instance ID"},
                    "window_minutes": {"type": "integer", "description": "Minutes of history (default 10)"}
                },
                "required": ["instance_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_security_group_changes",
            "description": "Fetches recent security group configuration modifications from CloudTrail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "window_minutes": {"type": "integer", "description": "Minutes of history (default 60)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_commits",
            "description": "Fetches list of recent commits in the target repository since specified minutes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "since_minutes": {"type": "integer", "description": "Minutes of history (default 60)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_commit_diff",
            "description": "Returns the code changes/diff for a given commit SHA hash.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sha": {"type": "string", "description": "Commit hash"}
                },
                "required": ["sha"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "test_fix_in_sandbox",
            "description": "Deploys a proposed remediation patch in sandbox and replays requests to verify performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fix_description": {"type": "string", "description": "Description of patch to test"},
                    "replay_count": {"type": "integer", "description": "Count of requests (default 200)"}
                },
                "required": ["fix_description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_config_rollback",
            "description": "Reverts a recent bad configuration change on the target application host.",
            "parameters": {
                "type": "object",
                "properties": {
                    "approval_token": {"type": "string", "description": "Secure approval token from the human operator"},
                    "target_id": {"type": "string", "description": "Target ID or instance ID"}
                },
                "required": ["approval_token", "target_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restart_instance",
            "description": "Reboots/restarts an EC2 instance that is unresponsive or showing high resource exhaustion.",
            "parameters": {
                "type": "object",
                "properties": {
                    "approval_token": {"type": "string", "description": "Secure approval token from the human operator"},
                    "instance_id": {"type": "string", "description": "EC2 instance ID"}
                },
                "required": ["approval_token", "instance_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restore_security_groups",
            "description": "Restores security group rules to their correct, known-good baseline configuration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "approval_token": {"type": "string", "description": "Secure approval token from the human operator"},
                    "group_id": {"type": "string", "description": "Security group ID to restore"}
                },
                "required": ["approval_token", "group_id"]
            }
        }
    }
]

# Tool execution dispatcher
TOOL_FUNCTIONS = {
    "list_running_instances": list_running_instances,
    "get_latency_metrics": get_latency_metrics,
    "get_error_rate": get_error_rate,
    "get_recent_security_group_changes": get_recent_security_group_changes,
    "get_recent_commits": get_recent_commits,
    "get_commit_diff": get_commit_diff,
    "test_fix_in_sandbox": test_fix_in_sandbox,
    "apply_config_rollback": apply_config_rollback,
    "restart_instance": restart_instance,
    "restore_security_groups": restore_security_groups
}

def filter_schemas(names):
    return [s for s in TOOL_SCHEMAS if s["function"]["name"] in names]

def call_tool(name, arguments):
    import ollama  # inline to ensure availability
    func = TOOL_FUNCTIONS.get(name)
    if not func:
        return f"Error: Tool {name} not found"
    
    try:
        return func(**arguments)
    except Exception as e:
        return f"Error executing tool {name}: {str(e)}"

def run_agent_turn(model, messages, allowed_tools, log_callback):
    import ollama
    schemas = filter_schemas(allowed_tools)
    
    while True:
        log_callback("DEBUG", f"Calling Ollama model {model}...")
        response = ollama.chat(
            model=model,
            messages=messages,
            tools=schemas if schemas else None
        )
        
        message = response.get("message", {})
        messages.append(message)
        
        if message.get("content"):
            log_callback("TEXT", message["content"])
            
        tool_calls = message.get("tool_calls", [])
        if not tool_calls:
            return message.get("content", "")
            
        for call in tool_calls:
            tool_name = call["function"]["name"]
            tool_args = call["function"]["arguments"]
            
            log_callback("TOOL_CALL", {
                "tool": tool_name,
                "arguments": tool_args
            })
            
            result = call_tool(tool_name, tool_args)
            
            log_callback("TOOL_RESPONSE", {
                "tool": tool_name,
                "response": result
            })
            
            messages.append({
                "role": "tool",
                "content": str(result),
                "name": tool_name
            })
