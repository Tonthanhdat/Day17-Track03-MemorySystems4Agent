from __future__ import annotations

from pathlib import Path

from agent_advanced import AdvancedAgent
from agent_baseline import BaselineAgent
from config import load_config


def make_config(tmp_path: Path):
    """Student TODO: build an isolated config for tests."""

    # Hint:
    # - point `state_dir` into tmp_path
    # - reduce compact threshold so compaction happens quickly in tests
    cfg = load_config()
    cfg.state_dir = tmp_path
    cfg.compact_threshold_tokens = 50
    cfg.compact_keep_messages = 2
    return cfg


def test_user_markdown_read_write_edit(tmp_path: Path) -> None:
    """Student TODO: verify `User.md` can be created, updated, and edited."""
    from memory_store import UserProfileStore
    store = UserProfileStore(tmp_path)
    
    path = store.write_text("u1", "Hello World")
    assert path.exists()
    
    txt = store.read_text("u1")
    assert txt == "Hello World"
    
    changed = store.edit_text("u1", "World", "Vietnam")
    assert changed
    assert store.read_text("u1") == "Hello Vietnam"


def test_compact_trigger(tmp_path: Path) -> None:
    """Student TODO: verify long threads trigger compaction."""
    cfg = make_config(tmp_path)
    agent = AdvancedAgent(cfg, force_offline=True)
    
    for i in range(10):
        agent.reply("u1", "t1", f"This is a long message {i} to trigger compaction. It has to be over 50 tokens eventually. Blah blah blah.")
        
    assert agent.compaction_count("t1") > 0


def test_cross_session_recall(tmp_path: Path) -> None:
    """Student TODO: verify advanced remembers across sessions and baseline does not."""
    cfg = make_config(tmp_path)
    base = BaselineAgent(cfg, force_offline=True)
    adv = AdvancedAgent(cfg, force_offline=True)
    
    base.reply("u1", "t1", "Tên tôi là Alice.")
    adv.reply("u1", "t1", "Tên tôi là Alice.")
    
    r_base = base.reply("u1", "t2", "Tên tôi là gì?")
    assert "Alice" not in r_base["content"]
    
    r_adv = adv.reply("u1", "t2", "Tên tôi là gì?")
    assert "alice" in r_adv["content"].lower()


def test_compact_reduces_prompt_load_on_long_thread(tmp_path: Path) -> None:
    """Student TODO: compare prompt load of baseline vs advanced on a long thread."""
    cfg = make_config(tmp_path)
    base = BaselineAgent(cfg, force_offline=True)
    adv = AdvancedAgent(cfg, force_offline=True)
    
    for i in range(20):
        msg = f"Message {i} " * 10
        base.reply("u1", "t1", msg)
        adv.reply("u1", "t1", msg)
        
    assert adv.prompt_token_usage("t1") < base.prompt_token_usage("t1")
