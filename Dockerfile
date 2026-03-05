FROM europe-west1-docker.pkg.dev/mlops-pipeline-01/mlops-build/mlops-build:1.0.1

WORKDIR /app
COPY app ./app

# Make app importable
ENV PYTHONPATH=/app

EXPOSE 8080
CMD ["streamlit", "run", "app/streamlit.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
