FROM python:3.10-slim

WORKDIR /app

COPY trainer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY trainer/train.py .

ENTRYPOINT ["python", "train.py"]
