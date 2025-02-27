FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.6.3 /uv /uvx /bin/


WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*


# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create alembic directory if it doesn't exist
RUN mkdir -p alembic/versions

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Keep container running for debugging
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Command will be specified in docker-compose.yml
