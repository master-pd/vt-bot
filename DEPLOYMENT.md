# Deployment Guide - VT View Tester

This guide covers deployment options for VT View Tester in different environments.

## 🏠 Self-Hosted Deployment

### Prerequisites
- Python 3.12+
- Git
- 1GB+ RAM
- 10GB+ storage
- Linux/Windows server

### Step-by-Step Deployment

#### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.12 python3-pip python3-venv -y

# Install Git
sudo apt install git -y

# Install additional dependencies
sudo apt install build-essential libssl-dev libffi-dev python3-dev -y