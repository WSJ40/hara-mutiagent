#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate minimal Stage 0 function mapping from a normalized function doc.

The generator is intentionally deterministic:
- read function names only from a table marked with "功能清单"
- use the exact column whose header is "功能"
- match each function name to a numbered heading while ignoring whitespace
- put the matched heading and all descendant section content into detail_text
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from extract_function_doc import extract as extract_document
except ImportError:  # pragma: no cover
    from .extract_function_doc import extract as extract_document


SPACE_RE = re.compile(r"[\s\u3000]+")
HEADING_PREFIX_RE = re.compile(r"^\s*\d+(?:\.\d+)+\s*")
IMAGE_BLOCK_TYPES = {"image", "picture", "drawing"}


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dump_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clean_text(value: Any) -> str:
    return SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def compact_text(value: Any) -> str:
    return SPACE_RE.sub("", str(value or "")).strip().lower()


def strip_heading_prefix(value: Any) -> str:
    return clean_text(HEADING_PREFIX_RE.sub("", str(value or "")))


def trim_function_suffix(value: str) -> str:
    text = clean_text(value)
    return text[:-2] if text.endswith("功能") else text


def function_name_forms(value: str) -> set[str]:
    name = strip_heading_prefix(value)
    base = trim_function_suffix(name)
    forms = {compact_text(name), compact_text(base)}
    if base:
        forms.add(compact_text(f"{base}功能"))
    return {form for form in forms if form}


def block_type(block: dict[str, Any]) -> str:
    return str(block.get("type") or "").strip().lower()


def section_id(block: dict[str, Any]) -> str:
    value = str(block.get("section_id") or "").strip()
    return "" if not value or value.lower() == "nan" else value


def section_depth(value: str) -> int:
    return len(value.split(".")) if value else sys.maxsize


def heading_title(block: dict[str, Any]) -> str:
    title = str(block.get("title") or "").strip()
    if title and title.lower() != "nan":
        return clean_text(title)
    return strip_heading_prefix(block.get("text"))


def is_heading(block: dict[str, Any]) -> bool:
    return block_type(block) == "heading" and bool(section_id(block))


def is_descendant(child_section: str, parent_section: str) -> bool:
    return bool(parent_section and child_section.startswith(f"{parent_section}."))


def render_table(rows: list[list[Any]]) -> str:
    rendered_rows: list[str] = []
    for row in rows:
        cells = [clean_text(cell) for cell in row]
        if any(cells):
            rendered_rows.append("\t".join(cells).rstrip())
    return "\n".join(rendered_rows)


def block_text(block: dict[str, Any]) -> str:
    if block_type(block) == "table" and isinstance(block.get("rows"), list):
        return render_table(block["rows"])
    return clean_text(block.get("text"))


def contains_function_list_marker(block: dict[str, Any]) -> bool:
    return "功能清单" in compact_text(block_text(block))


def previous_marker(blocks: list[dict[str, Any]], table_index: int, lookback: int = 3) -> bool:
    start = max(0, table_index - lookback)
    for block in blocks[start:table_index]:
        if contains_function_list_marker(block):
            return True
    return False


def table_rows(block: dict[str, Any]) -> list[list[Any]]:
    rows = block.get("rows")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, list)]


def find_function_header(rows: list[list[Any]]) -> tuple[int, int] | None:
    for row_index, row in enumerate(rows):
        for col_index, cell in enumerate(row):
            if compact_text(cell) == "功能":
                return row_index, col_index
    return None


def clean_function_name(value: Any) -> str:
    text = strip_heading_prefix(value)
    text = re.sub(r"^[（(]?\d+[）).、]\s*", "", text)
    text = text.strip("：:;；,，")
    return clean_text(text)


def names_from_function_table(block: dict[str, Any]) -> list[str]:
    rows = table_rows(block)
    header = find_function_header(rows)
    if header is None:
        return []
    header_index, function_col = header
    names: list[str] = []
    seen: set[str] = set()
    for row in rows[header_index + 1 :]:
        if function_col >= len(row):
            continue
        name = clean_function_name(row[function_col])
        key = compact_text(name)
        if not key or key == "功能" or key in seen:
            continue
        seen.add(key)
        names.append(name)
    return names


def function_list_table_indices(blocks: list[dict[str, Any]]) -> tuple[list[int], bool]:
    strict: list[int] = []
    fallback: list[int] = []
    for index, block in enumerate(blocks):
        if block_type(block) != "table" or find_function_header(table_rows(block)) is None:
            continue
        fallback.append(index)
        if contains_function_list_marker(block) or previous_marker(blocks, index):
            strict.append(index)
    return (strict, False) if strict else (fallback, bool(fallback))


