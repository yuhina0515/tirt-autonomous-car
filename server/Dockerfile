FROM python:3.12-alpine
WORKDIR /app
COPY ingest.py /app/ingest.py
USER 1000:1000
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
CMD ["python", "ingest.py"]
