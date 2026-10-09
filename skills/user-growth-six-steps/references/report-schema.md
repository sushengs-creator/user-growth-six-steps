# HTML 报告输入与生成规范

## 用法

把已经确认的业务材料组织为 UTF-8 JSON。当前环境可执行 Python 时优先用配套脚本；根据实际解释器与路径调整以下命令，不假定每个系统都叫 `python3`：

```bash
python3 scripts/render_report.py /absolute/path/report.json /absolute/path/report.html
```

从 Skill 目录之外运行时，使用脚本的完整路径。输出目录需要事先存在。默认拒绝覆盖已有文件；确需替换同一份报告时加 `--overwrite`。脚本只使用 Python 标准库，生成包含内嵌样式的单文件 HTML，无网络字体、CDN 或 JavaScript 依赖。完成后打开文件，检查中文、长文本、表格和打印预览，再把真实文件链接交付给用户。脚本成功输出文件绝对路径，失败向标准错误输出原因并返回退出码 2。

脚本仅做校验与排版：不计算转化率，不推断瓶颈，不补写用户事实、来源、预期收益或日期，也不决定是否可以定稿。`final` 是调用者提供的报告状态，不是脚本完成来源审核的证明。方法论忠实性、事实真伪、因果推断和建议是否适用，仍须在内容生成阶段核验。

## 宿主能力与交付方式

- **能执行 Python 并创建文件**：用配套脚本校验和渲染。读取成功输出，核对实际 HTML 与 JSON 内容；输入错误先按报错修复，不通过换方式跳过校验。Python 3.9 与 3.12 已实测，其余版本不据此声称兼容。
- **不能执行 Python，但能创建文件或附件**：按下述同一字段规范保存 JSON，并直接生成语义完整的单文件 HTML。保留事实、假设、未知值、六步真实状态、行动、验证和来源限制，不能在排版时改变含义。使用 UTF-8、内嵌样式和适合阅读/打印的表格；将所有业务文本按纯文本转义，来源只使用符合本规范的 HTTP/HTTPS 链接，不添加外部脚本或网络资源。内容和文件均需核对，明确注明“由宿主直接生成，未执行配套脚本校验”；视觉预览未完成时另说明。不要为了出文件擅自安装解释器或配置运行环境。
- **只能输出文字**：继续完成能支持的判断。用户需要 HTML 时，可提供完整 HTML 源码和 JSON，说明如何用 UTF-8 分别保存为 `.html`、`.json`；这是待手动保存的输出，不称为已生成文件，不给虚构文件路径。资料也无法读取时，如实缩小到已读材料支持的分析范围。

交付链接服从宿主的文件机制：本地文件链接必须指向真实文件；云端使用用户可下载的附件或文件链接，服务器绝对路径不能替代下载地址。初次交付说明“下载 HTML，用浏览器打开；保存 JSON，下次附上继续更新”。换会话不会自动继承文件，除非宿主确实提供该能力。仅交付给当前用户，不因报告可分享而自动发布到公开仓库或发送给第三方。

## 数据约定

- JSON 顶层必填 `schema_version: 1`、`status: "draft" | "final"` 和非空 `title`。其余字段可省略；列表无内容用 `[]`，未知标量用 `null`。可选字符串也接受 `null`。不能用 0 代替未知；明确的数字 0 会正常显示。
- 不接受未定义字段、重复 JSON 键、重复步骤、重复来源 ID、引用不存在的来源、NaN/Infinity、布尔型指标值或无效 Unicode 字符。字段拼写出错时会报错，不悄悄丢弃。
- 文本全部按纯文本转义；不支持 Markdown 或 HTML。换行会保留。不要为了排版在数据中加入标签。
- 来源链接只接受 `http://` 或 `https://`，必须有主机名，不允许空白、控制字符或 URL 内嵌账号密码；本地 PDF 用 `url: null` 并填写文件名和章节定位。来源本身是否可靠、是否已阅读由调用者核验。
- 所有对象的 `source_ids` 均可省略，存在时是来源 ID 数组。没有关联会显示“未关联来源”，不自动为业务事实匹配图书引用。业务事实的依据可记为 `type: "user"`。
- 缺失步骤仍显示在六步导航中，但标为“未填写”，不自动变成已完成。

