from google.cloud import aiplatform


print("Define variables for the project")
PROJECT_ID = "mlops-pipeline-01"
REGION = "europe-west1"
ENDPOINT_NAME = "knn-endpoint"
DEPLOYED_MODEL_NAME = "knn-v1"

def create_endpoint(
    display_name: str, 
    project: str,
    location: str,
    deployed_model_display_name: str
    ):  
    # init VertexAI
    aiplatform.init(project=project, location=location)

    # Create Endpoint
    endpoint = aiplatform.Endpoint.create(
            display_name=display_name,
            project=project,
            location=location,
        )
    
    model_name = "projects/71707089683/locations/europe-west1/models/2492392749051936768"
    
    model = aiplatform.Model(model_name=model_name)

    model.deploy(
            endpoint=endpoint,
            deployed_model_display_name=deployed_model_display_name,
            min_replica_count=1,
            max_replica_count=1,
            traffic_percentage=100,
            machine_type='n1-standard-4',
            sync=True
        )

    model.wait()

    print("Endpoint: ", endpoint.list_models())

    return endpoint.display_name

if __name__ == "__main__":
    create_endpoint(
        display_name=ENDPOINT_NAME,
        project=PROJECT_ID,
        location=REGION,
        deployed_model_display_name=DEPLOYED_MODEL_NAME
    )