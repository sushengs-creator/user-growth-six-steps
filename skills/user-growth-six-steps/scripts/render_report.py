#!/usr/bin/env python3
"""Render supplied growth-report data into one offline HTML file. Standard library only."""

import argparse
import html
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from string import Template
from urllib.parse import urlsplit


STEPS = (
    ("north_star", "北极星指标"),
    ("growth_mode", "增长驱动模式"),
    ("core_lever", "核心杠杆"),
    ("magic_number", "魔法数字"),
    ("growth_strategy", "增长策略"),
    ("ab_validation", "策略效果验证"),
)
STEP_STATES = {"done": "已完成", "current": "进行中", "pending": "待推进", "blocked": "待补资料"}
SOURCE_TYPES = {"book": "图书", "article": "文章", "user": "用户提供", "other": "其他"}
COVERAGE = {"full": "全文已读", "partial": "部分已读", "unread": "未读", "unavailable": "不可访问"}


class ValidationError(ValueError):
    pass


def fail(path, message):
    raise ValidationError(f"{path}: {message}")


def object_fields(value, path, allowed, required=()):
    if not isinstance(value, dict):
        fail(path, "应为 JSON 对象")
    extra = set(value) - set(allowed)
    if extra:
        fail(path, "存在未知字段: " + ", ".join(sorted(extra)))
    for key in required:
        if key not in value:
            fail(path, f"缺少必填字段 {key}")


def text_field(value, path, required=False):
    if value is None and not required:
        return
    if not isinstance(value, str):
        fail(path, "应为字符串" + ("或 null" if not required else ""))
    if required and not value.strip():
        fail(path, "不可为空")
    if "\x00" in value:
        fail(path, "不可包含 NUL 字符")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        fail(path, "包含无效 Unicode 字符（未配对代理项）")


def enum_field(value, path, choices, nullable=False):
    if value is None and nullable:
        return
    if not isinstance(value, str) or value not in choices:
        fail(path, "可选值为 " + ", ".join(choices))


def list_field(value, path):
    if not isinstance(value, list):
        fail(path, "应为数组；没有条目时使用 []")


def scalar_field(value, path):
    if value is None or isinstance(value, str):
        text_field(value, path)
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(path, "应为字符串、有限数字或 null")
    if isinstance(value, float) and not math.isfinite(value):
        fail(path, "不可使用 NaN 或 Infinity")


def valid_url(value, path):
    if value is None:
        return
    text_field(value, path, required=True)
    if re.search(r"[\s\x00-\x1f\x7f]", value):
        fail(path, "URL 不可包含空白或控制字符")
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
            fail(path, "只允许含主机名的 http/https URL")
        if parsed.username is not None or parsed.password is not None:
            fail(path, "URL 不可包含用户名或密码")
        parsed.port  # Reject malformed port numbers.
    except ValueError as exc:
        fail(path, f"无效 URL ({exc})")


