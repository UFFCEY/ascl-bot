# Output values for the ASCL Bot AWS deployment

# Load Balancer DNS name
output "load_balancer_dns" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

# Load Balancer Zone ID
output "load_balancer_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

# Database endpoint
output "db_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

# Database port
output "db_port" {
  description = "RDS instance port"
  value       = aws_db_instance.main.port
}

# Redis endpoint
output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_cluster.main.cache_nodes[0].address
  sensitive   = true
}

# Redis port
output "redis_port" {
  description = "ElastiCache Redis port"
  value       = aws_elasticache_cluster.main.cache_nodes[0].port
}

# VPC ID
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

# Public subnet IDs
output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

# Private subnet IDs
output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

# Security group IDs
output "bot_security_group_id" {
  description = "ID of the bot security group"
  value       = aws_security_group.bot.id
}

output "database_security_group_id" {
  description = "ID of the database security group"
  value       = aws_security_group.database.id
}

output "redis_security_group_id" {
  description = "ID of the Redis security group"
  value       = aws_security_group.redis.id
}

# Auto Scaling Group name
output "autoscaling_group_name" {
  description = "Name of the Auto Scaling Group"
  value       = aws_autoscaling_group.bot.name
}

# Launch template ID
output "launch_template_id" {
  description = "ID of the launch template"
  value       = aws_launch_template.bot.id
}

# S3 bucket name
output "s3_bucket_name" {
  description = "Name of the S3 bucket for file storage"
  value       = aws_s3_bucket.bot_storage.bucket
}

# CloudWatch log group name
output "cloudwatch_log_group" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.bot.name
}

# SNS topic ARN
output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.arn
}

# IAM role ARN
output "ec2_role_arn" {
  description = "ARN of the EC2 IAM role"
  value       = aws_iam_role.ec2_role.arn
}

# Key pair name
output "key_pair_name" {
  description = "Name of the EC2 key pair"
  value       = aws_key_pair.main.key_name
}

# Application URLs
output "application_urls" {
  description = "Important application URLs"
  value = {
    health_check = "http://${aws_lb.main.dns_name}/health"
    metrics      = "http://${aws_lb.main.dns_name}/metrics"
    webhook      = "http://${aws_lb.main.dns_name}/webhook"
  }
}

# AWS Console URLs
output "aws_console_urls" {
  description = "AWS Console URLs for monitoring"
  value = {
    cloudwatch_dashboard = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${var.project_name}-dashboard"
    ec2_instances       = "https://console.aws.amazon.com/ec2/v2/home?region=${var.aws_region}#Instances:tag:Name=${var.project_name}-instance"
    rds_database        = "https://console.aws.amazon.com/rds/home?region=${var.aws_region}#database:id=${aws_db_instance.main.id}"
    load_balancer       = "https://console.aws.amazon.com/ec2/v2/home?region=${var.aws_region}#LoadBalancers:search=${aws_lb.main.name}"
    auto_scaling        = "https://console.aws.amazon.com/ec2/autoscaling/home?region=${var.aws_region}#AutoScalingGroups:id=${aws_autoscaling_group.bot.name}"
  }
}

# Cost estimation
output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown (USD)"
  value = {
    ec2_instances    = "~$30-60 (2x t3.small)"
    rds_database     = "~$15-25 (t3.micro)"
    elasticache      = "~$12-20 (t3.micro)"
    load_balancer    = "~$18-25"
    data_transfer    = "~$5-15"
    cloudwatch_s3    = "~$5-10"
    total_estimated  = "~$85-155"
    note            = "Costs may vary based on usage and AWS pricing changes"
  }
}

# Deployment summary
output "deployment_summary" {
  description = "Summary of the deployed infrastructure"
  value = {
    project_name     = var.project_name
    environment      = var.environment
    aws_region       = var.aws_region
    deployment_time  = timestamp()
    infrastructure = {
      vpc_cidr           = aws_vpc.main.cidr_block
      availability_zones = length(data.aws_availability_zones.available.names)
      public_subnets     = length(aws_subnet.public)
      private_subnets    = length(aws_subnet.private)
      ec2_instance_type  = aws_launch_template.bot.instance_type
      database_engine    = aws_db_instance.main.engine
      database_version   = aws_db_instance.main.engine_version
      cache_engine       = aws_elasticache_cluster.main.engine
    }
    scaling = {
      min_instances     = aws_autoscaling_group.bot.min_size
      max_instances     = aws_autoscaling_group.bot.max_size
      desired_instances = aws_autoscaling_group.bot.desired_capacity
    }
    monitoring = {
      cloudwatch_logs    = aws_cloudwatch_log_group.bot.name
      sns_alerts        = aws_sns_topic.alerts.name
      dashboard_created = true
    }
    security = {
      vpc_isolated      = true
      database_private  = true
      cache_private     = true
      encryption_enabled = true
      iam_roles_created = true
    }
  }
}

# Quick commands
output "useful_commands" {
  description = "Useful commands for managing the deployment"
  value = {
    check_health     = "curl http://${aws_lb.main.dns_name}/health"
    view_logs        = "aws logs tail ${aws_cloudwatch_log_group.bot.name} --follow"
    ssh_to_instance  = "aws ec2 describe-instances --filters 'Name=tag:Name,Values=${var.project_name}-instance' --query 'Reservations[0].Instances[0].PublicIpAddress' --output text | xargs -I {} ssh -i ~/.ssh/id_rsa ec2-user@{}"
    scale_up         = "aws autoscaling set-desired-capacity --auto-scaling-group-name ${aws_autoscaling_group.bot.name} --desired-capacity 3"
    scale_down       = "aws autoscaling set-desired-capacity --auto-scaling-group-name ${aws_autoscaling_group.bot.name} --desired-capacity 1"
    create_snapshot  = "aws rds create-db-snapshot --db-instance-identifier ${aws_db_instance.main.id} --db-snapshot-identifier ${var.project_name}-manual-snapshot-$(date +%Y%m%d-%H%M%S)"
  }
}
