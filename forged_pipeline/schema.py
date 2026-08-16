"""Shared data structures for the Forged pipeline."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Shot:
    id: str
    scene: str
    visual: str
    audio: str
    tool: str  # "wan_video" | "flux_still" | "editorial"
    prompt: str
    dialogue: Optional[str] = None
    speaker: Optional[str] = None
    reference_image: Optional[str] = None
    consistency_note: Optional[str] = None


@dataclass
class ShotList:
    title: str
    shots: list = field(default_factory=list)
    open_questions: list = field(default_factory=list)

    @classmethod
    def from_json(cls, data: dict) -> "ShotList":
        shots = [Shot(**s) for s in data.get("shots", [])]
        return cls(
            title=data.get("title", ""),
            shots=shots,
            open_questions=data.get("open_questions", []),
        )

    def to_json(self) -> dict:
        return {
            "title": self.title,
            "shots": [s.__dict__ for s in self.shots],
            "open_questions": self.open_questions,
        }
