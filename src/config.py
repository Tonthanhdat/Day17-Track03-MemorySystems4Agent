from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

from model_provider import ProviderConfig


@dataclass
class LabConfig:
    """Student TODO: define the shared configuration for the lab.

    Hints:
    - Keep paths for the repo root, dataset directory, and state directory.
    - Add compact-memory settings such as threshold and number of messages to keep.
    - Add provider settings for `openai`, `custom`, `gemini`, `anthropic`, `ollama`, and `openrouter`.
    """

    base_dir: Path
    data_dir: Path
    state_dir: Path
    compact_threshold_tokens: int
    compact_keep_messages: int
    model: ProviderConfig
    judge_model: ProviderConfig


def load_config(base_dir: Path | None = None) -> LabConfig:
    """Student TODO: load environment variables and return a LabConfig.

    Pseudocode:
    1. Resolve the repo root or default to the current file parent.
    2. Optionally load values from `.env`.
    3. Create `state/` if it does not exist.
    4. Return a populated LabConfig instance.
    """

    root = (base_dir or Path(__file__).resolve().parent.parent).resolve()

    # TODO: read env vars for one of the supported providers.
    # Example knobs:
    # - LLM_PROVIDER / LLM_MODEL
    # - OPENAI_API_KEY
    # - GEMINI_API_KEY
    # - ANTHROPIC_API_KEY
    # - OLLAMA_BASE_URL
    # - OPENROUTER_API_KEY
    # - CUSTOM_BASE_URL / CUSTOM_API_KEY
    load_dotenv(root / ".env")
    
    # We will use OpenAI by default since the user provided an OpenAI key.
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_temp = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    
    provider_config = ProviderConfig(provider=llm_provider, model_name=llm_model, temperature=llm_temp)

    # TODO: create `root / "state"`.
    state_dir = root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    # TODO: choose sensible defaults for compact memory.
    compact_threshold_tokens = 2000
    compact_keep_messages = 4

    return LabConfig(
        base_dir=root,
        data_dir=root / "data",
        state_dir=state_dir,
        compact_threshold_tokens=compact_threshold_tokens,
        compact_keep_messages=compact_keep_messages,
        model=provider_config,
        judge_model=provider_config
    )
