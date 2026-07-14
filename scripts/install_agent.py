#!/usr/bin/env python3
"""Install this repository for a supported local agent runtime."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


SKILL_NAME = "lark-basetracker"
ROOT = Path(__file__).resolve().parents[1]


def destination(platform: str, scope: str, project_dir: Path) -> Path:
    home = Path.home()
    if platform == "codex":
        return (home / ".agents/skills" if scope == "user" else project_dir / ".agents/skills") / SKILL_NAME
    if platform == "claude-code":
        return (home / ".claude/skills" if scope == "user" else project_dir / ".claude/skills") / SKILL_NAME
    if platform == "openclaw":
        return (home / ".openclaw/skills" if scope == "user" else project_dir / ".agents/skills") / SKILL_NAME
    raise ValueError(f"不支持的平台：{platform}")


def copy_runtime(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "SKILL.md", target / "SKILL.md")
    shutil.copytree(ROOT / "scripts", target / "scripts", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if (ROOT / "agents").is_dir():
        shutil.copytree(ROOT / "agents", target / "agents", dirs_exist_ok=True)
    if (ROOT / "config.example.json").exists():
        shutil.copy2(ROOT / "config.example.json", target / "config.example.json")


def install_qclaw(dry_run: bool) -> tuple[Path, Path]:
    shared = Path.home() / ".quantumclaw/workspace/shared"
    runtime = shared / SKILL_NAME
    skill_file = shared / "skills" / f"{SKILL_NAME}.md"
    if dry_run:
        return runtime, skill_file
    copy_runtime(runtime)
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    content = re.sub(
        r"python3 scripts/([A-Za-z0-9_./-]+\.py)",
        lambda match: f'python3 "{runtime / "scripts" / match.group(1)}"',
        content,
    )
    skill_file.write_text(content, encoding="utf-8")
    return runtime, skill_file


def main() -> None:
    parser = argparse.ArgumentParser(description="安装 lark-basetracker 到本地 Agent")
    parser.add_argument("--platform", required=True, choices=["codex", "claude-code", "openclaw", "qclaw"])
    parser.add_argument("--scope", choices=["user", "project"], default="user")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.platform == "qclaw":
        if args.scope != "user":
            raise SystemExit("QClaw 当前只支持安装到 ~/.quantumclaw 的共享 Skill 目录。")
        runtime, skill_file = install_qclaw(args.dry_run)
        print(f"QClaw Skill：{skill_file}")
        print(f"运行文件：{runtime}")
        if not args.dry_run:
            print("安装完成。请重新启动 QClaw，并在 Skills 页面审核后启用该 Skill。")
        return

    target = destination(args.platform, args.scope, Path(args.project_dir).expanduser().resolve())
    print(f"安装目录：{target}")
    if not args.dry_run:
        copy_runtime(target)
        print("安装完成。新对话中即可通过自然语言触发。")


if __name__ == "__main__":
    main()
