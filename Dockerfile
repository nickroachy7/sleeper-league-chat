# Use Python slim image (much faster than alpine for Railway)
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy only requirements first for better Docker caching
COPY requirements-prod.txt .

# Install dependencies - use pip's binary wheels for speed
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy all Python files
COPY *.py ./

# Railway will set PORT env variable
ENV PORT=5001

# Run the application
CMD python api_server.py

