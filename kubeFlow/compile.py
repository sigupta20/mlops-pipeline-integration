from pipeline import pipeline
from kfp import compiler

compiler.Compiler().compile(
    pipeline_func=pipeline,
    package_path="pipeline.yaml",
)