## 字段定义

| 顶层字段 | 类型 | 含义 |
|---|---|---|
| `schema_version` | 整数，必填 | 当前为 1 |
| `status` | 枚举，必填 | `draft` 草案；`final` 定稿 |
| `title` | 非空字符串，必填 | 报告标题 |
| `subtitle` | 字符串或 null | 一句话说明 |
| `created_at` | 字符串或 null | 由调用者提供的日期，不自动猜测 |
| `subject` | 字符串或 null | 分析对象 |
| `summary` | 字符串或 null | 当前判断，需明确不确定性 |
| `facts` / `hypotheses` / `gaps` | 证据对象数组 | 已知事实 / 待验证假设 / 信息缺口 |
| `steps` | 步骤对象数组 | 本次已推进的步骤，最多 6 个、不可重复 |
| `metrics` | 指标对象数组 | 指标值及其口径 |
| `actions` | 行动对象数组 | 可执行行动与继续、停止依据 |
| `verification` | 验证对象数组 | 需要证实或推翻的假设与验证方法 |
| `sources` | 来源对象数组 | 来源及真实阅读范围 |
| `limitations` | 非空字符串数组 | 适用边界、未决事项及未核验内容 |

**证据对象**：`text`（必填非空字符串）、`note`（字符串或 null）、`source_ids`（数组）。`hypotheses` 中的正文应表述为假设，而不是已经证实的事实。

**步骤对象**：`id` 和 `state` 必填；`finding`（当前发现）、`decision`（判断与决定）、`next_question`（下一项待确认）均为字符串或 null；另可有 `source_ids`。

| `id` | 固定显示名 |
|---|---|
| `north_star` | 北极星指标 |
| `growth_mode` | 增长驱动模式 |
| `core_lever` | 核心杠杆 |
| `magic_number` | 魔法数字 |
| `growth_strategy` | 增长策略 |
| `ab_validation` | 策略效果验证 |

步骤状态为 `done`（已完成）、`current`（进行中）、`pending`（待推进）、`blocked`（待补资料）。不要用“已填写”冒充已完成判断。

第6步保留原书名称“通过AB实验验证用户增长策略效果”；报告显示中性名称“策略效果验证”，兼容字段 `ab_validation` 保持不变。实际采用随机AB、前后观察或用户反馈，在该步发现及 `verification.method` 中写明；前后观察形成阶段决定也不能显示或表述成随机AB已经完成。局部指标已定义不等于北极星步骤完成，未涉及步骤标明本轮未核对。

**指标对象**：`name` 必填；`value`、`numerator`、`denominator` 为字符串、有限数字或 null；`unit`、`definition`、`population`、`period` 为字符串或 null；另可有 `source_ids`。比率由内容阶段按已确认分子、分母计算，脚本不替代统计判断。

**行动对象**：`title` 必填；`owner`、`timeframe`、`scope`、`description`、`success_criterion`、`stop_criterion` 为字符串或 null；另可有 `source_ids`。`success_criterion` 表示继续依据，并非保证实现的收益。无依据时填 null，不能填虚构增长幅度。

**验证对象**：`hypothesis` 必填；`method`、`population`、`primary_metric`、`guardrails`、`sample_plan`、`duration`、`decision_rule`、`risks` 为字符串或 null；另可有 `source_ids`。

**来源对象**：`id`（必填，1–64 位英文字母、数字、下划线或连字符）、`title`（必填）、`type`（必填，`book` / `article` / `user` / `other`）、`url`（http/https 字符串或 null）、`location`（章节、页码、时间或段落）、`coverage`（`full` / `partial` / `unread` / `unavailable` 或 null）、`note`（说明）。`coverage` 仅描述读取情况，不证明内容或业务结论为真。

## 完整有效示例

以下为渲染演示，所有业务材料均为虚构，不是本书案例，也不是用户的真实业务。调用时替换成实际材料；不要把演示数据带入正式报告。示例只引用其自身的演示输入记录，未假装引用图书或文章。

