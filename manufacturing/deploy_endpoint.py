from google.cloud import aiplatform

def deploy_endpoint(
        project,
        location,
        model_name: str,
        endpoint_display_name: str
    ):
    aiplatform.init(project=project, location=location)

    endpoint = aiplatform.Endpoint.list(
            filter=f"display_name={endpoint_display_name}"
        )

    model = aiplatform.Model(model_name=model_name)
    model.deploy(
            endpoint=endpoint[0],
            deployed_model_display_name=model_name,
            min_replica_count=1,
            max_replica_count=1,
            traffic_percentage=100,
            machine_type='n1-standard-4',
        )

    model.wait()

    print(model.display_name)
    print(model.resource_name)
    return model