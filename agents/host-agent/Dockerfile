FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY agents/host-agent/ ./agents/host-agent/
WORKDIR /app/agents/host-agent
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
