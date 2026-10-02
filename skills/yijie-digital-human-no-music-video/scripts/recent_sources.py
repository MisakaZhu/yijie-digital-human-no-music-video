#!/usr/bin/env python3
"""Build a local rolling source index or check one source; standard library only."""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit, urlunsplit

ID = re.compile(r"[0-9]{19}\Z")
TERMINAL = {"failed", "cancelled", "canceled", "skipped", "duplicate_skipped", "abandoned"}
VERIFIED = {"verified", "completed"}


def video_id(source: str, explicit: str | None = None) -> str | None:
    observed: set[str] = set()
    if explicit is not None and explicit != "":
        if not ID.fullmatch(str(explicit)):
            raise ValueError("invalid_source_video_id")
        observed.add(str(explicit))
    if source:
        parsed = urlsplit(source)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("invalid_source_url")
        if parsed.username or parsed.password:
            raise ValueError("source_url_contains_credentials")
        match = re.search(r"/video/([0-9]{19})(?:/|$)", parsed.path)
        if match:
            observed.add(match.group(1))
        for value in parse_qs(parsed.query).get("modal_id", []):
            if not ID.fullmatch(value):
                raise ValueError("invalid_modal_id")
            observed.add(value)
    if len(observed) > 1:
        raise ValueError("conflicting_source_video_ids")
    return next(iter(observed), None)


def redacted_url(value: str) -> str:
    parsed = urlsplit(value)
    if not parsed.hostname:
        return ""
    host = parsed.hostname
    if ":" in host:
        host = "[" + host + "]"
    if parsed.port is not None:
        host += ":" + str(parsed.port)
    return urlunsplit((parsed.scheme, host, parsed.path, "", ""))


def timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("missing_timestamp")
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("timestamp_requires_timezone")
    return moment.astimezone(timezone.utc)


def load_records(root: Path, now: datetime, hours: int = 168) -> tuple[list[dict], list[dict]]:
    if not root.is_dir():
        raise ValueError("runs_dir_missing_or_not_directory")
    rows: list[dict] = []
    issues: list[dict] = []
    cutoff = now - timedelta(hours=hours)
    for file in sorted(root.glob("*/task-checkpoint.json")):
        try:
            data = json.loads(file.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict):
                raise ValueError("checkpoint_not_object")
            source = data.get("source_url") or ""
            if not isinstance(source, str):
                raise ValueError("source_url_not_string")
            identifier = video_id(source, data.get("source_video_id"))
            if not source and not identifier:
                continue  # Direct copy with no source is not source-indexable.
            run_id = data.get("run_id") or file.parent.name
            if not isinstance(run_id, str) or run_id != file.parent.name:
                raise ValueError("run_id_directory_mismatch")
            generation = str(data.get("generation_status") or "").lower()
            phase = str(data.get("phase") or "").lower()
            if generation in TERMINAL or phase in TERMINAL:
                continue
            identity = bool(data.get("result_identity_evidence"))
            local_ok = data.get("local_validation_status") == "passed"
            preview_ok = (data.get("preview_status") == "verified"
                          and data.get("result_origin") in {"right_history", "work_library"}
                          and bool(data.get("result_preview_clicked_at")))
            verified = generation in VERIFIED and identity and (local_ok or preview_ok)
            if generation in VERIFIED and not verified:
                raise ValueError("completed_result_missing_verification_evidence")
            if verified:
                time_value = next((data.get(k) for k in
                                   ("completed_at", "result_verified_at", "completion_at", "generated_at")
                                   if data.get(k)), None)
                when = timestamp(time_value)
            else:
                when = timestamp(data.get("created_at"))
            if when > now:
                raise ValueError("checkpoint_time_in_future")
            active = not verified
            recent = verified and cutoff <= when <= now
            if not active and not recent:
                continue
            local_file = data.get("local_file")
            if local_file is not None and not isinstance(local_file, str):
                raise ValueError("local_file_not_string")
            local_exists = bool(local_file and Path(local_file).is_file())
            rows.append({
                "run_id": run_id,
                "video_id": identifier,
                "source_url": source,  # Kept only in process for exact-link matching.
                "source_redacted": redacted_url(source) if source else "",
                "title": str(data.get("title") or "未记录标题"),
                "time": when.isoformat(),
                "verified": verified,
                "active": active,
                "local_file_status": "present" if local_exists else
                                     ("verified_but_missing" if local_file else "platform_only"),
            })
        except (OSError, ValueError, TypeError, OverflowError):
            # Do not echo raw exception messages, source URLs or private copy.
            issues.append({"checkpoint": str(file), "reason": "invalid_or_incomplete_checkpoint"})
    return rows, issues


