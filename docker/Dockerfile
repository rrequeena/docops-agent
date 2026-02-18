# docker/Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Java for tabula-py
RUN apt-get update && apt-get install -y \
    default-jre \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY src/ src/
COPY tests/ tests/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create uploads directory
RUN mkdir -p /app/data/uploads

EXPOSE 8000 8501

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
