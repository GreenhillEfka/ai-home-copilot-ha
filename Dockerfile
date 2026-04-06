FROM python:3.11-slim

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN groupadd -r pilotsuite && useradd -r -g pilotsuite pilotsuite

# Set working directory
WORKDIR /app

# Copy requirements
COPY copilot_core/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY copilot_core/ ./copilot_core/
COPY scripts/ ./scripts/

# Create data directories
RUN mkdir -p /data/{patterns,vectors,graphs,backups,logs,pids,plugins,migrations,reports} \
    && chown -R pilotsuite:pilotsuite /data

# Switch to non-root user
USER pilotsuite

# Expose ports
EXPOSE 8080 5555

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command
CMD ["python", "-m", "copilot_core"]