def validate(data):
    top = {"schema_version", "status", "title", "subtitle", "created_at", "subject", "summary",
           "facts", "hypotheses", "gaps", "steps", "metrics", "actions", "verification", "sources", "limitations"}
    object_fields(data, "$", top, ("schema_version", "status", "title"))
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        fail("$.schema_version", "当前仅支持整数 1")
    enum_field(data["status"], "$.status", ("draft", "final"))
    text_field(data["title"], "$.title", required=True)
    for key in ("subtitle", "created_at", "subject", "summary"):
        text_field(data.get(key), f"$.{key}")
    for key in top - {"schema_version", "status", "title", "subtitle", "created_at", "subject", "summary"}:
        if key in data:
            list_field(data[key], f"$.{key}")

    sources = {}
    for index, item in enumerate(data.get("sources", [])):
        p = f"$.sources[{index}]"
        object_fields(item, p, ("id", "title", "type", "url", "location", "coverage", "note"), ("id", "title", "type"))
        text_field(item["id"], p + ".id", True)
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", item["id"]):
            fail(p + ".id", "需为 1–64 位英文字母、数字、下划线或连字符")
        if item["id"] in sources:
            fail(p + ".id", "来源 ID 不可重复")
        text_field(item["title"], p + ".title", True)
        enum_field(item["type"], p + ".type", SOURCE_TYPES)
        enum_field(item.get("coverage"), p + ".coverage", COVERAGE, nullable=True)
        valid_url(item.get("url"), p + ".url")
        for key in ("location", "note"):
            text_field(item.get(key), p + "." + key)
        sources[item["id"]] = item

    def refs(item, p):
        if "source_ids" not in item:
            return
        list_field(item["source_ids"], p + ".source_ids")
        seen = set()
        for i, source_id in enumerate(item["source_ids"]):
            text_field(source_id, f"{p}.source_ids[{i}]", True)
            if source_id not in sources:
                fail(p + ".source_ids", f"来源 {source_id} 未在 sources 中定义")
            if source_id in seen:
                fail(p + ".source_ids", f"来源 {source_id} 重复引用")
            seen.add(source_id)

    for section in ("facts", "hypotheses", "gaps"):
        for i, item in enumerate(data.get(section, [])):
            p = f"$.{section}[{i}]"
            object_fields(item, p, ("text", "note", "source_ids"), ("text",))
            text_field(item["text"], p + ".text", True)
            text_field(item.get("note"), p + ".note")
            refs(item, p)

    seen_steps = set()
    for i, item in enumerate(data.get("steps", [])):
        p = f"$.steps[{i}]"
        object_fields(item, p, ("id", "state", "finding", "decision", "next_question", "source_ids"), ("id", "state"))
        enum_field(item["id"], p + ".id", dict(STEPS))
        if item["id"] in seen_steps:
            fail(p + ".id", "同一步骤不可重复")
        seen_steps.add(item["id"])
        enum_field(item["state"], p + ".state", STEP_STATES)
        for key in ("finding", "decision", "next_question"):
            text_field(item.get(key), p + "." + key)
        refs(item, p)

    for i, item in enumerate(data.get("metrics", [])):
        p = f"$.metrics[{i}]"
        fields = ("name", "value", "unit", "definition", "numerator", "denominator", "population", "period", "source_ids")
        object_fields(item, p, fields, ("name",))
        text_field(item["name"], p + ".name", True)
        for key in ("value", "numerator", "denominator"):
            scalar_field(item.get(key), p + "." + key)
        for key in ("unit", "definition", "population", "period"):
            text_field(item.get(key), p + "." + key)
        refs(item, p)

    for section, required, fields in (
        ("actions", "title", ("title", "owner", "timeframe", "scope", "description", "success_criterion", "stop_criterion", "source_ids")),
        ("verification", "hypothesis", ("hypothesis", "method", "population", "primary_metric", "guardrails", "sample_plan", "duration", "decision_rule", "risks", "source_ids")),
    ):
        for i, item in enumerate(data.get(section, [])):
            p = f"$.{section}[{i}]"
            object_fields(item, p, fields, (required,))
            for key in fields:
                if key != "source_ids":
                    text_field(item.get(key), p + "." + key, required=key == required)
            refs(item, p)

    for i, item in enumerate(data.get("limitations", [])):
        text_field(item, f"$.limitations[{i}]", True)
    return data


def esc(value):
    return html.escape(str(value), quote=True)


def display(value):
    if value is None or (isinstance(value, str) and not value.strip()):
        return '<span class="unknown">待补充</span>'
    return esc(value).replace("\n", "<br>")


def reference_links(item):
    refs = item.get("source_ids", [])
    if not refs:
        return '<span class="unreferenced">未关联来源</span>'
    return " ".join(f'<a class="ref" href="#source-{esc(source_id)}">{esc(source_id)}</a>' for source_id in refs)


