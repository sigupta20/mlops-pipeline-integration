FROM europe-west3-docker.pkg.dev/mlops-pipeline-01/mlops-build/mlops-build:1.0.1

WORKDIR /app

# # Install dependencies
# COPY app/requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Make "app" importable
ENV PYTHONPATH=/app

EXPOSE 8080
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
