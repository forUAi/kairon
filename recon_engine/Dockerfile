# Use official Python image
FROM python:3.11-slim

# Set environment
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-root

# Copy code
COPY . .

# Run FastAPI server by default
CMD ["uvicorn", "recon_engine.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
