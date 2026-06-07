FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY agents/experiment-agent/ ./agents/experiment-agent/
WORKDIR /app/agents/experiment-agent
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health')"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
