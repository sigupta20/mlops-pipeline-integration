from google.cloud import aiplatform

def upload_model(
    display_name: str, 
    project: str,
    location: str,
    bucket_name: str,
    container_image_uri: str
    ):  
    # # Call URI of artifact
    artifact_uri = f"gs://{bucket_name}/"

    # Init VertexAI
    aiplatform.init(project=project, location=location)

    models = aiplatform.Model.list(filter=("display_name={}").format(display_name))

    if len(models) == 0:
        model_upload = aiplatform.Model.upload(
            display_name = display_name ,
            artifact_uri=artifact_uri,
            serving_container_image_uri=container_image_uri
        ) 
        print("Model uploaded:", model_upload.resource_name)
        return model_upload.resource_name
    else:
        # If already exists, model versioning
        parent_model = models[0].resource_name   
        model_upload = aiplatform.Model.upload(
            display_name = display_name,
            parent_model = parent_model  ,
            artifact_uri=artifact_uri,
            serving_container_image_uri=container_image_uri     
        )
        print("Model uploaded:", model_upload.resource_name)
        return model_upload.resource_name