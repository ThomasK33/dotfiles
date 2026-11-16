#!/usr/bin/env python3
"""Create compact analysis artifacts for Mux-style session transcripts."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create chat_index.tsv and devtools_compact.jsonl for RFC synthesis."
    )
    parser.add_argument("session", type=Path, help="Session directory containing chat.jsonl.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to <session>/to-rfc-analysis.",
    )
    parser.add_argument(
        "--preview-chars",
        type=int,
        default=700,
        help="Maximum characters per preview field.",
    )
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def trunc(value: Any, limit: int) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", " ")
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield line_number, json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_number}: invalid JSON: {exc}") from exc


def format_time(timestamp_ms: Any) -> str:
    if not isinstance(timestamp_ms, (int, float)):
        return ""
    return dt.datetime.fromtimestamp(timestamp_ms / 1000, dt.timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


def text_parts(parts: Any) -> str:
    if not isinstance(parts, list):
        return ""
    texts: list[str] = []
    for part in parts:
        if isinstance(part, dict) and (part.get("type") == "text" or "text" in part):
            texts.append(str(part.get("text", "")))
    return "\n".join(texts)


def write_chat_index(session: Path, output_dir: Path, preview_chars: int) -> None:
    chat_path = session / "chat.jsonl"
    require(chat_path.is_file(), f"missing {chat_path}")
    out_path = output_dir / "chat_index.tsv"
    with out_path.open("w", encoding="utf-8") as out:
        out.write("chat_line\thistory_sequence\trole\ttime_utc\tagent\ttext_preview\n")
        for line_number, obj in read_jsonl(chat_path):
            metadata = obj.get("metadata") if isinstance(obj, dict) else {}
            if not isinstance(metadata, dict):
                metadata = {}
            fields = [
                line_number,
                metadata.get("historySequence", ""),
                obj.get("role", "") if isinstance(obj, dict) else "",
                format_time(metadata.get("timestamp")),
                metadata.get("agentId", ""),
                trunc(text_parts(obj.get("parts")) if isinstance(obj, dict) else "", preview_chars),
            ]
            out.write("\t".join(str(field) for field in fields) + "\n")


def summarize_run(line_number: int, obj: dict[str, Any]) -> dict[str, Any]:
    run = obj.get("run") if isinstance(obj.get("run"), dict) else {}
    return {
        "devtools_line": line_number,
        "type": "run",
        "run_id": run.get("id"),
        "workspace_id": run.get("workspaceId"),
        "started_at": run.get("startedAt"),
        "tool_policy_count": len(run.get("toolPolicy") or []),
    }


def summarize_step(line_number: int, obj: dict[str, Any], preview_chars: int) -> dict[str, Any]:
    step = obj.get("step") if isinstance(obj.get("step"), dict) else {}
    step_input = step.get("input") if isinstance(step.get("input"), dict) else {}
    prompt = step_input.get("prompt")
    if isinstance(prompt, list):
        prompt_preview = trunc(" ".join(json.dumps(item, ensure_ascii=False) for item in prompt), preview_chars)
    else:
        prompt_preview = trunc(prompt, preview_chars)
    return {
        "devtools_line": line_number,
        "type": "step",
        "step_id": step.get("id"),
        "run_id": step.get("runId"),
        "step_number": step.get("stepNumber"),
        "started_at": step.get("startedAt"),
        "provider": step.get("provider"),
        "model_id": step.get("modelId"),
        "input_keys": sorted(step_input.keys()),
        "prompt_preview": prompt_preview,
    }


def summarize_step_update(line_number: int, obj: dict[str, Any], preview_chars: int) -> dict[str, Any]:
    update = obj.get("update") if isinstance(obj.get("update"), dict) else {}
    output = update.get("output") if isinstance(update.get("output"), dict) else {}
    tool_calls = []
    for call in output.get("toolCalls") or []:
        if isinstance(call, dict):
            tool_calls.append(
                {
                    "tool_name": call.get("toolName"),
                    "args_preview": trunc(call.get("args"), preview_chars),
                }
            )
    text_preview = text_parts(output.get("textParts"))
    content = output.get("content")
    return {
        "devtools_line": line_number,
        "type": "step-update",
        "step_id": obj.get("stepId"),
        "duration_ms": update.get("durationMs"),
        "finish_reason": output.get("finishReason"),
        "text_preview": trunc(text_preview, preview_chars),
        "content_preview": trunc(json.dumps(content, ensure_ascii=False), preview_chars)
        if content is not None
        else "",
        "tool_calls": tool_calls,
        "tool_call_count": len(tool_calls),
        "reasoning_part_count": len(output.get("reasoningParts") or []),
        "has_error": bool(update.get("error")),
        "usage": update.get("usage"),
    }


def write_devtools_compact(session: Path, output_dir: Path, preview_chars: int) -> None:
    devtools_path = session / "devtools.jsonl"
    if not devtools_path.is_file():
        return
    out_path = output_dir / "devtools_compact.jsonl"
    with out_path.open("w", encoding="utf-8") as out:
        for line_number, obj in read_jsonl(devtools_path):
            if not isinstance(obj, dict):
                summary = {"devtools_line": line_number, "type": "unknown"}
            elif obj.get("type") == "run":
                summary = summarize_run(line_number, obj)
            elif obj.get("type") == "step":
                summary = summarize_step(line_number, obj, preview_chars)
            elif obj.get("type") == "step-update":
                summary = summarize_step_update(line_number, obj, preview_chars)
            else:
                summary = {"devtools_line": line_number, "type": obj.get("type", "unknown")}
            out.write(json.dumps(summary, ensure_ascii=False, sort_keys=True) + "\n")


def write_readme(session: Path, output_dir: Path) -> None:
    files = []
    for path in sorted(session.iterdir()):
        if path.is_file():
            try:
                lines = sum(1 for _ in path.open("rb"))
            except OSError:
                lines = ""
            files.append((path.name, path.stat().st_size, lines))
    with (output_dir / "README.md").open("w", encoding="utf-8") as out:
        out.write("# Transcript analysis artifacts\n\n")
        out.write(f"Source session: `{session}`.\n\n")
        out.write("The raw transcript remains the source of truth.\n\n")
        out.write("## Source files\n\n")
        out.write("| file | bytes | lines |\n|---|---:|---:|\n")
        for name, size, lines in files:
            out.write(f"| `{name}` | {size} | {lines} |\n")
        out.write("\n## Helper files\n\n")
        out.write("- `chat_index.tsv`: one row per chat JSONL entry with line numbers and previews.\n")
        if (output_dir / "devtools_compact.jsonl").exists():
            out.write("- `devtools_compact.jsonl`: observable devtools structure, tool calls, and counts without hidden reasoning text.\n")


def main() -> None:
    args = parse_args()
    session = args.session.expanduser().resolve()
    require(session.is_dir(), f"session directory not found: {session}")
    require(args.preview_chars > 0, "--preview-chars must be positive")
    output_dir = (args.output_dir.expanduser().resolve() if args.output_dir else session / "to-rfc-analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    write_chat_index(session, output_dir, args.preview_chars)
    write_devtools_compact(session, output_dir, args.preview_chars)
    write_readme(session, output_dir)
    print(output_dir)


if __name__ == "__main__":
    main()
