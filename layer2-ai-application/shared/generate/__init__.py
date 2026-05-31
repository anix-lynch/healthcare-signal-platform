"""Pattern 4 — generation public API."""
from .baseline import generate_note
from .schema import MadLibOutput, GenerationMethod
from .chart_note import generate

__all__ = ["generate_note", "MadLibOutput", "GenerationMethod", "generate"]
