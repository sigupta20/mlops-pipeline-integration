from manufacturing_knn_pipeline import manufacturing_knn_pipeline
from kfp import compiler

compiler.Compiler().compile(
    pipeline_func=manufacturing_knn_pipeline,
    package_path="manufacturing_knn_pipeline.yaml",
)