def check(root: Path, source: str, identifier: str | None, exclude_run: str | None,
          now: datetime, hours: int = 168) -> tuple[dict, int]:
    wanted_id = video_id(source, identifier)
    rows, issues = load_records(root, now, hours)
    matches = [row for row in rows if row["run_id"] != exclude_run and
               ((wanted_id is not None and row["video_id"] == wanted_id) or
                (source and row["source_url"] == source))]
    safe_matches = [{k: v for k, v in row.items() if k != "source_url"} for row in matches]
    status, code = ("duplicate", 10) if matches else (
        ("evidence_incomplete", 12) if issues else
        (("unknown_identity", 11) if wanted_id is None else ("no_match", 0)))
    return {"status": status, "checked_at": now.isoformat(), "window_hours": hours,
            "video_id": wanted_id, "matches": safe_matches, "issues": issues,
            "scope": "local_checkpoints_only"}, code


def cell(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("|", r"\|").replace("\r", " ").replace("\n", " ")


def refresh(root: Path, output: Path, now: datetime, hours: int = 168) -> dict:
    rows, issues = load_records(root, now, hours)
    if issues:
        return {"status": "evidence_incomplete", "issues": issues, "output_written": False}
    verified = [row for row in rows if row["verified"] and row["video_id"]]
    groups: dict[str, list[dict]] = {}
    for row in verified:
        groups.setdefault(row["video_id"], []).append(row)
    ordered = sorted(groups.items(), key=lambda item: min(row["time"] for row in item[1]))
    lines = ["# 近 7 天已核验生成的来源", "",
             f"更新时间（UTC）：{now.isoformat()}",
             f"统计窗口：{(now - timedelta(hours=hours)).isoformat()} ～ {now.isoformat()}（{hours} 小时）",
             f"已核验记录：{len(verified)}；不同来源 ID：{len(groups)}。", "",
             "仅覆盖指定本机运行目录，空清单不代表平台没有历史作品。完成时间取实际核验时间。", "",
             "| 序号 | 来源 ID | 最近完成时间 | 标题 | 来源（已去查询参数） | 次数 | 文件状态 |",
             "| ---: | --- | --- | --- | --- | ---: | --- |"]
    for number, (identifier, group) in enumerate(ordered, 1):
        latest = max(group, key=lambda row: row["time"])
        values = (number, identifier, latest["time"], latest["title"],
                  latest["source_redacted"], len(group), latest["local_file_status"])
        lines.append("| " + " | ".join(cell(v) for v in values) + " |")
    lines += ["", "文件后来缺失不抹去已核验生成证据。仅提交、提取或生成失败不计入。",
              f"进行中任务：{sum(row['active'] for row in rows)}；已核验但缺少可索引 ID："
              f"{sum(row['verified'] and not row['video_id'] for row in rows)}。", ""]
    if output.is_symlink():
        raise ValueError("output_symlink_refused")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(lines))
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return {"status": "updated", "updated_at": now.isoformat(), "output": str(output),
            "records": len(verified), "unique": len(groups), "output_written": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("refresh", "check"))
    parser.add_argument("--runs-dir", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source-url", default="")
    parser.add_argument("--video-id")
    parser.add_argument("--exclude-run")
    parser.add_argument("--hours", type=int, default=168)
    parser.add_argument("--now", help="Timezone-aware timestamp for offline deterministic tests")
    args = parser.parse_args()
    if args.hours <= 0 or (args.command == "refresh" and not args.output):
        parser.error("positive --hours and --output for refresh are required")
    if args.command == "check" and not (args.source_url or args.video_id):
        parser.error("check requires --source-url or --video-id")
    try:
        now = timestamp(args.now) if args.now else datetime.now(timezone.utc)
        if args.command == "check":
            result, code = check(args.runs_dir, args.source_url, args.video_id,
                                 args.exclude_run, now, args.hours)
        else:
            result = refresh(args.runs_dir, args.output, now, args.hours)
            code = 0 if result["output_written"] else 12
    except (OSError, ValueError, TypeError, OverflowError):
        result, code = {"status": "error", "reason": "invalid_input_or_filesystem_error"}, 2
    print(json.dumps(result, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
