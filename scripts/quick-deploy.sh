#!/bin/bash

set -e

echo "🚀 ASCL Bot Quick Deploy to AWS"
echo "==============================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on supported OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    print_error "This script is designed for Unix-like systems. Please use WSL on Windows."
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install AWS CLI
install_aws_cli() {
    print_status "Installing AWS CLI..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            brew install awscli
        else
            curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
            sudo installer -pkg AWSCLIV2.pkg -target /
        fi
    else
        # Linux
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        unzip awscliv2.zip
        sudo ./aws/install
        rm -rf aws awscliv2.zip
    fi
}

# Function to install Terraform
install_terraform() {
    print_status "Installing Terraform..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            brew tap hashicorp/tap
            brew install hashicorp/tap/terraform
        else
            print_error "Please install Homebrew first or install Terraform manually"
            exit 1
        fi
    else
        # Linux
        wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt update && sudo apt install terraform
    fi
}

# Function to install Docker
install_docker() {
    print_status "Installing Docker..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        print_warning "Please install Docker Desktop for Mac from https://docker.com/products/docker-desktop"
        read -p "Press Enter after installing Docker Desktop..."
    else
        # Linux
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        print_warning "Please log out and log back in for Docker permissions to take effect"
    fi
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check AWS CLI
if ! command_exists aws; then
    print_warning "AWS CLI not found. Installing..."
    install_aws_cli
fi

# Check Terraform
if ! command_exists terraform; then
    print_warning "Terraform not found. Installing..."
    install_terraform
fi

# Check Docker
if ! command_exists docker; then
    print_warning "Docker not found. Installing..."
    install_docker
fi

# Check Git
if ! command_exists git; then
    print_error "Git is required but not installed. Please install Git first."
    exit 1
fi

print_success "All prerequisites checked!"

# Get user inputs
echo ""
print_status "Setting up configuration..."

# AWS Configuration
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    print_warning "AWS credentials not configured."
    echo "Please configure AWS CLI with your credentials:"
    aws configure
fi

# Get project details
read -p "Enter your email for alerts: " ALERT_EMAIL
read -p "Enter AWS region (default: us-east-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

# Get Telegram credentials
echo ""
print_status "Telegram Bot Configuration"
echo "You need to get these from https://my.telegram.org/apps and @BotFather"
read -p "Enter Telegram API ID: " TELEGRAM_API_ID
read -p "Enter Telegram API Hash: " TELEGRAM_API_HASH
read -p "Enter Bot Token (from @BotFather): " WIZARD_BOT_TOKEN

# Get OpenAI API key
echo ""
read -p "Enter OpenAI API Key: " OPENAI_API_KEY

# Clone repository
print_status "Cloning ASCL Bot repository..."
if [ -d "ascl-bot" ]; then
    print_warning "Directory 'ascl-bot' already exists. Updating..."
    cd ascl-bot
    git pull
else
    git clone https://github.com/UFFCEY/ascl-bot.git
    cd ascl-bot
fi

# Create directory structure
mkdir -p terraform scripts docker

# Generate SSH key if needed
if [ ! -f ~/.ssh/id_rsa ]; then
    print_status "Generating SSH key for EC2 access..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
fi

# Create Terraform variables
print_status "Creating Terraform configuration..."
cat > terraform/terraform.tfvars << EOF
aws_region = "${AWS_REGION}"
environment = "production"
project_name = "ascl-bot"
db_password = "$(openssl rand -base64 32)"
alert_email = "${ALERT_EMAIL}"
EOF

# Create environment file
print_status "Creating environment configuration..."
cat > .env << EOF
# Telegram Configuration
TELEGRAM_API_ID=${TELEGRAM_API_ID}
TELEGRAM_API_HASH=${TELEGRAM_API_HASH}
WIZARD_BOT_TOKEN=${WIZARD_BOT_TOKEN}

# OpenAI Configuration
OPENAI_API_KEY=${OPENAI_API_KEY}

# AWS Configuration
AWS_REGION=${AWS_REGION}
ENVIRONMENT=production

# Bot Configuration
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=100
RATE_LIMIT_PER_MINUTE=60

# Security Configuration
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Feature Flags
ENABLE_AUTO_RESPONSE=true
ENABLE_CHAT_ANALYSIS=true
ENABLE_TYPING_SIMULATION=true
ENABLE_PREFERENCE_LEARNING=true
EOF

# Initialize and deploy Terraform
print_status "Initializing Terraform..."
cd terraform
terraform init

print_status "Planning Terraform deployment..."
terraform plan

echo ""
print_warning "This will create AWS resources that may incur charges (~$50-150/month)."
read -p "Do you want to proceed with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Deployment cancelled."
    exit 1
fi

print_status "Deploying infrastructure to AWS..."
terraform apply -auto-approve

# Get outputs
print_status "Getting deployment information..."
LOAD_BALANCER_DNS=$(terraform output -raw load_balancer_dns)
DB_ENDPOINT=$(terraform output -raw db_endpoint)

# Wait for deployment to be ready
print_status "Waiting for application to start..."
for i in {1..20}; do
    if curl -f "http://${LOAD_BALANCER_DNS}/health" >/dev/null 2>&1; then
        print_success "Application is healthy!"
        break
    fi
    echo "Waiting... (attempt $i/20)"
    sleep 30
done

# Final output
echo ""
echo "🎉 ASCL Bot deployed successfully to AWS!"
echo "========================================"
echo ""
echo "📊 Deployment Details:"
echo "├── Load Balancer URL: http://${LOAD_BALANCER_DNS}"
echo "├── Health Check: http://${LOAD_BALANCER_DNS}/health"
echo "├── Database Endpoint: ${DB_ENDPOINT}"
echo "├── AWS Region: ${AWS_REGION}"
echo "└── Environment: production"
echo ""
echo "🔧 Next Steps:"
echo "1. Test your bot: https://t.me/asclw_bot"
echo "2. Monitor in CloudWatch: https://console.aws.amazon.com/cloudwatch/"
echo "3. View logs: aws logs tail /aws/ec2/ascl-bot --follow"
echo "4. Update webhook (if needed): http://${LOAD_BALANCER_DNS}/webhook"
echo ""
echo "💰 Estimated monthly cost: $50-150 USD"
echo "📈 Auto-scaling: 1-5 instances based on load"
echo ""
print_success "Deployment completed! Your bot is now running 24/7 on AWS."
