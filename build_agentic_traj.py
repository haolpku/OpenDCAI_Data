"""
Build an 'Agentic 轨迹合成' category for the OpenDCAI_Data showcase site from
DataFlow-Agent's real synthesized trajectories (cache/), and inject it into
data.js (window.DB.catalog + window.DB.samples).

Idempotent: re-running replaces the agentic_traj category/samples in place.

Usage:
    python build_agentic_traj.py            # uses DataFlow-Agent/cache
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_JS = os.path.join(HERE, "data.js")
CACHE = os.path.abspath(os.path.join(HERE, "..", "DataFlow-Agent", "cache"))

KEY = "agentic_traj"


def _load_jsonl(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _as_obj(v):
    if isinstance(v, str):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return None
    return v


def _render_steps(traj):
    """Flatten a trajectory's steps into a readable list for the site."""
    out = []
    for i, st in enumerate(traj.get("steps") or [], 1):
        act = st.get("action") or {}
        out.append({
            "step": i,
            "thought": st.get("thought"),
            "tool": act.get("tool"),
            "args": act.get("args", {}),
            "observation": st.get("observation"),
        })
    return out


def build_samples():
    """Pull real trajectories from the eval'd cache step (has quality scores)."""
    samples = []

    # Main pipeline: step2 = trajectories + judge scores (traj_overall etc.)
    rows = _load_jsonl(os.path.join(CACHE, "dataflow_cache_step_step2.jsonl"))
    for r in rows:
        traj = _as_obj(r.get("trajectory"))
        if not traj:
            continue
        samples.append({
            "task": traj.get("task"),
            "domain": "mock / 知识检索",
            "success": "是" if traj.get("success") else "否",
            "num_steps": traj.get("num_steps"),
            "final_answer": traj.get("final_answer"),
            "overall_score": r.get("traj_overall"),
            "goal_achievement": r.get("traj_goal_achievement"),
            "efficiency": r.get("traj_efficiency"),
            "coherence": r.get("traj_coherence"),
            "tool_use": r.get("traj_tool_use"),
            "judge_rationale": r.get("traj_rationale"),
            "steps": _render_steps(traj),
        })

    # Tree generator: show one branching-tree sample (paths flattened)
    tree_rows = _load_jsonl(os.path.join(CACHE, "tree", "dataflow_cache_step_step1.jsonl"))
    for r in tree_rows[:1]:
        tree = _as_obj(r.get("tree"))
        if not tree:
            continue
        samples.append({
            "task": tree.get("task"),
            "domain": "探索树 (branching)",
            "success": "是" if tree.get("num_success_paths") else "否",
            "num_nodes": tree.get("num_nodes"),
            "num_paths": tree.get("num_paths"),
            "num_success_paths": tree.get("num_success_paths"),
            "final_answer": (tree.get("paths") or [{}])[0].get("final_answer"),
            "tree_paths": [
                {"success": p.get("success"), "num_steps": p.get("num_steps"),
                 "final_answer": p.get("final_answer"), "steps": _render_steps(p)}
                for p in (tree.get("paths") or [])
            ],
        })

    # Coding agent: real bug-fix trajectory in a live workspace (file ops +
    # pytest). step2 has the judge scores too.
    coding_rows = _load_jsonl(os.path.join(CACHE, "coding", "dataflow_cache_step_step2.jsonl"))
    for r in coding_rows:
        traj = _as_obj(r.get("trajectory"))
        if not traj:
            continue
        samples.append({
            "task": traj.get("task"),
            "domain": "Coding Agent (真实工作区 + pytest)",
            "success": "是" if traj.get("success") else "否",
            "num_steps": traj.get("num_steps"),
            "final_answer": traj.get("final_answer"),
            "overall_score": r.get("traj_overall"),
            "goal_achievement": r.get("traj_goal_achievement"),
            "efficiency": r.get("traj_efficiency"),
            "coherence": r.get("traj_coherence"),
            "tool_use": r.get("traj_tool_use"),
            "judge_rationale": r.get("traj_rationale"),
            "steps": _render_steps(traj),
        })

    return samples


CATALOG_ENTRY = {
    "key": KEY,
    "title": "Agentic 轨迹合成 (DataFlow-Agent)",
    "cat": "Agent",
    "color": "#7c6cff",
    "desc": ("DataFlow-Agent 合成的智能体探索轨迹:LLM 在沙箱中 多步『思考→调用工具→"
             "观察』直到给出答案,经 LLM-as-judge 四维打分(目标达成/效率/连贯性/工具使用)"
             "并过滤。下方为真实跑出的样本,含线性轨迹与分支探索树。生成→评估→过滤→修复闭环。"),
    "kind": "text",
    "count": 0,  # filled in below
    "labels": {
        "task": "任务",
        "domain": "环境/类型",
        "success": "是否成功",
        "num_steps": "步数",
        "num_nodes": "树节点数",
        "num_paths": "路径数",
        "num_success_paths": "成功路径数",
        "final_answer": "最终答案",
        "overall_score": "综合质量分(0-1)",
        "goal_achievement": "目标达成(1-5)",
        "efficiency": "效率(1-5)",
        "coherence": "连贯性(1-5)",
        "tool_use": "工具使用(1-5)",
        "judge_rationale": "裁判评语",
        "steps": "探索步骤(思考/工具/观察)",
        "tree_paths": "探索树各路径",
    },
}


def inject(samples):
    with open(DATA_JS, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^\s*window\.DB\s*=\s*(\{.*\})\s*;?\s*$", text, re.DOTALL)
    if not m:
        raise SystemExit("data.js not in expected 'window.DB={...}' form")
    db = json.loads(m.group(1))

    entry = dict(CATALOG_ENTRY)
    entry["count"] = len(samples)

    # upsert catalog entry
    db["catalog"] = [c for c in db["catalog"] if c.get("key") != KEY]
    db["catalog"].append(entry)
    # upsert samples
    db.setdefault("samples", {})[KEY] = samples

    new_text = "window.DB=" + json.dumps(db, ensure_ascii=False) + ";\n"
    with open(DATA_JS, "w", encoding="utf-8") as f:
        f.write(new_text)
    return len(samples), len(db["catalog"])


if __name__ == "__main__":
    samples = build_samples()
    n, ncat = inject(samples)
    print(f"injected {n} '{KEY}' samples; catalog now has {ncat} categories.")
    for s in samples:
        print(f"  - [{s['domain']}] {str(s['task'])[:50]}  steps/paths shown")
