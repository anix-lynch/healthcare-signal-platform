"""Azure provider — for Microsoft-shop deployments (Slalom MS / Avanade /
Perficient MS / Epic-on-Azure).

Service mapping:
    Embeddings        → Azure OpenAI text-embedding-3-large
    Vector store      → Azure AI Search (vector profile)
    LLM               → Azure OpenAI GPT-4o / GPT-5
    Clinical NLP      → Azure AI Language (Health Text Analytics)
    PHI de-id         → Azure AI Language (PII detection — health domain)
    Audit log         → Application Insights
    HIPAA region      → BAA-eligible regions, customer-managed keys
"""

from .adapter import CloudProvider, Entities, Hit, Vector
from pydantic import BaseModel


class AzureProvider:
    name = "azure"

    def embed(self, texts: list[str]) -> list[Vector]:
        raise NotImplementedError("TODO: azure.ai.openai.AzureOpenAI client")

    def vector_search(self, query: Vector, k: int = 10) -> list[Hit]:
        raise NotImplementedError("TODO: azure.search.documents SearchClient with vector query")

    def llm_complete(self, prompt: str, schema: type[BaseModel]) -> dict:
        raise NotImplementedError("TODO: AzureOpenAI structured output via response_format")

    def healthcare_nlp(self, clinical_text: str) -> Entities:
        raise NotImplementedError("TODO: TextAnalyticsClient.begin_analyze_healthcare_entities")

    def deidentify(self, phi_text: str) -> str:
        raise NotImplementedError("TODO: TextAnalyticsClient PII detection (health domain)")

    def audit_log(self, event: dict) -> None:
        raise NotImplementedError("TODO: applicationinsights TelemetryClient")