def empty(text="尚未提供"):
    return f'<p class="empty">{esc(text)}</p>'


def kv(label, value):
    return f'<div class="kv"><dt>{esc(label)}</dt><dd>{display(value)}</dd></div>'


def render_evidence(data):
    blocks = []
    for key, title, label in (("facts", "已知事实", "FACT"), ("hypotheses", "待验证假设", "HYPOTHESIS"), ("gaps", "信息缺口", "GAP")):
        items = []
        for item in data.get(key, []):
            note = f'<p class="note">{display(item["note"])}</p>' if item.get("note") else ""
            items.append(f'<li><p>{display(item["text"])}</p>{note}<div class="refs">{reference_links(item)}</div></li>')
        content = '<ul class="evidence-list">' + "".join(items) + "</ul>" if items else empty()
        blocks.append(f'<article class="evidence-card {key}"><span class="eyebrow">{label}</span><h3>{title}</h3>{content}</article>')
    return '<div class="evidence-grid">' + "".join(blocks) + "</div>"


def render_steps(data):
    by_id = {item["id"]: item for item in data.get("steps", [])}
    nav, cards = [], []
    for number, (key, title) in enumerate(STEPS, 1):
        item = by_id.get(key)
        state = item["state"] if item else "pending"
        status_label = STEP_STATES[state] if item else "未填写"
        nav.append(f'<a href="#step-{key}" class="nav-step {state}"><span class="step-number">0{number}</span><span>{title}<small>{status_label}</small></span></a>')
        body = ("<dl>" + kv("当前发现", item.get("finding")) + kv("判断与决定", item.get("decision"))
                + kv("下一项待确认", item.get("next_question")) + "</dl>"
                + f'<div class="refs">{reference_links(item)}</div>') if item else empty("本步骤尚未填写；不据此推断业务结论。")
        cards.append(f'<article class="step-card" id="step-{key}"><div class="card-head"><h3><span class="serial">0{number}</span>{title}</h3><span class="state {state}">{status_label}</span></div>{body}</article>')
    return '<nav class="steps-nav" aria-label="六步进度导航">' + "".join(nav) + "</nav>", "".join(cards)


def render_metrics(data):
    rows = []
    for item in data.get("metrics", []):
        value = display(item.get("value"))
        if item.get("value") is not None and item.get("value") != "" and item.get("unit"):
            value += f'<small class="unit">{esc(item["unit"])}</small>'
        definition = "<dl>" + kv("定义", item.get("definition")) + kv("分子", item.get("numerator")) + kv("分母", item.get("denominator")) + "</dl>"
        scope = "<dl>" + kv("用户群体", item.get("population")) + kv("观察周期", item.get("period")) + "</dl>"
        rows.append(f'<tr><th scope="row">{esc(item["name"])}</th><td class="metric-value">{value}</td><td>{definition}</td><td>{scope}</td><td>{reference_links(item)}</td></tr>')
    if not rows:
        return empty("尚未提供指标数据；未知值不会被当作 0，也不会自动计算指标。")
    return '<div class="table-wrap"><table><caption class="sr-only">指标及统计口径</caption><thead><tr><th>指标</th><th>当前值</th><th>统计口径</th><th>范围与周期</th><th>依据</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>"


def render_plans(data, section):
    blocks = []
    if section == "actions":
        title_key = "title"
        fields = (("owner", "负责角色"), ("timeframe", "时间安排"), ("scope", "执行对象"), ("description", "具体行动"), ("success_criterion", "继续依据"), ("stop_criterion", "停止或调整依据"))
    else:
        title_key = "hypothesis"
        fields = (("method", "验证方法"), ("population", "验证对象"), ("primary_metric", "主要指标"), ("guardrails", "约束指标"), ("sample_plan", "样本安排"), ("duration", "观察时间"), ("decision_rule", "判断规则"), ("risks", "局限与干扰"))
    for i, item in enumerate(data.get(section, []), 1):
        body = "".join(kv(label, item.get(key)) for key, label in fields)
        blocks.append(f'<article class="plan-card"><h3><span class="serial">{i:02d}</span>{esc(item[title_key])}</h3><dl>{body}</dl><div class="refs">{reference_links(item)}</div></article>')
    return '<div class="plans">' + "".join(blocks) + "</div>" if blocks else empty()


