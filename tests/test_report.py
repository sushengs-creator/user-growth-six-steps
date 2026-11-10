import copy
import tempfile
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent / "skills" / "user-growth-six-steps"
SCRIPT = SKILL / "scripts" / "render_report.py"
spec = importlib.util.spec_from_file_location("renderer", SCRIPT)
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attrs = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.extend(attrs)


class RendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = (SKILL / "references" / "report-schema.md").read_text()
        cls.example = json.loads(text.split("```json\n")[1].split("\n```", 1)[0])
        cls.temp = tempfile.TemporaryDirectory()
        cls.folder = Path(cls.temp.name)
        cls.addClassCleanup(cls.temp.cleanup)

    def write_case(self, name, data):
        path = self.folder / (name + ".json")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def run_case(self, input_path, output_path, *args):
        return subprocess.run([sys.executable, str(SCRIPT), str(input_path), str(output_path), *args], capture_output=True, text=True)

    def test_valid_example_and_all_steps(self):
        path = self.write_case("example", self.example)
        output = self.folder / "example.html"
        result = self.run_case(path, output, "--overwrite")
        self.assertEqual(result.returncode, 0, result.stderr)
        rendered = output.read_text()
        for key, title in renderer.STEPS:
            self.assertIn('id="step-' + key + '"', rendered)
            self.assertIn(title, rendered)
        self.assertNotIn("$navigation", rendered)
        self.assertNotIn("<script", rendered.lower())
        self.assertNotIn("@import", rendered)

    def test_xss_all_text_and_url_attribute(self):
        data = copy.deepcopy(self.example)
        payload = '<script>alert("x")</script><img src=x onerror=alert(1)> & 中文'
        data["title"] = payload
        data["summary"] = payload
        data["facts"][0]["text"] = payload
        data["metrics"][0]["value"] = payload
        data["actions"][0]["description"] = payload
        data["verification"][0]["hypothesis"] = payload
        data["sources"][0]["title"] = payload
        data["sources"][0]["url"] = 'https://example.org/book?q="onclick="alert(1)&x=<test>'
        data["limitations"] = [payload]
        renderer.validate(data)
        rendered = renderer.render(data, SKILL / "assets" / "report-template.html")
        parsed = Tags()
        parsed.feed(rendered)
        self.assertNotIn("script", parsed.tags)
        self.assertNotIn("img", parsed.tags)
        self.assertFalse(any(name.lower().startswith("on") for name, _ in parsed.attrs))
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn("&amp; 中文", rendered)
        self.write_case("xss", data)
        (self.folder / "xss.html").write_text(rendered)

    def test_unknown_null_and_known_zero(self):
        data = {"schema_version": 1, "status": "draft", "title": "空值测试", "metrics": [
            {"name": "未知", "value": None, "unit": "%"},
            {"name": "确为零", "value": 0, "unit": "人"}
        ]}
        renderer.validate(data)
        rendered = renderer.render(data, SKILL / "assets" / "report-template.html")
        self.assertIn('<th scope="row">未知</th><td class="metric-value"><span class="unknown">待补充</span></td>', rendered)
        self.assertIn('<th scope="row">确为零</th><td class="metric-value">0<small class="unit">人</small></td>', rendered)
        self.assertIn("尚未提供来源", rendered)
        self.assertEqual(rendered.count("本步骤尚未填写"), 6)
        (self.folder / "null.html").write_text(rendered)

    def test_rejects_unsafe_urls(self):
        for url in ("javascript:alert(1)", "data:text/html,<script>", "file:///tmp/a", "//evil.test", "https://", "https://example.com\n", "https://user:password@example.com", "https://example.com:noport"):
            with self.subTest(url=url):
                data = copy.deepcopy(self.example)
                data["sources"][0]["url"] = url
                with self.assertRaises(renderer.ValidationError):
                    renderer.validate(data)

    def test_rejects_invalid_structures(self):
        cases = []
        d = copy.deepcopy(self.example); d["source"] = []; cases.append(d)
        d = copy.deepcopy(self.example); d["metrics"][0]["value"] = True; cases.append(d)
        d = copy.deepcopy(self.example); d["metrics"][0]["value"] = float("nan"); cases.append(d)
        d = copy.deepcopy(self.example); d["steps"].append(d["steps"][0]); cases.append(d)
        d = copy.deepcopy(self.example); d["sources"].append(d["sources"][0]); cases.append(d)
        d = copy.deepcopy(self.example); d["facts"][0]["source_ids"] = ["NO_SOURCE"]; cases.append(d)
        d = copy.deepcopy(self.example); d["facts"][0]["text"] = 123; cases.append(d)
        d = copy.deepcopy(self.example); d["steps"][0]["state"] = "invented"; cases.append(d)
        d = copy.deepcopy(self.example); d["status"] = "complete"; cases.append(d)
        for data in cases:
            with self.subTest(data=str(data)[:100]):
                with self.assertRaises(renderer.ValidationError):
                    renderer.validate(data)

    def test_duplicate_keys_and_invalid_json_leave_no_output(self):
        for i, raw in enumerate(('{"schema_version":1,"status":"draft","title":"a","title":"b"}', '{"value":NaN}', '{')):
            input_path = self.folder / f"invalid-{i}.json"
            input_path.write_text(raw)
            output = self.folder / f"invalid-{i}.html"
            if output.exists(): output.unlink()
            result = self.run_case(input_path, output)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())

    def test_invalid_unicode_leaves_no_output(self):
        input_path = self.folder / "invalid-unicode.json"
        input_path.write_bytes(b'{"schema_version":1,"status":"draft","title":"\\ud800"}')
        output = self.folder / "invalid-unicode.html"
        if output.exists(): output.unlink()
        result = self.run_case(input_path, output)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unicode", result.stderr)
        self.assertFalse(output.exists())

    def test_overwrite_guard_and_explicit_overwrite(self):
        path = self.write_case("overwrite", self.example)
        output = self.folder / "overwrite.html"
        output.write_text("original unchanged")
        result = self.run_case(path, output)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(output.read_text(), "original unchanged")
        result = self.run_case(path, output, "--overwrite")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(output.read_text().startswith("<!doctype html>"))

    def test_input_same_output_and_symlink_protection(self):
        path = self.write_case("same", self.example)
        before = path.read_bytes()
        result = self.run_case(path, path, "--overwrite")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(path.read_bytes(), before)
        target = self.folder / "untouched-target.html"
        target.write_text("untouched")
        link = self.folder / "link.html"
        if link.is_symlink(): link.unlink()
        link.symlink_to(target)
        result = self.run_case(path, link, "--overwrite")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(target.read_text(), "untouched")

    def test_chinese_long_paragraph_and_final_label(self):
        data = copy.deepcopy(self.example)
        data["title"] = "长中文内容与跨页排版测试：" + "用户增长诊断" * 12
        data["status"] = "final"
        data["summary"] = "这是用于验证断行与打印表现的合成中文长段落，不属于任何真实业务。" * 30
        data["facts"][0]["text"] = "中文无空格内容需要自然换行，不能横向溢出页面。" * 60
        data["metrics"][0]["definition"] = "明确分子分母群体周期，保持口径一致。" * 15
        data["sources"][0]["url"] = "https://example.org/" + "long-path-" * 35
        renderer.validate(data)
        rendered = renderer.render(data, SKILL / "assets" / "report-template.html")
        self.assertIn('class="badge final">定稿', rendered)
        self.assertIn(data["summary"], rendered)
        self.write_case("long-zh", data)
        (self.folder / "long-zh.html").write_text(rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
