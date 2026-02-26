# HR Employee Search Microservice
# Python 3.12 slim for Linux/Unix
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

# Install production deps (exclude pytest etc. for smaller image)
RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]"

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
