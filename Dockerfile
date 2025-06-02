FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.7.2 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1

ENV UV_LINK_MODE=copy

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*


# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# Create alembic directory if it doesn't exist
# RUN mkdir -p alembic/versions

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Default command (can be overridden in docker-compose)
CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]
