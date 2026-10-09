# 安装与第一次使用

用户增长6步法是一套交给智能体使用的工作流程。安装后，你描述增长问题，智能体按需要追问，再把判断、行动和验证计划整理成报告。你不需要先学会六步法，也不需要会编程。

它采用 [Agent Skills 开放格式](https://agentskills.io/specification)，并非某个智能体产品专用。**格式通用不等于每个聊天工具都有安装入口**：请按下面与你环境相符的方式使用。

## 先选一种方式

| 你正在使用的环境 | 从哪里开始 |
| --- | --- |
| 智能体能访问 GitHub、写入文件，并支持安装 Skill | [方式一：让智能体协助安装](#方式一让智能体协助安装) |
| 本机有终端，想安装到 Claude Code、Cursor 等支持的工具 | [方式二：交互式安装命令](#方式二交互式安装命令) |
| 不使用终端，但工具有上传 Skill 的入口，或你能管理项目文件 | [方式三：下载后导入或复制](#方式三下载后导入或复制) |
| 工具不能安装 Skill，但能读取你提供的文件 | [本次对话临时使用](#不能安装时本次对话临时使用) |
| 只能发文字，不能读文件或生成文件 | [纯聊天环境](#纯聊天环境能做什么) |

## 方式一：让智能体协助安装

适用于具备联网、文件操作和 Skill 安装能力的智能体。复制下面整段发送给它；这是安装请求，还没有开始分析你的业务。

```text
请安装“用户增长6步法”Skill：
https://github.com/sushengs-creator/user-growth-six-steps/tree/main/skills/user-growth-six-steps

请按你当前产品支持的 Skill 安装方式操作，完整保留 SKILL.md、references、scripts 和 assets。
如果已有同名 Skill，先保留我修改过的内容，再更新。
完成后告诉我实际安装位置、适用范围，以及是否能读取参考文件、运行 Python 3 并生成 HTML 文件。
如果当前环境不能安装，请明确说明，并指导我使用本仓库安装指南中的导入或临时加载方式；不要把读取网页说成安装成功。
```

**安装成功后，再发送下面的开始口令：**

```text
请使用“用户增长6步法”（user-growth-six-steps）分析我的增长问题。
我的产品或业务是：【一句话说明】。
现在最想改善的是：【注册、首次使用、活跃、留存、转化等具体问题】。
已知数据和限制：【有多少写多少；不知道的可以写“暂时没有”】。
请一步步引导，优先每轮只问一个关键问题；信息足够后交付可打开的 HTML 增长方案和用于后续复盘的 JSON。
```

中文请求适用于已加载这套文件、能理解并执行其指引的智能体。原生快捷调用各不相同：Claude Code 和 Cursor 可使用 `/user-growth-six-steps`；`$user-growth-six-steps` 只用于支持这种语法的产品，不是通用命令。

## 方式二：交互式安装命令

电脑需具备 Node.js、npm/npx 和网络访问能力。建议使用 Node.js 当前 LTS 版本。打开终端；若只想在一个项目中使用，先进入那个项目文件夹，再执行：

```bash
npx skills add sushengs-creator/user-growth-six-steps --skill user-growth-six-steps
```

这是 Vercel Labs 的跨智能体 Skills CLI。根据屏幕提示完成：

1. 确认显示的智能体，必要时选择你使用的产品；工具有时会自动选中检测到的环境。
2. 选择 **Project**，表示仅供当前项目使用；选择 **Global**，表示本机个人环境中的多个项目可用。
3. 若出现安装方式选择，可采用默认选项；需要独立文件副本时选择 **Copy**。
4. 检查安装摘要，完成后到智能体中进行下文的使用验证。

主命令不限定 Codex，也不跳过交互。熟悉 CLI 后，可以用 `--agent claude-code`、`--agent cursor` 指定工具，用 `--global` 指定个人全局范围；这些选项都不代表自动同步到云端。

若提示找不到 `npx`，说明当前终端没有可用的 Node.js/npm 环境。你可以改用方式三，无须为了使用这套方法先配置终端。工具与选项见 [Skills CLI 官方说明](https://github.com/vercel-labs/skills)。

## 方式三：下载后导入或复制

1. [下载单 Skill 安装包](https://github.com/sushengs-creator/user-growth-six-steps/raw/refs/heads/main/dist/user-growth-six-steps.zip)，保存 `user-growth-six-steps.zip`。
2. 应用有“上传 Skill”入口时，直接上传这个 ZIP。它已经按单个 Skill 打包，无须自行压缩。
3. 需要复制文件夹的应用，先解压，找到 **`user-growth-six-steps` 整个文件夹**，放到对应目录。不要只复制 `SKILL.md`。

仓库的 **Code → Download ZIP** 下载的是整个项目源码，不能直接当成单 Skill 上传；首次使用请选择上面的现成安装包。

这个文件夹应保留以下结构：

```text
user-growth-six-steps/
├── SKILL.md
├── references/
├── scripts/
└── assets/
```

### Claude 网页版或支持此入口的 Claude 桌面端

1. 下载上面的单 Skill ZIP，保留 `.zip` 文件用于上传。若浏览器自动解压，请保留原 ZIP，或将解压后的 `user-growth-six-steps` 文件夹重新压缩；不要上传整个仓库源码包。
2. 个人账号进入 **Settings → Capabilities（设置 → 能力）**，启用 **Code execution and file creation（代码执行与文件创建）**。团队或企业账号如被限制，需要组织管理员在 **Organization settings → Plugins & skills → Policy** 确认代码执行和 Skills 已启用。
3. 进入 **Customize → Skills → + → Create skill → Upload a skill**，上传这个单 Skill ZIP，然后启用 `user-growth-six-steps`。
4. 打开新对话，先发送下文的验证口令，再发送你的增长问题。

找不到入口时，先确认正在使用 Claude 网页版且登录了目标账号，再检查能力开关；组织账号检查管理员权限。若当前界面仍不提供 Skill 上传，可按本文的临时加载方式使用能读取文件的环境，或使用 Claude Code 等有明确安装入口的工具，不能把普通附件上传当成原生安装。[官方导入说明](https://support.claude.com/en/articles/12512180-use-skills-in-claude)、[官方打包要求](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)。

### Claude Code、Cursor 等本机智能体

| 产品 | 复制到当前项目中的位置 | 原生手动调用 |
| --- | --- | --- |
| Claude Code | `.claude/skills/user-growth-six-steps/` | `/user-growth-six-steps` 后写你的问题 |
| Cursor | `.cursor/skills/user-growth-six-steps/`，也支持 `.agents/skills/user-growth-six-steps/` | 在 Agent 对话中输入 `/`，选择 `user-growth-six-steps` |

表中的目录以项目根目录为起点。个人全局目录和云端规则请查 [Claude Code 官方文档](https://code.claude.com/docs/en/skills)、[Cursor 官方文档](https://cursor.com/docs/skills)。复制后在相应项目中打开新会话，再检查是否识别。

Cursor 的 **From GitHub Repository** 图形界面入口目前用于带 marketplace 配置的插件仓库。本仓库提供的是普通 Skill，因此这里使用文件夹复制或前面的 CLI 方式。

其他支持 Agent Skills 的产品，请把同一个完整文件夹放到其官方文档指定的位置，或使用其上传入口；不要假设所有产品都读取 `.claude/skills`、`.cursor/skills` 或 `.agents/skills`。

## 怎样确认真的可以使用

安装器显示完成后，在你准备开展工作的智能体里发送：

```text
请检查你是否已经加载 user-growth-six-steps。
请实际读取它的 SKILL.md，并检查 references/book-methods.md、references/report-schema.md、scripts/render_report.py 和 assets/report-template.html 是否可访问。
告诉我已读取的文件、当前是否能运行 Python 3，以及能否生成供我打开或下载的 HTML 文件。
先不要诊断业务，也不要把没有读取的文件说成已读取。
```

如果工具能展示 Skill 名单，确认其中有 `user-growth-six-steps`。只有名称出现，还不足以证明所有参考文件和报告脚本可用；开始一次[操作示范](../README.md#操作示范)，收到真实报告文件，才完成了使用验证。

完整报告优先由包内 Python 3 脚本生成，仅使用 Python 标准库。没有 Python 但能创建文件时，可由宿主按相同内容规范生成，并明确未执行配套脚本校验。**你负责描述业务和回答问题，智能体负责读取材料、组织报告并运行脚本**，通常不需要你手工编辑 JSON。

## 不能安装时：本次对话临时使用

如果工具能读取工作区或附件，但没有原生 Skill 机制，可以把整个文件夹放入可读取的工作区；支持解压附件的工具也可以接收该文件夹的 ZIP。然后发送：

```text
我已提供 user-growth-six-steps 完整文件夹。
请先实际读取其中 SKILL.md，并按当前问题需要读取它引用的参考文件，在本次对话按这些指引工作。
这属于临时加载，不要称为已安装或承诺下次自动可用。
我的增长问题是：【填写问题】。
请优先每轮问一个关键问题；可以创建文件和运行 Python 3 时，按包内脚本交付 HTML 和 JSON；缺少文件或执行能力时先说明具体限制。
```

如果工具不能访问某个必需文件，请补充该文件或换到可读取完整包的环境。仅发送 README 的网址不等于已经加载方法材料。

## 纯聊天环境能做什么

只能收发文字、不能读取文件的环境，无法完整运行这套 Skill。你仍可参照[六步方法论](methodology.md)讨论问题；若手动提供所需指引和参考内容，可以进行一次方法练习。这样的练习不算安装，也不能保证产生可下载的真实 HTML 文件。

若只能得到 HTML 源码，可以手工保存为 `.html` 后打开；这属于降级交付，应明确与完整 Skill 生成并校验的报告区分。

## 换电脑、云端或新会话时

本机安装成功不代表云端环境已经获得文件。云端任务需要使用该产品支持的账号上传、同步机制，或从项目仓库中读取 Skill。临时加载的环境在新会话可能需要重新提供文件；项目安装则要进入同一个项目。每次切换环境，先用上面的验证口令检查，不要只凭旧会话说“安装过”就认定可用。

接口名称和支持范围可能随产品更新。本指南的产品入口与 CLI 行为于 **2026-10-09** 对照以上官方资料核验；这是文档核验，不代表已在每个产品中完成实际运行测试。

维护者更新技能文件后，在仓库根目录运行 `python3 scripts/package_skill.py` 重新生成安装包；脚本会逐文件核对 ZIP 与源目录一致。
