from kfp import dsl
from extract_data_component import extract_data_op
from prepare_data_component import prepare_data_op
from train_knn_component import train_knn_op
from evaluate_model_component import evaluate_model_op
from upload_model_component import upload_model_op
from deploy_endpoint_component import deploy_model_op


@dsl.pipeline(
    name="manufacturing-knn-training",
    description="MLOps automated pipeline for training, evaluation and deployment",
)
def manufacturing_knn_pipeline(
    project_id: str,
    location: str,
    bucket_name: str,
    endpoint_display_name: str = "knn-endpoint",
    model_display_name: str = "knn-model",
    f1_threshold: float = 0.9,
):

    # 1️⃣ Extract data
    extract_task = extract_data_op(
        bucket_name=bucket_name
    )
    extract_task.set_caching_options(False)

    # 2️⃣ Prepare data
    prepare_task = prepare_data_op(
        raw_data=extract_task.outputs["raw_data"]
    )
    prepare_task.set_caching_options(False)

    # 3️⃣ Train model
    train_task = train_knn_op(
        prepared_data=prepare_task.outputs["prepared_data"],
    )
    train_task.set_caching_options(False)

    # 4️⃣ Evaluate model
    evaluate_task = evaluate_model_op(
        model=train_task.outputs["model"],
        prepared_data=prepare_task.outputs["prepared_data"],
        f1_threshold=f1_threshold,
    )
    evaluate_task.set_caching_options(False)

    # 5️⃣ Conditional deployment
    with dsl.Condition(evaluate_task.outputs["deploy_decision"] == "true"):

        # 6️⃣ Upload model
        upload_task = upload_model_op(
            project_id=project_id,
            location=location,
            model=train_task.outputs["model"],
            display_name=model_display_name,
        )

        # 7️⃣ Deploy model
        deploy_model_op(
            project_id=project_id,
            location=location,
            endpoint_display_name=endpoint_display_name,
            model_resource=upload_task.outputs["model_resource"],
        )
