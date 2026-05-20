FROM python:3.14-slim

# Install uv
RUN pip install uv --no-cache-dir

# Non-root user matching prod (uid=1000)
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Store model cache inside /app so the named volume in docker-compose
# can shadow it cleanly (model_cache:/app/.cache/huggingface)
ENV HF_HOME=/app/.cache/huggingface

# Install dependencies first (layer cache friendly).
# --no-install-project: skip editable install of the project itself —
# source code is not fully present at this layer; it will be mounted
# at runtime via the docker-compose volume.
COPY pyproject.toml uv.lock ./
# --frozen: skip resolution, install exactly what's in uv.lock (faster + reproducible).
# --mount=type=cache keeps downloaded wheels on the build host between rebuilds.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy source (mounted as volume in dev, so changes are reflected via --reload)
COPY . .

# Give appuser ownership of the venv and any copied files
RUN mkdir -p /app/.cache/huggingface && chown -R appuser:appuser /app

USER appuser

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "src"]
