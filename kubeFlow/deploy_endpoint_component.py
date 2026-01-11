from kfp.dsl import component, Input, Artifact

@component(
    base_image="gcr.io/deeplearning-platform-release/base-cpu.py310",
    packages_to_install=["google-cloud-aiplatform"],
)
def deploy_model_op(
    project_id: str,
    location: str,
    endpoint_display_name: str,
    model_resource: Input[Artifact],  # ✅ Artifact input
    machine_type: str = "n1-standard-4",
    min_replica_count: int = 1,
    max_replica_count: int = 1,
):
    from google.cloud import aiplatform

    aiplatform.init(project=project_id, location=location)

    # 🔑 READ model resource name from Artifact
    with open(model_resource.path, "r") as f:
        model_name = f.read().strip()

    print("Deploying model:", model_name)

    endpoints = aiplatform.Endpoint.list(
        filter=f'display_name="{endpoint_display_name}"'
    )

    if endpoints:
        endpoint = endpoints[0]
        print("Using existing endpoint:", endpoint.resource_name)
    else:
        endpoint = aiplatform.Endpoint.create(
            display_name=endpoint_display_name
        )
        print("Created new endpoint:", endpoint.resource_name)

    model = aiplatform.Model(model_name)

    endpoint.deploy(
        model=model,
        deployed_model_display_name=f"{endpoint_display_name}-model",
        machine_type=machine_type,
        min_replica_count=min_replica_count,
        max_replica_count=max_replica_count,
        traffic_percentage=100,
        sync=True,
    )

    print("Model deployed successfully")
