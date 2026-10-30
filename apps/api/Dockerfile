FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "fastapi==0.115.*" "uvicorn[standard]==0.32.*" "pyjwt[crypto]==2.9.*"
COPY main.py .
USER nobody
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
