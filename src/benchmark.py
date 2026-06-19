from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_advanced import AdvancedAgent
from agent_baseline import BaselineAgent
from config import load_config


@dataclass
class BenchmarkRow:
    agent_name: str
    agent_tokens_only: int
    prompt_tokens_processed: int
    recall_score: float
    response_quality: float
    memory_growth_bytes: int
    compactions: int


def load_conversations(path: Path) -> list[dict[str, Any]]:
    """Student TODO: read JSON conversations from disk."""
    import json
    if not path.exists(): return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def recall_points(answer: str, expected: list[str]) -> float:
    """Student TODO: return 0 / 0.5 / 1 depending on how many expected facts appear."""
    if not expected: return 1.0
    ans = answer.lower()
    found = sum(1 for e in expected if str(e).lower() in ans)
    return found / len(expected)


def heuristic_quality(answer: str, expected: list[str]) -> float:
    """Student TODO: add a lightweight quality score for offline mode."""
    if "tôi không biết" in answer.lower(): return 0.0
    return 1.0


def run_agent_benchmark(agent_name: str, agent, conversations: list[dict[str, Any]], config) -> BenchmarkRow:
    """Student TODO: evaluate one agent over many conversations.

    Pseudocode:
    1. Feed all turns to the agent.
    2. Track `agent tokens only`.
    3. Track `prompt tokens processed`.
    4. Ask recall questions in a fresh thread.
    5. Compute average recall and quality.
    6. Record memory file growth and compaction count.
    """
    total_agent_tokens = 0
    total_prompt_tokens = 0
    total_recall = 0.0
    total_quality = 0.0
    q_count = 0
    max_mem_size = 0
    total_compactions = 0
    
    for conv in conversations:
        user_id = conv.get("user_id", "u1")
        thread_id = conv.get("thread_id", "t1")
        
        for turn_text in conv.get("turns", []):
            agent.reply(user_id, thread_id, turn_text)
        
        new_thread = thread_id + "_q"
        for q in conv.get("recall_questions", []):
            res = agent.reply(user_id, new_thread, q["question"])
            r_pts = recall_points(res["content"], q.get("expected_contains", []))
            total_recall += r_pts
            total_quality += heuristic_quality(res["content"], q.get("expected_contains", []))
            q_count += 1
            
        total_agent_tokens += agent.token_usage(thread_id) + agent.token_usage(new_thread)
        total_prompt_tokens += agent.prompt_token_usage(thread_id) + agent.prompt_token_usage(new_thread)
        
        if hasattr(agent, "memory_file_size"):
            msize = agent.memory_file_size(user_id)
            if msize > max_mem_size: max_mem_size = msize
            
        if hasattr(agent, "compaction_count"):
            total_compactions += agent.compaction_count(thread_id) + agent.compaction_count(new_thread)

    avg_recall = total_recall / q_count if q_count else 0.0
    avg_qual = total_quality / q_count if q_count else 0.0
    
    return BenchmarkRow(
        agent_name=agent_name,
        agent_tokens_only=total_agent_tokens,
        prompt_tokens_processed=total_prompt_tokens,
        recall_score=avg_recall,
        response_quality=avg_qual,
        memory_growth_bytes=max_mem_size,
        compactions=total_compactions
    )


def format_rows(rows: list[BenchmarkRow]) -> str:
    """Student TODO: print a markdown table or tabulated output."""
    from tabulate import tabulate
    headers = ["Agent", "Agent Tokens", "Prompt Tokens Processed", "Recall", "Quality", "Memory Growth (B)", "Compactions"]
    table_data = []
    for r in rows:
        table_data.append([
            r.agent_name, 
            r.agent_tokens_only, 
            r.prompt_tokens_processed, 
            f"{r.recall_score:.2f}", 
            f"{r.response_quality:.2f}", 
            r.memory_growth_bytes, 
            r.compactions
        ])
    return tabulate(table_data, headers=headers, tablefmt="github")


def main() -> None:
    """Student TODO: run both benchmark suites.

    Required benchmark sections:
    - Standard benchmark from `data/conversations.json`
    - Long-context stress benchmark from `data/advanced_long_context.json`

    Compare:
    - Baseline
    - Advanced

    Keep the same output columns as the solved lab:
    - Agent tokens only
    - Prompt tokens processed
    - Cross-session recall
    - Response quality
    - Memory growth (bytes)
    - Compactions
    """

    config = load_config(Path(__file__).resolve().parent.parent)

    # TODO:
    # - load both datasets from root/data
    # - initialize baseline and advanced agents
    # - run benchmarks
    # - print comparison tables
    std_path = config.data_dir / "conversations.json"
    long_path = config.data_dir / "advanced_long_context.json"
    
    std_convs = load_conversations(std_path)
    long_convs = load_conversations(long_path)
    
    if not std_convs and not long_convs:
        print("No data found to benchmark.")
        return

    for suite_name, convs in [("Standard Benchmark", std_convs), ("Long-context Stress Benchmark", long_convs)]:
        if not convs: continue
        
        print(f"\n=== {suite_name} ===")
        
        baseline = BaselineAgent(config, force_offline=True)
        advanced = AdvancedAgent(config, force_offline=True)
        
        r_base = run_agent_benchmark("Baseline", baseline, convs, config)
        r_adv = run_agent_benchmark("Advanced", advanced, convs, config)
        
        print(format_rows([r_base, r_adv]))


if __name__ == "__main__":
    main()