def extract_function_names(
    blocks: list[dict[str, Any]],
    allow_heading_fallback: bool,
    review_log: list[dict[str, Any]],
) -> tuple[list[str], set[int]]:
    table_indices, used_fallback_table = function_list_table_indices(blocks)
    names: list[str] = []
    seen: set[str] = set()
    for index in table_indices:
        for name in names_from_function_table(blocks[index]):
            key = compact_text(name)
            if key and key not in seen:
                seen.add(key)
                names.append(name)

    if names:
        if used_fallback_table:
            review_log.append({
                "stage": "stage0",
                "level": "warning",
                "code": "function_list_marker_missing",
                "message": "未找到包含“功能清单”的表格，已退回使用带“功能”列头的表格。",
            })
        return names, set(table_indices)

    if not allow_heading_fallback:
        raise SystemExit(
            "No function names found. Provide a table marked with “功能清单” and a column whose header is exactly “功能”, "
            "or rerun with --allow-heading-fallback for legacy documents."
        )

    for block in blocks:
        if not is_heading(block):
            continue
        title = heading_title(block)
        if title.endswith("功能"):
            key = compact_text(title)
            if key and key not in seen:
                seen.add(key)
                names.append(title)
    if not names:
        raise SystemExit("No function names found from function-list tables or heading fallback.")
    review_log.append({
        "stage": "stage0",
        "level": "warning",
        "code": "heading_fallback_used",
        "message": "未从“功能清单”表格提取到功能，已按显式参数使用标题 fallback。",
    })
    return names, set()


def heading_match_score(function_name: str, block: dict[str, Any]) -> int:
    if not is_heading(block):
        return 0
    title = heading_title(block)
    function_forms = function_name_forms(function_name)
    title_exact = compact_text(title)
    title_base = compact_text(trim_function_suffix(title))
    if title_exact == compact_text(function_name):
        return 120
    if title_exact in function_forms:
        return 110
    if title_base in function_forms:
        return 100
    return 0


def find_matching_heading(function_name: str, blocks: list[dict[str, Any]]) -> int | None:
    candidates: list[tuple[int, int, int]] = []
    for index, block in enumerate(blocks):
        score = heading_match_score(function_name, block)
        if score:
            candidates.append((-score, section_depth(section_id(block)), index))
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][2]


def build_detail_text(
    blocks: list[dict[str, Any]],
    heading_index: int,
    skipped_table_indices: set[int],
) -> tuple[str, list[str]]:
    parent = section_id(blocks[heading_index])
    pieces: list[str] = []
    detail_sections: list[str] = []
    for index in range(heading_index, len(blocks)):
        block = blocks[index]
        if index != heading_index and is_heading(block):
            current = section_id(block)
            if parent and not is_descendant(current, parent):
                break
            if not parent:
                break
        if index in skipped_table_indices or block_type(block) in IMAGE_BLOCK_TYPES:
            continue
        text = block_text(block)
        if not text:
            continue
        pieces.append(text)
        current_section = section_id(block)
        if current_section and current_section != parent and current_section not in detail_sections:
            detail_sections.append(current_section)
    return "\n\n".join(pieces).strip() or "nan", detail_sections


def infer_run_id(args: argparse.Namespace, source_meta: dict[str, Any], out_path: Path) -> str:
    if args.run_id:
        return args.run_id
    if args.prefix:
        return args.prefix
    match = re.match(r"(.+?)_stage0", out_path.name)
    if match:
        return match.group(1)
    source_name = str(source_meta.get("source_name") or source_meta.get("source_path") or "").strip()
    if source_name:
        return Path(source_name).stem
    return "HARA_RUN"


def infer_system(run_id: str, source_meta: dict[str, Any], explicit: str | None) -> str:
    if explicit:
        return explicit
    for value in (run_id, source_meta.get("source_name"), source_meta.get("source_path")):
        text = str(value or "").strip()
        match = re.match(r"[A-Za-z0-9]+", text)
        if match:
            return match.group(0).upper()
    return "unknown"


