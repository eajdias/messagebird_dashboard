# ============================================================
# Dockerfile - Backend API (Python 3.14)
# ============================================================

FROM python:3.14-slim AS base

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || \
    pip install --no-cache-dir \
    fastapi>=0.139.0 uvicorn[standard]>=0.51.0 \
    pydantic>=2.13.4 pydantic-settings>=2.13.0 \
    "python-jose[cryptography]>=3.5.0" "passlib[bcrypt]>=1.7.4" \
    asyncpg>=0.31.0 "sqlalchemy[asyncio]>=2.0.51" alembic>=1.18.5 \
    "pydantic[email]" python-dotenv pyyaml httpx apscheduler \
    xlsxwriter fpdf2

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://127.0.0.1:8000/api/v1/admin/health').raise_for_status()"

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
