FROM python:3.10-slim

WORKDIR /app

# Install runtime deps
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    scikit-learn \
    joblib \
    numpy

# Copy serving code
COPY app.py /app/app.py

# Model will be injected at build time
ENV MODEL_PATH=/model/model.joblib

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