def load_source(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any] | None]:
    if args.source_extraction and args.input:
        raise SystemExit("Use either --source-extraction or --input, not both.")
    if args.source_extraction:
        source_path = Path(args.source_extraction)
        source_data = load_json(source_path)
        blocks = source_data.get("blocks") if isinstance(source_data, dict) else None
        if not isinstance(blocks, list):
            raise SystemExit(f"source_extraction is missing blocks: {source_path}")
        meta = source_data.get("meta", {}) if isinstance(source_data, dict) else {}
        if isinstance(meta, dict):
            meta = dict(meta)
        else:
            meta = {}
        meta.setdefault("source_extraction", str(source_path))
        return [block for block in blocks if isinstance(block, dict)], meta, None

    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"Input file not found: {input_path}")
        blocks, method = extract_document(input_path)
        source_data = {
            "meta": {
                "source_path": str(input_path),
                "source_name": input_path.name,
                "source_type": input_path.suffix.lower().lstrip(".") or "text",
                "extraction_method": method,
                "blocks": len(blocks),
            },
            "blocks": blocks,
            "full_text": "\n\n".join(block.get("text", "") for block in blocks if block.get("text")),
        }
        if args.source_out:
            dump_json(source_data, Path(args.source_out))
        return blocks, source_data["meta"], source_data

    raise SystemExit("Provide --source-extraction or --input.")


def write_stage1_contexts(stage0_path: Path, stage0_data: dict[str, Any], run_id: str, out_dir: Path) -> list[str]:
    try:
        from prepare_stage1_context import build_context, default_context_path
    except ImportError:  # pragma: no cover
        from .prepare_stage1_context import build_context, default_context_path

    rows = [row for row in stage0_data.get("function_mapping", []) if isinstance(row, dict)]
    paths: list[str] = []
    for index, row in enumerate(rows, start=1):
        fid = str(row.get("Function_ID") or "").strip()
        context = build_context(stage0_path, stage0_data, row, index, len(rows), run_id)
        out_path = default_context_path(out_dir, run_id, fid)
        dump_json(context, out_path)
        paths.append(str(out_path))
    return paths


def build_stage0(args: argparse.Namespace) -> tuple[dict[str, Any], Path, list[str]]:
    out_path = Path(args.out)
    blocks, source_meta, _source_data = load_source(args)
    review_log: list[dict[str, Any]] = []
    function_names, skipped_table_indices = extract_function_names(blocks, args.allow_heading_fallback, review_log)
    run_id = infer_run_id(args, source_meta, out_path)
    system = infer_system(run_id, source_meta, args.system)
    rows: list[dict[str, Any]] = []

    for index, name in enumerate(function_names, start=1):
        heading_index = find_matching_heading(name, blocks)
        if heading_index is None:
            detail_text = "nan"
            review_log.append({
                "stage": "stage0",
                "level": "warning",
                "code": "function_heading_not_found",
                "Function_ID": f"F{index:03d}",
                "function_name": name,
                "message": "功能清单中存在该功能，但未在正文标题中匹配到对应功能章节。",
            })
        else:
            detail_text, _detail_sections = build_detail_text(blocks, heading_index, skipped_table_indices)
        rows.append({
            "Function_ID": f"F{index:03d}",
            "extracted_function_name": name,
            "detail_text": detail_text,
        })

    data = {
        "meta": {
            "run_id": run_id,
            "stage": "stage0",
            "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "source_file": str(source_meta.get("source_path") or source_meta.get("source_extraction") or args.input or args.source_extraction),
            "system": system,
            "generator": "tools/hara/generate_stage0_function_mapping.py",
        },
        "function_mapping": rows,
        "review_log": review_log,
    }
    dump_json(data, out_path)

    context_files: list[str] = []
    if args.write_contexts:
        context_files = write_stage1_contexts(out_path, data, run_id, Path(args.context_dir or out_path.parent))
    return data, out_path, context_files


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="Generate minimal Stage0 function mapping from a function document.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--source-extraction", help="Normalized source extraction JSON from extract_function_doc.py")
    source.add_argument("--input", help="Function document path; supported by extract_function_doc.py")
    parser.add_argument("--source-out", help="When using --input, also write normalized source extraction JSON")
    parser.add_argument("--out", required=True, help="Stage0 output JSON path")
    parser.add_argument("--run-id", help="RUN_ID stored in meta.run_id")
    parser.add_argument("--prefix", help="Alias for --run-id")
    parser.add_argument("--system", help="System code/name stored in meta.system")
    parser.add_argument("--allow-heading-fallback", action="store_true", help="Legacy fallback: extract headings ending in 功能 when no function-list table exists")
    parser.add_argument("--write-contexts", action="store_true", help="Also write output/<RUN_ID>_stage1_context_<Function_ID>.json files")
    parser.add_argument("--context-dir", help="Output directory for --write-contexts; defaults to the Stage0 output directory")
    args = parser.parse_args()

    data, out_path, context_files = build_stage0(args)
    summary = {
        "ok": True,
        "stage": "stage0",
        "run_id": data["meta"]["run_id"],
        "system": data["meta"]["system"],
        "functions": len(data["function_mapping"]),
        "warnings": len(data["review_log"]),
        "output": str(out_path),
        "context_files": context_files,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