def render_sources(data):
    items = []
    for source in data.get("sources", []):
        title = esc(source["title"])
        if source.get("url"):
            title = f'<a href="{esc(source["url"])}" rel="noopener noreferrer">{title}</a>'
        note = f'<p class="note">{display(source["note"])}</p>' if source.get("note") else ""
        url_print = f'<p class="source-url">{esc(source["url"])}</p>' if source.get("url") else ""
        coverage = COVERAGE.get(source.get("coverage"), "覆盖范围未填写")
        items.append(f'<li id="source-{esc(source["id"])}"><div class="source-title"><span class="source-id">{esc(source["id"])}</span>{title}</div><p class="source-meta">{SOURCE_TYPES[source["type"]]} · {coverage}</p><p>章节 / 定位：{display(source.get("location"))}</p>{note}{url_print}</li>')
    return '<ol class="sources">' + "".join(items) + "</ol>" if items else empty("尚未提供来源。此报告不应被视为已经完成来源核验。")


def render(data, template_path):
    navigation, steps = render_steps(data)
    limits = data.get("limitations", [])
    limitations = '<ul class="plain-list">' + "".join(f"<li>{display(item)}</li>" for item in limits) + "</ul>" if limits else empty("尚未填写适用边界与限制。")
    values = {
        "title": esc(data["title"]),
        "subtitle": display(data.get("subtitle")),
        "status": "草案" if data["status"] == "draft" else "定稿",
        "status_class": data["status"],
        "date": display(data.get("created_at")),
        "subject": display(data.get("subject")),
        "summary": display(data.get("summary")),
        "navigation": navigation,
        "evidence": render_evidence(data),
        "steps": steps,
        "metrics": render_metrics(data),
        "actions": render_plans(data, "actions"),
        "verification": render_plans(data, "verification"),
        "sources": render_sources(data),
        "limitations": limitations,
    }
    return Template(template_path.read_text(encoding="utf-8")).substitute(values)


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"JSON 字段重复: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValidationError(f"JSON 不允许 {value}")


def write_output(path, content, overwrite):
    if path.is_symlink():
        raise ValidationError("输出路径不可为符号链接")
    if not path.parent.is_dir():
        raise ValidationError("输出目录不存在，请先创建目录")
    if not overwrite:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        return
    if path.exists() and not path.is_file():
        raise ValidationError("输出路径不是普通文件")
    fd, temporary = tempfile.mkstemp(prefix=".growth-report-", suffix=".html", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        if path.is_symlink():
            raise ValidationError("输出路径不可为符号链接")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(description="将用户增长报告 JSON 渲染为单文件离线 HTML；不会填造业务事实。")
    parser.add_argument("input", type=Path, help="输入 JSON 文件")
    parser.add_argument("output", type=Path, help="输出 .html 文件")
    parser.add_argument("--overwrite", action="store_true", help="明确允许替换已有输出；默认拒绝覆盖")
    args = parser.parse_args(argv)
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValidationError("输入与输出不可为同一文件")
        if args.output.suffix.lower() != ".html":
            raise ValidationError("输出文件扩展名必须是 .html")
        data = json.loads(args.input.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs, parse_constant=reject_constant)
        validate(data)
        template_path = Path(__file__).resolve().parent.parent / "assets" / "report-template.html"
        content = render(data, template_path)
        write_output(args.output, content, args.overwrite)
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        print(f"生成失败：{exc}", file=sys.stderr)
        return 2
    print(str(args.output.resolve()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
