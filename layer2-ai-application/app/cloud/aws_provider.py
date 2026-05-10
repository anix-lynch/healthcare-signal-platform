"""AWS provider — for AWS-shop deployments (most large US health systems
on Epic-on-AWS, Cerner-on-AWS, or HealthLake-native).

Service mapping:
    Embeddings        → Bedrock Titan Embeddings v2
    Vector store      → OpenSearch with k-NN  OR  Kendra (intelligent search)
    LLM               → Bedrock Claude / Nova / Llama
    Clinical NLP      → Comprehend Medical
    PHI de-id         → Comprehend Medical PHI detection  OR  HealthLake
    Audit log         → CloudWatch / CloudTrail
    HIPAA region      → BAA + dedicated VPC, KMS-encrypted at rest
"""

from .adapter import CloudProvider, Entities, Hit, Vector
from pydantic import BaseModel


class AWSProvider:
    name = "aws"

    def embed(self, texts: list[str]) -> list[Vector]:
        raise NotImplementedError("TODO: bedrock-runtime invoke_model amazon.titan-embed-text-v2")

    def vector_search(self, query: Vector, k: int = 10) -> list[Hit]:
        raise NotImplementedError("TODO: opensearch-py knn_search OR kendra retrieve")

    def llm_complete(self, prompt: str, schema: type[BaseModel]) -> dict:
        raise NotImplementedError("TODO: bedrock-runtime converse with tool_choice for structured output")

    def healthcare_nlp(self, clinical_text: str) -> Entities:
        raise NotImplementedError("TODO: comprehendmedical detect_entities_v2")

    def deidentify(self, phi_text: str) -> str:
        raise NotImplementedError("TODO: comprehendmedical detect_phi → mask")

    def audit_log(self, event: dict) -> None:
        raise NotImplementedError("TODO: boto3 cloudwatchlogs put_log_events")
