output "load_balancer_dns" {
  value       = aws_lb.target_nlb.dns_name
  description = "The DNS Name of the Network Load Balancer"
}

output "instance_ids" {
  value       = aws_instance.target_instances[*].id
  description = "IDs of the deployed EC2 instances"
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.postmortem_bucket.id
  description = "S3 bucket for logs and postmortem storage"
}
