                                                                             Dockerfile
# syntax=docker/dockerfile:1

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies (ffmpeg for audio/video processing)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . .

RUN chmod +x ./entrypoint.sh
RUN chmod +x ./bin/rhubarb
RUN chmod +x ./bin/rhubarb

EXPOSE 4000

# Default command (PORT can be overridden at runtime)
CMD ["/bin/sh", "-c", "./entrypoint.sh"]

