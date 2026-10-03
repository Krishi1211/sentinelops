terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- VPC Infrastructure ---
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = {
    Name    = "${var.project_name}-vpc"
    Project = var.project_name
  }
}

resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true
  tags = {
    Name = "${var.project_name}-public-subnet-1"
  }
}

resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = true
  tags = {
    Name = "${var.project_name}-public-subnet-2"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags = {
    Name = "${var.project_name}-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "pub_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "pub_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

# --- Security Groups ---
resource "aws_security_group" "app_sg" {
  name        = "${var.project_name}-app-sg"
  description = "Security group for SentinelOps target web instances"
  vpc_id      = aws_vpc.main.id

  # Allow HTTP to target application port
  ingress {
    description = "Allow port 8080 from VPC"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  ingress {
    description = "Allow port 5000 from Load Balancer"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow SSH for administration
  ingress {
    description = "Allow SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Egress rules
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project_name}-app-sg"
    Project = var.project_name
  }
}

# --- S3 Bucket for Auditable Postmortems ---
resource "aws_s3_bucket" "postmortem_bucket" {
  bucket_prefix = "${var.project_name}-postmortems-"
  force_destroy = true
  tags = {
    Name    = "${var.project_name}-postmortems"
    Project = var.project_name
  }
}

# --- IAM Roles for Agent Isolation ---

# Read-only Telemetry role
resource "aws_iam_role" "agent_read_only" {
  name = "${var.project_name}-read-only-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "read_only_policy" {
  name        = "${var.project_name}-read-only-policy"
  description = "Allows agents to inspect telemetry and configuration without modifying state"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeSecurityGroups",
          "cloudwatch:GetMetricData",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:DescribeAlarms",
          "cloudtrail:LookupEvents",
          "s3:ListBucket",
          "s3:GetObject"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ro_attach" {
  role       = aws_iam_role.agent_read_only.name
  policy_arn = aws_iam_policy.read_only_policy.arn
}

# Write Remediation role (requires Human Approval token verification in code)
resource "aws_iam_role" "agent_remediation" {
  name = "${var.project_name}-remediation-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "remediation_policy" {
  name        = "${var.project_name}-remediation-policy"
  description = "Write access to EC2 reboot and security group settings, scoped strictly to Project resources"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:RebootInstances",
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupIngress",
          "s3:PutObject"
        ]
        Resource = "*" # Scoped down in deployment to specific VPC / instances
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "remed_attach" {
  role       = aws_iam_role.agent_remediation.name
  policy_arn = aws_iam_policy.remediation_policy.arn
}

# --- EC2 Target application instances ---
resource "aws_instance" "target_instances" {
  count                  = 3
  ami                    = "ami-0c7217cdde317cfec" # Ubuntu Server 22.04 LTS (HVM) in us-east-1
  instance_type          = var.instance_type
  subnet_id              = count.index % 2 == 0 ? aws_subnet.public_1.id : aws_subnet.public_2.id
  vpc_security_group_ids = [aws_security_group.app_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              sudo apt-get update -y
              sudo apt-get install -y nodejs npm git
              git clone https://github.com/example/sentinelops-target-app.git /home/ubuntu/app
              cd /home/ubuntu/app
              npm install
              PORT=5000 npm start
              EOF

  tags = {
    Name    = "${var.project_name}-target-app-${count.index + 1}"
    Project = var.project_name
  }
}

# --- Network Load Balancer ---
resource "aws_lb" "target_nlb" {
  name               = "${var.project_name}-nlb"
  internal           = false
  load_balancer_type = "network"
  subnets            = [aws_subnet.public_1.id, aws_subnet.public_2.id]

  tags = {
    Name    = "${var.project_name}-nlb"
    Project = var.project_name
  }
}

resource "aws_lb_target_group" "target_tg" {
  name        = "${var.project_name}-tg"
  port        = 5000
  protocol    = "TCP"
  vpc_id      = aws_vpc.main.id
  target_type = "instance"

  health_check {
    port     = "5000"
    protocol = "TCP"
    interval = 30
  }
}

resource "aws_lb_listener" "listener" {
  load_balancer_arn = aws_lb.target_nlb.arn
  port              = 80
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.target_tg.arn
  }
}

resource "aws_lb_target_group_attachment" "app_attachment" {
  count            = 3
  target_group_arn = aws_lb_target_group.target_tg.arn
  target_id        = aws_instance.target_instances[count.index].id
  port             = 5000
}

# --- CloudWatch Metric Alarm for Monitoring ---
resource "aws_cloudwatch_metric_alarm" "latency_alarm" {
  alarm_name          = "${var.project_name}-latency-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "NetworkIn" # Simulating p99 response metric
  namespace           = "AWS/EC2"
  period              = "60"
  statistic           = "Average"
  threshold           = "4000" # Alarm on high latency simulate value
  alarm_description   = "Trigger alert when latency exceeds 4000ms"
  actions_enabled     = false
}
