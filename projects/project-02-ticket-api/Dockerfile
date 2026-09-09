FROM python:3.12-slim
WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

# Dependencies first so this layer survives source edits (M2-L20).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
COPY src/ ./src/
RUN pip install --no-cache-dir -e . && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

# NO secrets in this file. Configuration arrives at runtime.
CMD ["uvicorn", "ticketapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
