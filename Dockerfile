# Minimal Dockerfile for GovCon Suite
FROM python:3.11-slim

# System packages (optional: add build tools if needed by some wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Default environment (can be overridden by docker-compose)
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Entrypoint for Streamlit app
CMD ["streamlit", "run", "Apollo_GovCon.py", "--server.port", "8501", "--server.address", "0.0.0.0"]

