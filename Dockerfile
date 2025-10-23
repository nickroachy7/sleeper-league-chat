# Use Python 3.9 slim image for faster builds
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-prod.txt requirements.txt

# Install Python dependencies (production only - faster build)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway will override this with PORT env var)
EXPOSE 5001

# Run the application
CMD ["python", "api_server.py"]

