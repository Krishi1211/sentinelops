variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region to deploy resources"
}

variable "instance_type" {
  type        = string
  default     = "t2.micro"
  description = "EC2 instance type for target application (free tier eligible)"
}

variable "project_name" {
  type        = string
  default     = "sentinelops"
  description = "Project name tag for resource naming"
}
