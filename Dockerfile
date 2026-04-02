FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY requirements.txt .
COPY env/ ./env/
COPY agent/ ./agent/
COPY evaluate.py .
COPY run.py .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default command: run evaluation
CMD ["python", "evaluate.py"]
