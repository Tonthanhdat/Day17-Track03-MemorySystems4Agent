from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from config import LabConfig, load_config
from memory_store import estimate_tokens
from model_provider import build_chat_model


@dataclass
class SessionState:
    messages: list[dict[str, str]] = field(default_factory=list)
    token_usage: int = 0
    prompt_tokens_processed: int = 0


class BaselineAgent:
    """Student TODO: implement Agent A.

    Requirements:
    - Within-session memory only
    - No persistent `User.md`
    - Should forget long-term facts across new threads
    """

    def __init__(self, config: LabConfig | None = None, force_offline: bool = False) -> None:
        self.config = config or load_config()
        self.force_offline = force_offline
        self.sessions: dict[str, SessionState] = {}

        # TODO: optionally initialize a real LangChain/LangGraph agent when dependencies exist.
        self.langchain_agent = None

    def reply(self, user_id: str, thread_id: str, message: str) -> dict[str, Any]:
        """Student TODO: return the agent response and token accounting.

        Pseudocode:
        - If a live agent exists, call the live path.
        - Otherwise use a deterministic offline path.
        """
        if self.langchain_agent and not self.force_offline:
            pass # Real agent not fully implemented for lab simplicity, defaulting to offline
        return self._reply_offline(thread_id, message)

    def token_usage(self, thread_id: str) -> int:
        # TODO: return cumulative agent token count for one thread.
        if thread_id not in self.sessions: return 0
        return self.sessions[thread_id].token_usage

    def prompt_token_usage(self, thread_id: str) -> int:
        # TODO: estimate how much prompt context this baseline kept processing.
        if thread_id not in self.sessions: return 0
        return self.sessions[thread_id].prompt_tokens_processed

    def compaction_count(self, thread_id: str) -> int:
        # Baseline has no compact memory.
        return 0

    def _reply_offline(self, thread_id: str, message: str) -> dict[str, Any]:
        """Student TODO: implement a simple offline behavior.

        Suggested behavior:
        - Store the new user message in the session
        - Generate a short deterministic reply
        - Update token counts
        - Never remember facts across different thread ids
        """
        if thread_id not in self.sessions:
            self.sessions[thread_id] = SessionState()
        
        state = self.sessions[thread_id]
        
        # calculate prompt tokens processed for this turn
        prompt_tokens = estimate_tokens(message) + sum(estimate_tokens(m["content"]) for m in state.messages)
        state.prompt_tokens_processed += prompt_tokens
        
        state.messages.append({"role": "user", "content": message})
        
        # simple deterministic reply based on short-term memory (this thread only)
        lower_msg = message.lower()
        if "tên tôi là gì" in lower_msg:
            # check thread history
            found = False
            for m in reversed(state.messages):
                if "tên tôi là" in m["content"].lower():
                    parts = m["content"].lower().split("tên tôi là")
                    if len(parts) > 1:
                        reply_text = f"Tên của bạn là {parts[1].strip()}."
                        found = True
                        break
            if not found:
                reply_text = "Tôi không biết tên của bạn."
        elif "sống ở đâu" in lower_msg:
            found = False
            for m in reversed(state.messages):
                if "sống ở" in m["content"].lower():
                    parts = m["content"].lower().split("sống ở")
                    if len(parts) > 1:
                        reply_text = f"Bạn sống ở {parts[1].strip()}."
                        found = True
                        break
            if not found:
                reply_text = "Tôi không biết bạn sống ở đâu."
        elif "làm nghề gì" in lower_msg:
            found = False
            for m in reversed(state.messages):
                if "làm nghề" in m["content"].lower():
                    parts = m["content"].lower().split("làm nghề")
                    if len(parts) > 1:
                        reply_text = f"Bạn làm nghề {parts[1].strip()}."
                        found = True
                        break
            if not found:
                reply_text = "Tôi không biết bạn làm nghề gì."
        else:
            reply_text = "Đã ghi nhận thông tin trong thread này."
            
        state.messages.append({"role": "agent", "content": reply_text})
        reply_tokens = estimate_tokens(reply_text)
        state.token_usage += reply_tokens
        
        return {
            "content": reply_text,
            "agent_tokens": reply_tokens,
            "prompt_tokens_processed": prompt_tokens
        }

    def _maybe_build_langchain_agent(self):
        """Student TODO: optionally wire `create_agent` + `InMemorySaver` here.

        Use `build_chat_model(self.config.model)` so the baseline can run with any supported provider.
        """
        if not self.force_offline:
            pass # Can integrate LangGraph here if needed
