# Dockerfile for Captioner Backend (FastAPI)
# Python 3.12, using requirements.txt for dependencies

FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install system dependencies (if any are needed, add here)
# RUN apt-get update && apt-get install -y <package> && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

# Expose port for FastAPI (default 8000)
EXPOSE 8000

# Set environment variables (add as needed)
# ENV EXAMPLE_ENV_VAR=example_value

# Run FastAPI app with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
