# 🚀 AWS Deployment Guide for ASCL Bot

## 📋 Infrastructure Overview

### **Architecture Components:**
1. **EC2 Instances** - Host the wizard bot and user instances
2. **RDS Database** - Store user configurations and sessions
3. **S3 Buckets** - Store logs and backups
4. **Load Balancer** - Distribute traffic across instances
5. **Auto Scaling** - Handle traffic spikes
6. **CloudWatch** - Monitoring and logging

## 🏗️ AWS Services Required

### **Compute:**
- **EC2 t3.medium** (Wizard Bot) - $30/month
- **EC2 t3.large** (User Instances) - $60/month each
- **Auto Scaling Group** - Scale based on demand

### **Database:**
- **RDS PostgreSQL db.t3.micro** - $15/month
- **ElastiCache Redis** - $15/month (session storage)

### **Storage:**
- **S3 Standard** - $5/month (logs, backups)
- **EBS gp3** - $10/month per instance

### **Networking:**
- **Application Load Balancer** - $20/month
- **CloudFront CDN** - $5/month
- **Route 53 DNS** - $1/month

### **Security:**
- **AWS Certificate Manager** - Free (SSL certificates)
- **AWS Secrets Manager** - $1/month (API keys)

### **Total Estimated Cost:**
- **Base Infrastructure:** ~$150/month
- **Per 100 Users:** ~$200/month additional
- **Break-even:** ~20 paying users

## 🔧 Deployment Steps

### **1. Initial Setup**
```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Install Terraform (Infrastructure as Code)
# Download from: https://www.terraform.io/downloads.html
```

### **2. Infrastructure Deployment**
```bash
# Clone deployment repository
git clone https://github.com/luareload/ascl-bot.git
cd ascl-bot/aws-deployment

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Deploy infrastructure
terraform apply
```

### **3. Application Deployment**
```bash
# Build Docker images
docker build -t ascl-wizard-bot .
docker build -t ascl-user-bot -f Dockerfile.user .

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag ascl-wizard-bot:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/ascl-wizard-bot:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ascl-wizard-bot:latest

# Deploy with ECS
aws ecs update-service --cluster ascl-cluster --service wizard-bot-service --force-new-deployment
```

## 📁 Required Files

### **1. Dockerfile (Wizard Bot)**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "wizard_bot.py"]
```

### **2. Dockerfile.user (User Instances)**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### **3. docker-compose.yml (Local Testing)**
```yaml
version: '3.8'

services:
  wizard-bot:
    build: .
    ports:
      - "8000:8000"
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=ascl_bot
      - POSTGRES_USER=ascl
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### **4. terraform/main.tf (Infrastructure)**
```hcl
provider "aws" {
  region = "us-east-1"
}

# VPC and Networking
resource "aws_vpc" "ascl_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "ascl-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "ascl_igw" {
  vpc_id = aws_vpc.ascl_vpc.id

  tags = {
    Name = "ascl-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public_subnet_1" {
  vpc_id                  = aws_vpc.ascl_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "ascl-public-subnet-1"
  }
}

resource "aws_subnet" "public_subnet_2" {
  vpc_id                  = aws_vpc.ascl_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true

  tags = {
    Name = "ascl-public-subnet-2"
  }
}

# Security Groups
resource "aws_security_group" "ascl_sg" {
  name_description = "ASCL Bot Security Group"
  vpc_id          = aws_vpc.ascl_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ascl-security-group"
  }
}

# RDS Database
resource "aws_db_instance" "ascl_db" {
  identifier     = "ascl-database"
  engine         = "postgres"
  engine_version = "13.7"
  instance_class = "db.t3.micro"
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
  storage_encrypted     = true

  db_name  = "ascl_bot"
  username = "ascl_admin"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.ascl_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.ascl_db_subnet_group.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = true

  tags = {
    Name = "ascl-database"
  }
}

# Load Balancer
resource "aws_lb" "ascl_alb" {
  name               = "ascl-load-balancer"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.ascl_sg.id]
  subnets           = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]

  enable_deletion_protection = false

  tags = {
    Name = "ascl-load-balancer"
  }
}
```

## 🔐 Environment Variables

### **Production Environment:**
```bash
# Bot Configuration
BOT_TOKEN=your_wizard_bot_token_here
DATABASE_URL=postgresql://ascl_admin:password@ascl-database.region.rds.amazonaws.com:5432/ascl_bot
REDIS_URL=redis://ascl-redis.region.cache.amazonaws.com:6379

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Security
ENCRYPTION_KEY=your_32_byte_encryption_key
JWT_SECRET=your_jwt_secret_key

# Monitoring
SENTRY_DSN=your_sentry_dsn
LOG_LEVEL=INFO
```

## 📊 Monitoring & Scaling

### **CloudWatch Metrics:**
- CPU Utilization
- Memory Usage
- Active User Count
- Response Times
- Error Rates

### **Auto Scaling Triggers:**
- **Scale Up:** CPU > 70% for 5 minutes
- **Scale Down:** CPU < 30% for 10 minutes
- **Max Instances:** 10
- **Min Instances:** 2

### **Alerts:**
- High error rate (>5%)
- Database connection issues
- Memory usage >90%
- Disk space <10%

## 💰 Cost Optimization

### **Reserved Instances:**
- Save 30-60% on EC2 costs
- Commit to 1-3 year terms

### **Spot Instances:**
- Use for non-critical workloads
- Save up to 90% on compute costs

### **S3 Lifecycle Policies:**
- Move old logs to cheaper storage
- Delete logs after 90 days

## 🚀 Deployment Commands

### **Quick Deploy:**
```bash
# Deploy everything
./deploy.sh production

# Deploy only wizard bot
./deploy.sh wizard-bot

# Deploy user instance template
./deploy.sh user-bot

# Update configuration
./deploy.sh config-update
```

### **Monitoring:**
```bash
# Check service status
aws ecs describe-services --cluster ascl-cluster

# View logs
aws logs tail /aws/ecs/ascl-wizard-bot --follow

# Check metrics
aws cloudwatch get-metric-statistics --namespace AWS/ECS
```

## 🔧 Maintenance

### **Regular Tasks:**
- **Daily:** Check error logs and metrics
- **Weekly:** Review costs and usage
- **Monthly:** Update dependencies and security patches
- **Quarterly:** Review and optimize infrastructure

### **Backup Strategy:**
- **Database:** Daily automated backups
- **User Data:** Real-time replication
- **Configuration:** Version controlled in Git
- **Logs:** Archived to S3 Glacier

---

**This AWS deployment will provide enterprise-grade infrastructure for the ASCL Bot ecosystem, supporting thousands of users with high availability and scalability!** 🚀
