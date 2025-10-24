# Use Python with pre-built wheels (fastest option)
FROM python:3.10-slim-bullseye

# Set working directory
WORKDIR /app

# Force rebuild - updated 2025-10-24
ARG CACHEBUST=20251024

# Copy requirements
COPY requirements-prod.txt .

# Install dependencies in one layer with aggressive caching
# --prefer-binary ensures we use pre-compiled wheels (much faster)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefer-binary -r requirements-prod.txt

# Copy all Python files (not web-ui)
COPY *.py ./

# Port that Railway will use
EXPOSE 8080

# Start command
CMD ["python", "api_server.py"]

