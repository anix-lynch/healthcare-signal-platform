"""Vertex AI provider (default for ER3 — uses Bchan's $900 GCP credit).

Service mapping:
    Embeddings        → Vertex `textembedding-gecko` / `text-embedding-005`
    Vector store      → Vertex Vector Search (formerly Matching Engine)
    LLM               → Gemini 2.5 Pro / Flash · or Anthropic via Vertex
    Clinical NLP      → Healthcare Natural Language API
    PHI de-id         → Healthcare API DLP
    Audit log         → Cloud Logging
    HIPAA region      → us-central1 with BAA enabled
"""

from .adapter import CloudProvider, Entities, Hit, Vector
from pydantic import BaseModel


class VertexProvider:
    name = "vertex"

    def embed(self, texts: list[str]) -> list[Vector]:
        raise NotImplementedError("TODO: vertexai.language_models.TextEmbeddingModel")

    def vector_search(self, query: Vector, k: int = 10) -> list[Hit]:
        raise NotImplementedError("TODO: aiplatform.MatchingEngineIndexEndpoint.find_neighbors")

    def llm_complete(self, prompt: str, schema: type[BaseModel]) -> dict:
        raise NotImplementedError("TODO: AnthropicVertex client OR vertexai.GenerativeModel + structured output")

    def healthcare_nlp(self, clinical_text: str) -> Entities:
        raise NotImplementedError("TODO: googleapiclient discovery for healthcare.v1 NLP")

    def deidentify(self, phi_text: str) -> str:
        raise NotImplementedError("TODO: Healthcare API DLP deidentify endpoint")

    def audit_log(self, event: dict) -> None:
        raise NotImplementedError("TODO: google.cloud.logging Client")
