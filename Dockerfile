# Use Python with pre-built wheels (fastest option)
FROM python:3.10-slim-bullseye

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements-prod.txt .

# Install dependencies in one layer with aggressive caching
# --prefer-binary ensures we use pre-compiled wheels (much faster)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefer-binary -r requirements-prod.txt

# Copy only Python files (not web-ui)
COPY api_server.py fantasy_assistant.py league_queries.py dynamic_queries.py sync_sleeper_data.py config.py logger_config.py external_stats.py ./

# Port that Railway will use
EXPOSE 8080

# Start command
CMD ["python", "api_server.py"]

