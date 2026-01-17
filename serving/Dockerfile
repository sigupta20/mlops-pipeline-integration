FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    scikit-learn \
    joblib \
    numpy

COPY app.py /app/app.py

# Vertex mounts model artifacts here
ENV MODEL_PATH=/model/model.joblib

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
