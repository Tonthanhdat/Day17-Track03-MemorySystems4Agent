from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config import LabConfig, load_config
from memory_store import CompactMemoryManager, UserProfileStore, estimate_tokens, extract_profile_updates
from model_provider import build_chat_model


@dataclass
class AgentContext:
    user_id: str
    memory_path: str


class AdvancedAgent:
    """Student TODO: implement Agent B / Advanced Agent.

    Required memory layers:
    1. within-session memory
    2. persistent `User.md`
    3. compact memory for long threads
    """

    def __init__(self, config: LabConfig | None = None, force_offline: bool = False) -> None:
        self.config = config or load_config()
        self.force_offline = force_offline
        
        prof_dir = self.config.state_dir / "profiles"
        prof_dir.mkdir(parents=True, exist_ok=True)
        
        self.profile_store = UserProfileStore(prof_dir)
        self.compact_memory = CompactMemoryManager(
            threshold_tokens=self.config.compact_threshold_tokens,
            keep_messages=self.config.compact_keep_messages,
        )
        self.thread_tokens: dict[str, int] = {}
        self.thread_prompt_tokens: dict[str, int] = {}

        # TODO: optionally initialize a real LangChain/LangGraph agent.
        self.langchain_agent = None

    def reply(self, user_id: str, thread_id: str, message: str) -> dict[str, Any]:
        """Student TODO: route between offline mode and live mode."""
        if self.langchain_agent and not self.force_offline:
            pass # Use offline mode for simplicity in this lab unless explicitly implemented
        return self._reply_offline(user_id, thread_id, message)

    def token_usage(self, thread_id: str) -> int:
        return self.thread_tokens.get(thread_id, 0)

    def prompt_token_usage(self, thread_id: str) -> int:
        return self.thread_prompt_tokens.get(thread_id, 0)

    def memory_file_size(self, user_id: str) -> int:
        return self.profile_store.file_size(user_id)

    def compaction_count(self, thread_id: str) -> int:
        return self.compact_memory.compaction_count(thread_id)

    def _reply_offline(self, user_id: str, thread_id: str, message: str) -> dict[str, Any]:
        """Student TODO: implement the deterministic advanced path.

        Pseudocode:
        1. Extract stable profile facts from the incoming message.
        2. Persist those facts into `User.md`.
        3. Append the message into compact memory.
        4. Estimate prompt-context load from `User.md` + summary + recent messages.
        5. Generate a response that can answer long-term recall questions.
        6. Append the assistant reply and update token counters.
        """
        facts = extract_profile_updates(message)
        
        if facts:
            current_profile = self.profile_store.read_text(user_id)
            
            # BONUS: Conflict Handling
            # Instead of blindly appending new facts which might cause duplicate or conflicting information 
            # (e.g. user moves from Da Nang to Hanoi), we parse the existing profile and update keys.
            profile_dict = {}
            for line in current_profile.split("\n"):
                line = line.strip()
                if line.startswith("- ") and ":" in line:
                    parts = line[2:].split(":", 1)
                    if len(parts) == 2:
                        profile_dict[parts[0].strip()] = parts[1].strip()
                        
            # Update with new facts (overwriting old ones)
            profile_dict.update(facts)
            
            # Write back the resolved profile
            updated = "\n".join(f"- {k}: {v}" for k, v in profile_dict.items())
            self.profile_store.write_text(user_id, updated)
                
        self.compact_memory.append(thread_id, "user", message)
        
        prompt_tokens = self._estimate_prompt_context_tokens(user_id, thread_id)
        self.thread_prompt_tokens[thread_id] = self.thread_prompt_tokens.get(thread_id, 0) + prompt_tokens
        
        reply_text = self._offline_response(user_id, thread_id, message)
        
        self.compact_memory.append(thread_id, "agent", reply_text)
        reply_tokens = estimate_tokens(reply_text)
        self.thread_tokens[thread_id] = self.thread_tokens.get(thread_id, 0) + reply_tokens
        
        return {
            "content": reply_text,
            "agent_tokens": reply_tokens,
            "prompt_tokens_processed": prompt_tokens
        }

    def _estimate_prompt_context_tokens(self, user_id: str, thread_id: str) -> int:
        """Student TODO: estimate the context carried into one turn.

        Hint:
        - Include `User.md`
        - Include compact summary text
        - Include recent kept messages
        """
        tokens = 0
        profile = self.profile_store.read_text(user_id)
        tokens += estimate_tokens(profile)
        
        ctx = self.compact_memory.context(thread_id)
        if ctx["summary"]:
            tokens += estimate_tokens(str(ctx["summary"]))
            
        for m in ctx["messages"]:
            if isinstance(m, dict) and "content" in m:
                tokens += estimate_tokens(str(m["content"]))
            
        return tokens

    def _offline_response(self, user_id: str, thread_id: str, message: str) -> str:
        """Student TODO: return a deterministic answer using persisted memory.

        Make sure the advanced agent can answer questions like:
        - "Mình tên gì?"
        - "Hiện tại mình làm nghề gì?"
        - "Nhắc lại style trả lời mình thích"
        - questions in the long stress dataset
        """
        lower_msg = message.lower()
        profile = self.profile_store.read_text(user_id).lower()
        ctx = self.compact_memory.context(thread_id)
        
        if "tên tôi là gì" in lower_msg or "tôi là ai" in lower_msg or "mình tên gì" in lower_msg:
            for line in profile.split("\n"):
                if "- name:" in line:
                    return f"Tên của bạn là {line.split('- name:')[1].strip()}."
            for m in reversed(ctx["messages"]):
                if isinstance(m, dict) and "tên tôi là" in m.get("content", "").lower():
                    parts = m["content"].lower().split("tên tôi là")
                    if len(parts) > 1: return f"Tên của bạn là {parts[1].strip()}."
            return "Tôi không biết tên của bạn."
            
        elif "sống ở đâu" in lower_msg:
            for line in profile.split("\n"):
                if "- location:" in line:
                    return f"Bạn sống ở {line.split('- location:')[1].strip()}."
            return "Tôi không biết bạn sống ở đâu."
            
        elif "làm nghề gì" in lower_msg or "công việc của tôi" in lower_msg:
            for line in profile.split("\n"):
                if "- profession:" in line:
                    return f"Bạn làm nghề {line.split('- profession:')[1].strip()}."
            return "Tôi không biết bạn làm nghề gì."
            
        elif "style trả lời" in lower_msg or "thích" in lower_msg or "mong muốn" in lower_msg:
            for line in profile.split("\n"):
                if "- preference:" in line:
                    return f"Bạn thích {line.split('- preference:')[1].strip()}."
            return "Tôi không biết sở thích của bạn."
            
        elif "tóm tắt" in lower_msg or "nhớ" in lower_msg:
            if ctx["summary"]:
                return f"Đây là tóm tắt lịch sử: {ctx['summary']}"
                
        # Additional checks for long context stress tests (assuming they ask about details in thread)
        # We can implement a simple fallback that checks if the summary contains the answer
        return "Đã ghi nhận thông tin."

    def _maybe_build_langchain_agent(self):
        """Student TODO: wire a live agent with tools and compact middleware.

        High-level design:
        - `build_chat_model(self.config.model)` for the selected provider
        - `InMemorySaver` for short-term thread state
        - tool to read `User.md`
        - tool to write/edit `User.md`
        - dynamic prompt that injects profile memory
        - summarization middleware for long threads
        """
        if not self.force_offline:
            pass
