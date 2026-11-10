"""Build an offline reader handbook from the current public Markdown sources."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import html
import posixpath
import re
import unicodedata

REPO = Path(__file__).resolve().parents[1]
BASE_URL = "https://github.com/sushengs-creator/user-growth-six-steps"
DOCUMENTS = {"README.md": "readme", "docs/install-guide.md": "install", "docs/reader-guide.md": "usage", "docs/methodology.md": "methodology"}
sources = {path: (REPO / path).read_text(encoding="utf-8") for path in DOCUMENTS}
headings = {}

def slug(text):
    text = re.sub(r"[`*]", "", text).lower()
    text = "".join(c for c in text if c in "-_" or not unicodedata.category(c).startswith(("P", "S")))
    return re.sub(r"\s", "-", text)

for source, content in sources.items():
    seen = Counter()
    headings[source] = {}
    in_code = False
    for line in content.splitlines():
        if line.startswith("```"): in_code = not in_code
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match and not in_code:
            key = slug(match[2]); number = seen[key]; seen[key] += 1
            key += f"-{number}" if number else ""
            headings[source][key] = DOCUMENTS[source] + "-" + key

def resolve_link(target, source):
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme not in ("http", "https"): raise ValueError(f"Unsupported URL: {target}")
        return target
    target_path = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(parsed.path))) if parsed.path else source
    fragment = unquote(parsed.fragment)
    if target_path in DOCUMENTS:
        if fragment:
            if fragment not in headings[target_path]: raise ValueError(f"Missing Markdown anchor: {source} -> {target}")
            return "#" + headings[target_path][fragment]
        return "#" + DOCUMENTS[target_path]
    if not (REPO / target_path).is_file(): raise ValueError(f"Missing linked file: {source} -> {target}")
    return BASE_URL + "/blob/main/" + target_path + ("#" + fragment if fragment else "")

def inline(text, source):
    tokens = []
    def save(markup):
        tokens.append(markup)
        return f"\x01{len(tokens) - 1}\x02"
    text = re.sub(r"`([^`]+)`", lambda m: save("<code>" + html.escape(m[1]) + "</code>"), text)
    def link(match):
        target = resolve_link(match[2], source)
        return save('<a href="' + html.escape(target, quote=True) + '">' + html.escape(match[1]) + "</a>")
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    for i in reversed(range(len(tokens))): text = text.replace(f"\x01{i}\x02", tokens[i])
    return text

def render(text, source, heading_counts=None):
    lines = text.splitlines(); output = []; i = 0
    heading_counts = heading_counts if heading_counts is not None else Counter()
    while i < len(lines):
        line = lines[i]
        if not line.strip(): i += 1; continue
        if line.startswith("```"):
            code = []; i += 1
            while i < len(lines) and not lines[i].startswith("```"): code.append(lines[i]); i += 1
            if i == len(lines): raise ValueError(f"Unclosed code fence in {source}")
            output.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>"); i += 1; continue
        heading = re.match(r"^(#{1,6})\s+(.+)", line)
        if heading:
            level = min(len(heading[1]) + 1, 6)
            key = slug(heading[2]); number = heading_counts[key]; heading_counts[key] += 1
            key += f"-{number}" if number else ""
            anchor = headings[source][key]
            output.append(f'<h{level} id="{html.escape(anchor, quote=True)}">' + inline(heading[2], source) + f"</h{level}>"); i += 1; continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                parts = [p.strip() for p in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", p.replace(" ", "")) for p in parts): rows.append(parts)
                i += 1
            if not rows: raise ValueError(f"Empty table in {source}")
            output.append('<div class="table-wrap"><table><thead><tr>' + "".join('<th scope="col">' + inline(p, source) + "</th>" for p in rows[0]) + "</tr></thead><tbody>" + "".join("<tr>" + "".join("<td>" + inline(p, source) + "</td>" for p in row) + "</tr>" for row in rows[1:]) + "</tbody></table></div>"); continue
        if line.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].startswith(">"): quote.append(re.sub(r"^> ?", "", lines[i])); i += 1
            output.append("<blockquote>" + render("\n".join(quote), source, heading_counts) + "</blockquote>"); continue
        item = re.match(r"^(?:- |\d+\. )(.+)", line)
        if item:
            ordered = bool(re.match(r"^\d+\.", line)); tag = "ol" if ordered else "ul"
            start = int(line.split(".", 1)[0]) if ordered else 1; items = []
            while i < len(lines):
                current = re.match(r"^\d+\. (.+)" if ordered else r"^- (.+)", lines[i])
                if not current: break
                items.append("<li>" + inline(current[1], source) + "</li>"); i += 1
            attr = f' start="{start}"' if ordered and start != 1 else ""
            output.append(f"<{tag}{attr}>" + "".join(items) + f"</{tag}>"); continue
        paragraph = [line]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||>|```|- |\d+\. )", lines[i]): paragraph.append(lines[i]); i += 1
        output.append("<p>" + inline(" ".join(paragraph), source) + "</p>")
    return "\n".join(output)

sections = [f'<section id="{section_id}" data-source="{source}">' + render(sources[source], source) + "</section>" for source, section_id in DOCUMENTS.items()]
page = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>用户增长6步法｜跨智能体安装、使用与方法论</title>
<style>
:root{--bg:#f5f6ee;--ink:#1a322e;--muted:#5d6b64;--accent:#1d7058;--line:#d9e2d8}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.9 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;overflow-wrap:anywhere}main{max-width:1040px;margin:auto;padding:44px 28px 70px}header{padding:20px 0 30px;border-bottom:3px solid var(--accent)}.eyebrow{color:var(--accent);font-size:13px;letter-spacing:.15em}h1{font-size:clamp(32px,5vw,48px);line-height:1.25;margin:16px 0}h2{font-size:30px;line-height:1.5;margin:0 0 20px}h3{font-size:24px;margin:34px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--line)}h4{font-size:19px;margin:24px 0 10px}h2,h3,h4,section{scroll-margin-top:20px}p{margin:14px 0}.lead{font-size:20px}.muted{color:var(--muted);font-size:14px}nav{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0}nav a{border:1px solid var(--line);padding:7px 14px;border-radius:30px;background:white;font-size:15px;text-decoration:none}section{background:#fff;border:1px solid var(--line);border-radius:14px;padding:32px;margin:24px 0}a{color:var(--accent);text-underline-offset:3px;overflow-wrap:anywhere}a:focus-visible{outline:3px solid #d3a554;outline-offset:3px}blockquote{border-left:4px solid #d3a554;background:#fff6e4;padding:10px 18px;margin:20px 0;font-size:15px}blockquote p{margin:8px 0}pre{background:#142f29;color:#e5f2dd;border-radius:10px;padding:20px;white-space:pre-wrap;overflow-wrap:anywhere;font-size:14px;line-height:1.8}code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.88em}p code,li code,td code{background:#edf3eb;padding:2px 5px;border-radius:4px}pre code{font-size:1em}.table-wrap{overflow:auto;margin:20px 0}table{border-collapse:collapse;width:100%;font-size:15px}th,td{padding:13px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{background:#eef3e9}li{margin:9px 0}footer{font-size:13px;color:var(--muted);margin-top:30px}@media(max-width:650px){main{padding:24px 14px}section{padding:22px 18px}table{min-width:540px}h2{font-size:26px}h3{font-size:22px}pre{padding:15px}}@media print{html{scroll-behavior:auto}body{background:white;font-size:11pt}main{max-width:none;padding:0}section{border:0;padding:0;border-radius:0;break-before:page}section:first-of-type{break-before:auto}nav{display:none}h2,h3,h4{break-after:avoid}table{min-width:0!important;font-size:9pt}tr,pre,blockquote{break-inside:avoid}.table-wrap{overflow:visible}pre{background:#f1f3ef;color:var(--ink);border:1px solid var(--line)}a{color:inherit}}@page{size:A4;margin:16mm}
</style></head><body><main>
<header><div class="eyebrow">用户增长6步法 · 完整读者手册</div><h1>从第一句问题，<br>走到能执行的增长方案。</h1><p class="lead">安装或加载 → 说出问题 → 回答追问 → 打开报告。无需先懂增长术语，按示范开始即可。</p><p>面向支持技能或能读取完整资料的不同智能体；具体安装、文件生成与云端能力取决于你使用的应用。</p><p><a href="__REPO__">GitHub 仓库</a> · <a href="__REPO__/blob/main/examples/growth-report.html">公开 HTML 报告示例</a> · <a href="__REPO__/blob/main/examples/growth-report.json">公开 JSON 示例</a></p><p class="muted">本页可离线阅读。首次安装、外部资料及 GitHub 文件下载需要联网。示例 HTML 在 GitHub 上通常显示为源码，点击 Download raw file 下载后用浏览器打开。</p></header>
<nav aria-label="读者手册导航"><a href="#readme-安装或加载">开始安装</a><a href="#readme-开始第一次对话">第一次怎么问</a><a href="#readme-操作示范">完整操作示范</a><a href="#readme-拿到报告后怎么用">报告与复盘</a><a href="#install">各平台安装</a><a href="#usage">更多使用口令</a><a href="#methodology">完整六步方法论</a></nav>
__SECTIONS__
<footer>本页由仓库 README、跨平台安装指南、读者使用指南与六步方法论同步生成。方法整理依据《增长杠杆：探索用户增长的6步法》及指定专辑中实际读取的内容，阅读范围以来源目录为准。</footer>
</main></body></html>'''.replace("__REPO__", BASE_URL).replace("__SECTIONS__", "\n".join(sections))

class VerifyHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []; self.links = []; self.code = []; self.current_code = None; self.in_pre = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs: self.ids.append(attrs["id"])
        if tag == "a": self.links.append(attrs.get("href", ""))
        if tag == "pre": self.in_pre = True; self.current_code = []
    def handle_endtag(self, tag):
        if tag == "pre":
            self.in_pre = False; self.code.append("".join(self.current_code)); self.current_code = None
    def handle_data(self, data):
        if self.in_pre: self.current_code.append(data)

check = VerifyHTML(); check.feed(page)
assert len(check.ids) == len(set(check.ids)), "Duplicate HTML IDs"
assert all(link[1:] in check.ids for link in check.links if link.startswith("#")), "Broken internal anchor"
assert all(link.startswith(("#", "https://", "http://")) for link in check.links), "Unresolved relative link"
expected_code = [match[1] for text in sources.values() for match in re.finditer(r"^```[^\n]*\n(.*?)\n```", text, flags=re.M | re.S)]
assert check.code == expected_code, "Fenced code changed during rendering"
assert not re.search(r"\x01\d+\x02", page), "Unresolved inline token"
assert "-a codex" not in page and "--agent codex" not in page, "Outdated Codex-specific installation command"
for target in [REPO / "docs/reader-handbook.html"]:
    target.write_text(page, encoding="utf-8"); print(target)
print(f"Checked {len(sources)} source documents, {len(check.ids)} unique anchors, {len(check.links)} links and {len(check.code)} unchanged fenced code blocks.")
