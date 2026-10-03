export const mockScenarios = {
  config_regression: {
    name: "Config Regression (Timeout)",
    description: "Database connection pool timeout increased to 50s, leading to thread exhaustion.",
    steps: [
      {
        type: "log",
        agent: "SYSTEM",
        logType: "INFO",
        content: "Monitoring target application on us-east-1. NLB DNS: sentinelops-nlb-12948.amazonaws.com",
        latency: 165
      },
      {
        type: "log",
        agent: "SYSTEM",
        logType: "ALERT",
        content: "CloudWatch Metric Alarm triggered: sentinelops-latency-high. Latency threshold > 1000ms violated.",
        latency: 4200,
        pipeline: { detector: "active", diagnostician: "idle", remediator: "idle" }
      },
      {
        type: "log",
        agent: "DETECTOR",
        logType: "INFO",
        content: "Polling CloudWatch... anomaly detected: p99 latency 4200ms (baseline 180ms). Alerting Diagnostician Agent.",
        latency: 4205,
        pipeline: { detector: "done", diagnostician: "active", remediator: "idle" }
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Diagnostician Agent active. Formulating Hypothesis 1: Recent git deployment code regression.",
        latency: 4210
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Tool call: get_recent_commits(since_minutes=60)",
        latency: 4210
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Tool response: Found commit a3f9c2d by dev-bot: 'deploy: update connection_pool_timeout_ms setting to 50000ms'",
        latency: 4212
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Tool call: get_commit_diff(sha='a3f9c2d')",
        latency: 4215
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Tool response: Changed 'connection_pool_timeout_ms' from 1000 to 50000 in config.json.",
        latency: 4215
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Formulating Hypothesis 2: Network configuration/Security group changes. Querying CloudTrail...",
        latency: 4220
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Tool call: get_recent_security_group_changes(window_minutes=60)",
        latency: 4220
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Tool response: No matching security group ingress/egress events found in last 60 minutes.",
        latency: 4222
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Hypothesis 2 ruled out. Root cause confirmed: connection pool exhaustion due to 50s timeout setting in commit a3f9c2d. Handing off to Remediator.",
        latency: 4230,
        pipeline: { detector: "done", diagnostician: "done", remediator: "active" }
      },
      {
        type: "log",
        agent: "REMEDIATOR",
        logType: "INFO",
        content: "Remediator Agent active. Proposed fix: rollback connection_pool_timeout_ms to baseline (1000ms).",
        latency: 4230
      },
      {
        type: "log",
        agent: "REMEDIATOR",
        logType: "INFO",
        content: "Tool call: test_fix_in_sandbox(fix_description='rollback pool timeout to 1000ms')",
        latency: 4235
      },
      {
        type: "log",
        agent: "REMEDIATOR",
        logType: "INFO",
        content: "Tool response: Sandbox verified. 200/200 requests OK. Latency: 164ms. Status: PASSED.",
        latency: 4240
      },
      {
        type: "log",
        agent: "REMEDIATOR",
        logType: "ALERT",
        content: "Awaiting human approval to apply to production. Security token generated: SO-A3F9C2D.",
        latency: 4250,
        checkpoint: true // Blocks progress until clicked
      },
      {
        type: "log",
        agent: "SYSTEM",
        logType: "INFO",
        content: "Remediation approved by user. Token verified.",
        latency: 4250
      },
      {
        type: "log",
        agent: "REMEDIATOR",
        logType: "INFO",
        content: "Tool call: apply_config_rollback(approval_token='SO-A3F9C2D', target_id='i-091a1a2b3c4d5e6f0')",
        latency: 2800
      },
      {
        type: "log",
        agent: "REMEDIATOR",
        logType: "INFO",
        content: "Tool response: Configuration rolled back successfully on host replica.",
        latency: 1200
      },
      {
        type: "log",
        agent: "SYSTEM",
        logType: "INFO",
        content: "Target application recovery verified. Latency returned to healthy baseline.",
        latency: 168,
        pipeline: { detector: "done", diagnostician: "done", remediator: "done" }
      },
      {
        type: "postmortem",
        postmortem: `# POSTMORTEM: Connection Pool Exhaustion

**Incident Date:** 2026-07-13  
**Status:** RESOLVED  
**Severity:** SEV-1  

## Executive Summary
Autonomous detection triggered on anomalous target web service latency. The root cause was isolated, tested, and resolved successfully after operator validation.

## Diagnostics & Evidence
- Anomaly detected: p99 latency spiked to 4200ms.
- Diagnostician verified git history.
- Found commit \`a3f9c2d\` increasing pool timeout to 50000ms.
- Database pool connections exhausted due to persistent connection holding.

## Action Taken
Reverted timeout threshold back to baseline config (1000ms) on target environment.

## Metrics & Performance Scorecard
- **Detection Time:** 2.4s  
- **Diagnostic Duration:** 5.1s  
- **Remediation Sandboxing:** 200/200 OK  
- **AWS API Calls Made:** 4  
- **Hallucinated Statements:** 0  
`
      }
    ]
  },
  security_group: {
    name: "Security Group Lockdown",
    description: "Port 8080 ingress access removed, causing authentication calls to time out.",
    steps: [
      {
        type: "log",
        agent: "SYSTEM",
        logType: "INFO",
        content: "Monitoring target application on us-east-1. NLB DNS: sentinelops-nlb-12948.amazonaws.com",
        latency: 160
      },
      {
        type: "log",
        agent: "SYSTEM",
        logType: "ALERT",
        content: "CloudWatch Metric Alarm triggered: sentinelops-error-rate-high. Error rate spiked to 100%.",
        latency: 3000,
        pipeline: { detector: "active", diagnostician: "idle", remediator: "idle" }
      },
      {
        type: "log",
        agent: "DETECTOR",
        logType: "INFO",
        content: "Polling CloudWatch... anomaly detected: error rate 100%, p99 latency 3000ms. Alerting Diagnostician Agent.",
        latency: 3005,
        pipeline: { detector: "done", diagnostician: "active", remediator: "idle" }
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Diagnostician Agent active. Formulating Hypothesis 1: Recent git deployment code regression.",
        latency: 3010
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Tool call: get_recent_commits(since_minutes=60)",
        latency: 3010
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Tool response: Found commit b5e8d3f by web-dev: 'docs: update API documentation endpoints readme'",
        latency: 3012
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Hypothesis 1 ruled out. Commit b5e8d3f contains only README doc updates. Formulating Hypothesis 2: Security Group ingress/egress block.",
        latency: 3015
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Tool call: get_recent_security_group_changes(window_minutes=60)",
        latency: 3020
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Tool response: Found event ct-event-99a22f: RevokeSecurityGroupIngress on group sg-0123456789abcdef0 by username: ci-deployer-bot",
        latency: 3025
      },
      {
        type: "log",
        agent: "DIAGNOSTICIAN",
        logType: "INFO",
        content: "Evidence matches: Ingress permissions on port 8080 (Auth service) were revoked. Root cause confirmed: Port block. Handing off to Remediator.",
        latency: 3030,
        pipeline: { detector: "done", diagnostician: "done", remediator: "active" }
      },
      {
        type: "log",
        agent: "REMEDIATOR",
        logType: "INFO",
        content: "Remediator Agent active. Proposed fix: restore security group ingress rules to allow traffic on port 8080.",
        latency: 3030
      },
      {
        type: "log",
        agent: "REMEDIATOR",
        logType: "INFO",
        content: "Tool call: test_fix_in_sandbox(fix_description='authorize ingress port 8080 from VPC CIDR')",
        latency: 3035
      },
      {
        type: "log",
        agent: "REMEDIATOR",
        logType: "INFO",
        content: "Tool response: Sandbox verified. Auth service connection restored. Status: PASSED.",
        latency: 3040
      },
      {
        type: "log",
        agent: "REMEDIATOR",
        logType: "ALERT",
        content: "Awaiting human approval to apply to production. Security token generated: SO-SG8080X.",
        latency: 3050,
        checkpoint: true
      },
      {
        type: "log",
        agent: "SYSTEM",
        logType: "INFO",
        content: "Remediation approved by user. Token verified.",
        latency: 3050
      },
      {
        type: "log",
        agent: "REMEDIATOR",
        logType: "INFO",
        content: "Tool call: restore_security_groups(approval_token='SO-SG8080X', group_id='sg-0123456789abcdef0')",
        latency: 2000
      },
      {
        type: "log",
        agent: "REMEDIATOR",
        logType: "INFO",
        content: "Tool response: Ingress permissions successfully restored on group sg-0123456789abcdef0.",
        latency: 1000
      },
      {
        type: "log",
        agent: "SYSTEM",
        logType: "INFO",
        content: "Target application recovery verified. Error rate resolved to 0%.",
        latency: 165,
        pipeline: { detector: "done", diagnostician: "done", remediator: "done" }
      },
      {
        type: "postmortem",
        postmortem: `# POSTMORTEM: Security Group ingress block on Auth service

**Incident Date:** 2026-07-13  
**Status:** RESOLVED  
**Severity:** SEV-1  

## Executive Summary
Autonomous detection triggered on anomalous target web service latency. The root cause was isolated, tested, and resolved successfully after operator validation.

## Diagnostics & Evidence
- Anomaly detected: p99 latency spiked to 3000ms, error rate 100%.
- Checked Git log (no regressions found).
- Checked CloudTrail security group changes.
- Identified event ID \`ct-event-99a22f\` deleting Port 8080 ingress access.

## Action Taken
Restored security group rule to authorize traffic on port 8080 from VPC CIDR.

## Metrics & Performance Scorecard
- **Detection Time:** 2.4s  
- **Diagnostic Duration:** 5.1s  
- **Remediation Sandboxing:** 200/200 OK  
- **AWS API Calls Made:** 4  
- **Hallucinated Statements:** 0  
`
      }
    ]
  }
};
