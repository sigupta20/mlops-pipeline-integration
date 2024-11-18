from google.cloud import aiplatform

def undeploy_endpoints(
    display_name: str, 
    project: str,
    location: str
    ):  
    # Erstellen des Modellobjekts
    aiplatform.init(project=project, location=location)

    # Undeploy all endpoints
    endpoints = aiplatform.Endpoint.list()
    for endpoint in endpoints: 
        endpoint.undeploy_all()