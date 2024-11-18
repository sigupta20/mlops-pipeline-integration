from google.cloud import aiplatform

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
    
    model_name = "projects/214116934981/locations/europe-west1/models/2566493235694272512"
    
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