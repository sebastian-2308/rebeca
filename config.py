import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    provider: str = field(default_factory=lambda: os.getenv("REBECA_PROVIDER", os.getenv("GACE_PROVIDER", "openai")))
    model: str = field(default_factory=lambda: os.getenv("REBECA_MODEL", os.getenv("GACE_MODEL", "gpt-4o")))
    api_key: str = field(default_factory=lambda: os.getenv("REBECA_API_KEY", os.getenv("GACE_API_KEY", "")))
    max_turns: int = int(os.getenv("REBECA_MAX_TURNS", os.getenv("GACE_MAX_TURNS", "50")))
    system_prompt: str = field(default_factory=lambda: _default_system_prompt())


WORK_DIR = Path(os.getenv("REBECA_WORK_DIR", os.getenv("GACE_WORK_DIR", os.getcwd())))


def _default_system_prompt() -> str:
    from .prompts import SYSTEM_PROMPT
    return SYSTEM_PROMPT
