FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "scripts/turntable_tool_api.py", "--address", "D3:36:39:34:5D:29", "--host", "0.0.0.0", "--port", "8000"]
