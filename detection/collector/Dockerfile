FROM python:3.12-slim
RUN pip install --no-cache-dir "requests==2.32.*"
COPY collector.py /app/collector.py
CMD ["python", "-u", "/app/collector.py"]
