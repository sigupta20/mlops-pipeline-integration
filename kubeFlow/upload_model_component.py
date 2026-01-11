from kfp.dsl import component, Input, Output, Artifact, Model

@component(
    base_image="gcr.io/deeplearning-platform-release/base-cpu.py310",
    packages_to_install=["google-cloud-aiplatform"],
)
def upload_model_op(
    project_id: str,
    location: str,
    model: Input[Model],
    display_name: str,
    model_resource: Output[Artifact],
):
    from google.cloud import aiplatform

    aiplatform.init(project=project_id, location=location)

    artifact_uri = model.path

    # ✅ ALWAYS use a SERVING container
    serving_container_image_uri = (
        "europe-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest"
    )

    existing_models = aiplatform.Model.list(
        filter=f'display_name="{display_name}"'
    )

    if existing_models:
        uploaded_model = aiplatform.Model.upload(
            display_name=display_name,
            parent_model=existing_models[0].resource_name,
            artifact_uri=artifact_uri,
            serving_container_image_uri=serving_container_image_uri,
        )
        print("Uploaded new model version")
    else:
        uploaded_model = aiplatform.Model.upload(
            display_name=display_name,
            artifact_uri=artifact_uri,
            serving_container_image_uri=serving_container_image_uri,
        )
        print("Uploaded new model")

    with open(model_resource.path, "w") as f:
        f.write(uploaded_model.resource_name)

    print("Model resource:", uploaded_model.resource_name)
