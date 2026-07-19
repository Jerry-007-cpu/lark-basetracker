"""Local registry for named table tracking sources."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


REGISTRY_SCHEMA_VERSION = 1
DEFAULT_REGISTRY_PATH = "~/.config/lark-basetracker/sources.json"
SOURCE_LABELS = {"lark": "飞书", "tencent": "腾讯文档", "file": "本地文件"}


def _path(path: str) -> Path:
    return Path(path).expanduser().resolve()


def _empty_registry() -> dict[str, Any]:
    return {"schema_version": REGISTRY_SCHEMA_VERSION, "sources": []}


def load_registry(path: str = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    registry_path = _path(path)
    if not registry_path.is_file():
        return _empty_registry()
    with registry_path.open("r", encoding="utf-8") as handle:
        registry = json.load(handle)
    if registry.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise ValueError("不是受支持的 lark-basetracker 追踪源清单。")
    if not isinstance(registry.get("sources"), list):
        raise ValueError("追踪源清单缺少 sources 数组。")
    return registry


def save_registry(path: str, registry: dict[str, Any]) -> None:
    registry_path = _path(path)
    parent_was_missing = not registry_path.parent.exists()
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    if parent_was_missing:
        try:
            registry_path.parent.chmod(0o700)
        except OSError:
            pass
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=registry_path.parent, delete=False
        ) as handle:
            json.dump(registry, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            temporary_name = handle.name
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, registry_path)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _clean_name(name: str) -> str:
    cleaned = " ".join(name.split())
    if not cleaned:
        raise ValueError("追踪源名称不能为空。")
    return cleaned


def _target_key(source: dict[str, Any]) -> tuple[str, str, str, str]:
    kind = str(source.get("kind", ""))
    location = str(source.get("location", ""))
    if kind == "tencent":
        parsed = urlsplit(location)
        location = f"{parsed.netloc.lower()}{parsed.path.rstrip('/')}"
    return (
        kind,
        location,
        str(source.get("table_id", "")),
        str(source.get("sheet_id", "")),
    )


def add_source(
    path: str,
    *,
    name: str,
    kind: str,
    location: str,
    table_id: str = "",
    sheet_id: str = "",
    sheet_name: str = "",
    replace: bool = False,
) -> dict[str, Any]:
    cleaned_name = _clean_name(name)
    if kind not in SOURCE_LABELS:
        raise ValueError(f"不支持的数据源类型：{kind}")
    if not location.strip():
        raise ValueError("数据源链接或文件路径不能为空。")

    registry = load_registry(path)
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    source = {
        "name": cleaned_name,
        "kind": kind,
        "location": location.strip(),
        "table_id": table_id.strip(),
        "sheet_id": sheet_id.strip(),
        "sheet_name": sheet_name.strip(),
        "created_at": now,
        "updated_at": now,
    }
    sources = registry["sources"]
    name_index = next(
        (
            index
            for index, item in enumerate(sources)
            if item.get("name", "").casefold() == cleaned_name.casefold()
        ),
        None,
    )
    target_index = next(
        (index for index, item in enumerate(sources) if _target_key(item) == _target_key(source)),
        None,
    )

    if name_index is not None and target_index is not None and name_index != target_index:
        raise ValueError(f"追踪源名称“{cleaned_name}”和目标分别匹配了不同记录，无法安全替换。")
    replace_index = name_index if name_index is not None else target_index
    if replace_index is not None:
        if not replace:
            if name_index is not None:
                raise ValueError(f"追踪源名称“{cleaned_name}”已存在；请换一个名称或使用 --replace。")
            raise ValueError(f"这个数据源已保存为“{sources[target_index].get('name', '')}”。")
        source["created_at"] = sources[replace_index].get("created_at", now)
        sources[replace_index] = source
    else:
        sources.append(source)

    sources.sort(key=lambda item: (item.get("kind", ""), item.get("name", "").casefold()))
    save_registry(path, registry)
    return source


def get_source(path: str, name: str) -> dict[str, Any]:
    cleaned_name = _clean_name(name)
    sources = load_registry(path)["sources"]
    matches = [item for item in sources if item.get("name", "").casefold() == cleaned_name.casefold()]
    if not matches:
        raise ValueError(f"没有找到追踪源“{cleaned_name}”。")
    return matches[0]


def remove_source(path: str, name: str) -> dict[str, Any]:
    source = get_source(path, name)
    registry = load_registry(path)
    registry["sources"] = [
        item
        for item in registry["sources"]
        if item.get("name", "").casefold() != source.get("name", "").casefold()
    ]
    save_registry(path, registry)
    return source


def source_label(source: dict[str, Any]) -> str:
    platform = SOURCE_LABELS.get(str(source.get("kind", "")), "未知来源")
    return f"{platform}｜{source.get('name', '未命名')}"


def render_source_picker(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "\n".join([
            "欢迎使用 lark-basetracker。请选择首次连接方式：",
            "1. 飞书多维表格（用户身份只读）",
            "2. 腾讯文档在线表格",
            "3. CSV、TSV 或 XLSX 文件",
            "",
            "直接回复序号即可，我会按所选来源逐步引导。",
        ])
    if len(sources) == 1:
        return f"当前追踪源：{source_label(sources[0])}"
    lines = [f"你已保存 {len(sources)} 个追踪源，想查看哪个？"]
    lines.extend(f"{index}. {source_label(source)}" for index, source in enumerate(sources, start=1))
    lines.append(f"{len(sources) + 1}. 全部汇总")
    lines.extend(["", "也可以直接说“查秋招表最近 7 天更新”。"])
    return "\n".join(lines)
