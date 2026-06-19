from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def estimate_tokens(text: str) -> int:
    """Student TODO: implement a simple token estimator.

    Example idea:
    - Strip whitespace
    - Return 0 for empty text
    - Approximate tokens from character count, e.g. len(text) / 4
    """
    text = text.strip()
    if not text:
        return 0
    return max(1, len(text) // 4)


@dataclass
class UserProfileStore:
    """Persistent storage for `User.md`.

    Student TODO:
    - Map each user id to one markdown file
    - Support read / write / edit operations
    - Optionally expose helpers like `facts()` or `upsert_fact()`
    """

    root_dir: Path

    def path_for(self, user_id: str) -> Path:
        # TODO: slugify or sanitize the user id before building the file path.
        safe_id = "".join(c if c.isalnum() else "_" for c in user_id)
        return self.root_dir / f"{safe_id}.md"

    def read_text(self, user_id: str) -> str:
        # TODO: return file content or an empty default markdown profile.
        path = self.path_for(user_id)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def write_text(self, user_id: str, content: str) -> Path:
        # TODO: write markdown to disk and return the file path.
        path = self.path_for(user_id)
        path.write_text(content, encoding="utf-8")
        return path

    def edit_text(self, user_id: str, search_text: str, replacement: str) -> bool:
        # TODO: replace one occurrence inside User.md and return whether it changed.
        path = self.path_for(user_id)
        if not path.exists():
            return False
        content = path.read_text(encoding="utf-8")
        if search_text in content:
            new_content = content.replace(search_text, replacement, 1)
            path.write_text(new_content, encoding="utf-8")
            return True
        return False

    def file_size(self, user_id: str) -> int:
        # TODO: return the current file size in bytes.
        path = self.path_for(user_id)
        return path.stat().st_size if path.exists() else 0


def extract_profile_updates(message: str) -> dict[str, str]:
    """Student TODO: convert raw user text into stable profile facts.

    Example facts you may want to extract:
    - name
    - location
    - profession
    - preferences / response style
    - favorite food / drink

    Pseudocode:
    1. Build a few regex patterns.
    2. Skip obvious question-only turns.
    3. Return only the facts that are confidently present in the message.
    """
    import re
    facts = {}
    lower_msg = message.lower()
    
    if "?" in message:
        return facts # simple heuristic: skip questions

    m = re.search(r'(?:tên tôi là|tôi là|gọi tôi là|tên là) ([\w\s]+)', lower_msg)
    if m: facts['name'] = m.group(1).strip()
    
    m = re.search(r'(?:tôi sống ở|ở|đến từ|sống tại) ([\w\s]+)', lower_msg)
    if m: facts['location'] = m.group(1).strip()
    
    m = re.search(r'(?:tôi làm|tôi là một|nghề của tôi là) ([\w\s]+)', lower_msg)
    if m:
        val = m.group(1).strip()
        if val not in ['người', 'ai']:
            facts['profession'] = val

    m = re.search(r'(?:tôi thích|tôi muốn bạn|hãy|nên) ([\w\s]+)', lower_msg)
    if m: facts['preference'] = m.group(1).strip()

    return facts


def summarize_messages(messages: list[dict[str, str]], max_items: int = 6) -> str:
    """Student TODO: create a compact summary of older messages.

    This can be heuristic text concatenation first.
    Later, you can replace it with an LLM-based summary if desired.
    """
    if not messages: return ""
    return f"Đã thảo luận về {len(messages)} tin nhắn trước đó."


@dataclass
class CompactMemoryManager:
    """Student TODO: implement compact memory for long threads.

    Goal:
    - Keep recent messages in full
    - When the thread grows too large, move older content into a summary
    - Track how many compactions happened for benchmarking
    """

    threshold_tokens: int
    keep_messages: int
    state: dict[str, dict[str, object]] = field(default_factory=dict)

    def append(self, thread_id: str, role: str, content: str) -> None:
        # TODO:
        # 1. create thread state if missing
        # 2. append the new message
        # 3. trigger compaction if needed
        if thread_id not in self.state:
            self.state[thread_id] = {
                "messages": [],
                "summary": "",
                "compactions": 0
            }
        
        st = self.state[thread_id]
        msgs = st["messages"]
        msgs.append({"role": role, "content": content})
        
        total_tokens = sum(estimate_tokens(m["content"]) for m in msgs)
        if st["summary"]:
            total_tokens += estimate_tokens(st["summary"])
            
        if total_tokens > self.threshold_tokens and len(msgs) > self.keep_messages:
            old_msgs = msgs[:-self.keep_messages]
            new_msgs = msgs[-self.keep_messages:]
            
            new_summary = summarize_messages(old_msgs)
            if st["summary"]:
                st["summary"] += "\n" + new_summary
            else:
                st["summary"] = new_summary
                
            st["messages"] = new_msgs
            st["compactions"] += 1

    def context(self, thread_id: str) -> dict[str, object]:
        # TODO: return per-thread state with keys like messages, summary, compactions.
        if thread_id not in self.state:
            return {"messages": [], "summary": "", "compactions": 0}
        return self.state[thread_id]

    def compaction_count(self, thread_id: str) -> int:
        # TODO: return number of compactions for this thread.
        return self.context(thread_id).get("compactions", 0)
