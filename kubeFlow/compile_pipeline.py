from mlops_manufacturing_pipeline import mlops_manufacturing_pipeline
from kfp import compiler

compiler.Compiler().compile(
    pipeline_func=mlops_manufacturing_pipeline,
    package_path="mlops_manufacturing_pipeline.yaml",
)
