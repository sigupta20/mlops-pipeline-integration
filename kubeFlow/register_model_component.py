from kfp.dsl import component, Input, Output, Model, Artifact

@component(
    base_image="python:3.10",
    packages_to_install=["google-cloud-aiplatform"],
)
def register_model_op(
    project_id: str,
    location: str,
    model: Input[Model],
    display_name: str,
    model_resource: Output[Artifact],
):
    from google.cloud import aiplatform

    aiplatform.init(project=project_id, location=location)

    print(f"Registering model from: {model.path}")

    uploaded_model = aiplatform.Model.upload(
        display_name=display_name,
        artifact_uri=model.path,
        serving_container_image_uri=
        "europe-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest",
        sync=True,
    )

    with open(model_resource.path, "w") as f:
        f.write(uploaded_model.resource_name)

    print("Model registered:", uploaded_model.resource_name)
