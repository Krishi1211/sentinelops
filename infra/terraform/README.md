# SentinelOps Target App Terraform Provisioning

This directory contains the Terraform configuration to provision the target application infrastructure in AWS.

## Topology
- **VPC** (`10.0.0.0/16`) with public subnets.
- **3 EC2 Instances** (`t2.micro` or `t3.micro`) running the Express Node.js target app behind a Network Load Balancer (NLB).
- **Network Load Balancer** listening on port 80 and forwarding traffic to port 5000 on the instances.
- **Security Groups** restricting incoming and outgoing traffic (exposing ports 22, 5000, and 8080).
- **S3 Bucket** to archive logs and generated incident postmortems.
- **IAM Roles** mapping isolated read-only (telemetry analysis) and write (remediation execution) credentials.

## Approximate Costs
All resources fall under the **AWS Free Tier** limits:
- **EC2 instances:** 750 hours/month of `t2.micro` or `t3.micro` are free.
- **NLB:** Free tier provides 15 LCU (Load Balancer Capacity Units) per month.
- **S3:** 5 GB of standard storage is free.
- **CloudWatch:** Standard metrics are free.

If run outside the free tier, the infrastructure costs less than **$0.05/hour** in total.

## Commands

### 1. Initialize Terraform
```bash
terraform init
```

### 2. Preview Plan
```bash
terraform plan
```

### 3. Deploy Resources
Ensure your AWS credentials are set up (e.g. via `aws configure` or env variables `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`).
```bash
terraform apply -auto-approve
```

### 4. Tear Down Infrastructure
Once done with testing/demonstration, destroy resources to avoid unnecessary costs:
```bash
terraform destroy -auto-approve
```
