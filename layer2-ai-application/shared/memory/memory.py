"""Memory — multi-turn state for triage sessions.

Three tiers of memory (don't bolt them all together):

    SHORT-TERM       within-session, last N turns
                     "what did the nurse just type 3 messages ago?"
                     storage: in-process dict / Redis with TTL

    SESSION          one ER visit, multi-turn conversation
                     "what's been said about THIS patient today?"
                     storage: Firestore / Cosmos DB / DynamoDB
                              keyed by session_id

    LONG-TERM        cross-session, persistent
                     "this patient was here last week — what happened?"
                     storage: Vector store (case embeddings)
                              + structured DB (visit history)

Each memory tier has its own retention + audit policy. PHI in any tier
goes through the same redaction layer as input_guardrails.

🛡️ COMPLIANCE pillar evidence — auditable retention, scoped access.
🤖 INNOVATION pillar evidence — agent-friendly, each tier exposes a
   stable API agents can call without auth-hell.
"""

from typing import Protocol


class ShortTermMemory(Protocol):
    def append(self, session_id: str, message: dict) -> None: ...
    def last_n(self, session_id: str, n: int = 10) -> list[dict]: ...
    def clear(self, session_id: str) -> None: ...


class SessionMemory(Protocol):
    def create(self, session_id: str, patient_id: str, metadata: dict) -> None: ...
    def get(self, session_id: str) -> dict: ...
    def append_event(self, session_id: str, event: dict) -> None: ...
    def close(self, session_id: str, outcome: dict) -> None: ...


class LongTermMemory(Protocol):
    def write_visit(self, patient_id: str, visit_summary: dict) -> str: ...
    def get_history(self, patient_id: str, k: int = 5) -> list[dict]: ...
    def search_similar_visits(self, query_embedding, k: int = 10) -> list[dict]: ...


class TriageMemory:
    """Composite memory facade — all three tiers behind one interface.

    Production wiring will fan out to the active CloudProvider's storage
    primitives (Firestore / Cosmos / DynamoDB + Vector Search).
    """

    def __init__(self, short_term: ShortTermMemory, session: SessionMemory,
                 long_term: LongTermMemory) -> None:
        self.short = short_term
        self.session = session
        self.long = long_term

    def remember_turn(self, session_id: str, role: str, content: str) -> None:
        raise NotImplementedError("TODO: write to short-term + session, conditionally long-term")

    def recall_context(self, session_id: str, patient_id: str) -> dict:
        """Build the LLM prompt context: short-term + session-summary + relevant
        long-term history."""
        raise NotImplementedError("TODO: gather across 3 tiers, return prompt-ready dict")
