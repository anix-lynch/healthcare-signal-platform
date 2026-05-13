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
🤖 INNOVATION pillar evidence — agent-friendly, stable API per tier.
"""

from typing import Protocol


# ────────────────────────────────────────────────────────────────────────────
# Tier protocols (production implementations inject these)
# ────────────────────────────────────────────────────────────────────────────

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


# ────────────────────────────────────────────────────────────────────────────
# In-memory implementations (zero external deps — swap for cloud backends)
# ────────────────────────────────────────────────────────────────────────────

class InMemoryShortTerm:
    def __init__(self) -> None:
        self._store: dict[str, list[dict]] = {}

    def append(self, session_id: str, message: dict) -> None:
        self._store.setdefault(session_id, []).append(message)

    def last_n(self, session_id: str, n: int = 10) -> list[dict]:
        return self._store.get(session_id, [])[-n:]

    def clear(self, session_id: str) -> None:
        self._store.pop(session_id, None)


class InMemorySession:
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def create(self, session_id: str, patient_id: str, metadata: dict) -> None:
        self._store[session_id] = {"patient_id": patient_id, "events": [], **metadata}

    def get(self, session_id: str) -> dict:
        return self._store.get(session_id, {})

    def append_event(self, session_id: str, event: dict) -> None:
        self._store.setdefault(session_id, {"events": []})["events"].append(event)

    def close(self, session_id: str, outcome: dict) -> None:
        if session_id in self._store:
            self._store[session_id].update({"outcome": outcome, "closed": True})


class InMemoryLongTerm:
    def __init__(self) -> None:
        self._visits: dict[str, list[dict]] = {}

    def write_visit(self, patient_id: str, visit_summary: dict) -> str:
        visits = self._visits.setdefault(patient_id, [])
        visits.append(visit_summary)
        return f"{patient_id}_visit_{len(visits)}"

    def get_history(self, patient_id: str, k: int = 5) -> list[dict]:
        return self._visits.get(patient_id, [])[-k:]

    def search_similar_visits(self, query_embedding, k: int = 10) -> list[dict]:
        # Deterministic fallback: return most recent visits across all patients.
        # Production: swap for vector-store nearest-neighbor search.
        all_visits = [v for visits in self._visits.values() for v in visits]
        return all_visits[-k:]


# ────────────────────────────────────────────────────────────────────────────
# Composite facade
# ────────────────────────────────────────────────────────────────────────────

class TriageMemory:
    """Composite memory facade — all three tiers behind one interface.

    Inject any implementation of the three Protocol types. Default to the
    InMemory* variants for local/test use; swap to cloud backends in prod.
    """

    def __init__(
        self,
        short_term: ShortTermMemory | None = None,
        session: SessionMemory | None = None,
        long_term: LongTermMemory | None = None,
    ) -> None:
        self.short = short_term or InMemoryShortTerm()
        self.session = session or InMemorySession()
        self.long = long_term or InMemoryLongTerm()

    def remember_turn(self, session_id: str, role: str, content: str) -> None:
        """Record one turn in short-term and session memory."""
        msg = {"role": role, "content": content}
        self.short.append(session_id, msg)
        self.session.append_event(session_id, msg)

    def recall_context(self, session_id: str, patient_id: str) -> dict:
        """Build the LLM prompt context dict: short-term + session summary +
        relevant long-term history."""
        return {
            "recent_turns": self.short.last_n(session_id, n=10),
            "session": self.session.get(session_id),
            "long_term_history": self.long.get_history(patient_id, k=5),
        }


# ────────────────────────────────────────────────────────────────────────────
# Convenience factory
# ────────────────────────────────────────────────────────────────────────────

def make_memory() -> TriageMemory:
    """Return a ready-to-use TriageMemory with in-memory backends."""
    return TriageMemory()
