FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    git \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright
RUN playwright install chromium

# Copy application
COPY . .

# Create data directory
RUN mkdir -p data/{accounts,proxies,logs,backups,reports}

# Initialize database
RUN python -c "from database.models import init_database; init_database()"

# Expose port (if needed)
# EXPOSE 8000

# Run application
CMD ["python", "run.py", "--mode", "bot"]