```json
{
  "schema_version": 1,
  "status": "draft",
  "title": "演示项目｜用户增长诊断草案",
  "subtitle": "此示例仅用于检查报告生成，不代表真实业务结论。",
  "created_at": "2026-10-08",
  "subject": "演示记账工具（虚构）",
  "summary": "目前仅能确认存在激活体验的待验证问题；尚不足以认定主要增长瓶颈。",
  "facts": [
    {
      "text": "演示输入称产品面向小商户，团队只有两人。",
      "note": "虚构输入；在真实报告中应标明实际提供者和时间。",
      "source_ids": ["DEMO_INPUT"]
    }
  ],
  "hypotheses": [
    {
      "text": "第一次操作后的反馈不清晰，可能妨碍部分用户完成核心任务。",
      "note": "尚无足够证据证明它是主因，也没有量化其影响。",
      "source_ids": []
    }
  ],
  "gaps": [
    {
      "text": "缺少有效注册用户的完整观察窗口和任务完成事件定义。",
      "note": null,
      "source_ids": []
    }
  ],
  "steps": [
    {
      "id": "north_star",
      "state": "current",
      "finding": "已有业务对象，尚未确认能代表用户持续获得价值的指标。",
      "decision": null,
      "next_question": "用户通过这个产品持续完成的核心任务是什么？",
      "source_ids": ["DEMO_INPUT"]
    },
    {
      "id": "growth_mode",
      "state": "pending",
      "finding": null,
      "decision": null,
      "next_question": null,
      "source_ids": []
    },
    {
      "id": "core_lever",
      "state": "blocked",
      "finding": "尚无口径一致的数据支持杠杆判断。",
      "decision": null,
      "next_question": "可以取得哪些用户行为记录？",
      "source_ids": []
    },
    {
      "id": "magic_number",
      "state": "pending",
      "finding": null,
      "decision": null,
      "next_question": null,
      "source_ids": []
    },
    {
      "id": "growth_strategy",
      "state": "pending",
      "finding": null,
      "decision": null,
      "next_question": null,
      "source_ids": []
    },
    {
      "id": "ab_validation",
      "state": "pending",
      "finding": null,
      "decision": null,
      "next_question": null,
      "source_ids": []
    }
  ],
  "metrics": [
    {
      "name": "首次核心任务完成率（候选）",
      "value": null,
      "unit": "%",
      "definition": "需先确认何为有效注册、核心任务完成及观察窗口。",
      "numerator": null,
      "denominator": null,
      "population": "目标用户范围待确认",
      "period": null,
      "source_ids": []
    }
  ],
  "actions": [
    {
      "title": "整理现有证据",
      "owner": "产品负责人（待确认）",
      "timeframe": "本次诊断之后，时间待确认",
      "scope": "现有用户行为记录与反馈",
      "description": "先对齐注册与核心任务完成事件定义，标明哪些记录具备完整观察窗口。",
      "success_criterion": "能够用同一口径复核人数与比例；不是承诺业务增长。",
      "stop_criterion": "若记录无法确认用户或时间，先修复数据，不据此得出增长结论。",
      "source_ids": []
    }
  ],
  "verification": [
    {
      "hypothesis": "操作反馈不清晰可能妨碍完成任务。",
      "method": "先复核反馈与行为记录，后续验证设计待补充。",
      "population": null,
      "primary_metric": null,
      "guardrails": null,
      "sample_plan": null,
      "duration": null,
      "decision_rule": "资料不足时不判定假设成立。",
      "risks": "观察到相关性不代表已经识别因果关系。",
      "source_ids": []
    }
  ],
  "sources": [
    {
      "id": "DEMO_INPUT",
      "title": "渲染示例中的虚构输入记录",
      "type": "user",
      "url": null,
      "location": "本示例 facts 字段",
      "coverage": "full",
      "note": "仅为演示；不代表实际用户提供的材料，也不属于图书证据。"
    }
  ],
  "limitations": [
    "全部业务材料均为虚构演示，不能用于现实决策。",
    "未提供图书或文章证据，因此不声称已经完成方法论的来源核验。",
    "尚未确认目标指标、分母及观察周期；未知值保持为 null。"
  ]
}
```
