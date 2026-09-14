# Skill Manager

管理、审计和维护 Codex Skills，默认先报告与计划，再按授权修改。
Audit and maintain Codex skills, with reports and plans before authorized changes.

[中文](#中文) · [English](#english)

## 中文

### 功能

- **只读 CLI**：inventory、audit、snapshot、diff；输出 JSON，不修改被审计的目录。
- **结构与资源检查**：SKILL.md frontmatter、agents/openai.yaml、Markdown 本地链接、Python 脚本语法，以及 tests/evals 缺失提示。
- **冲突与过期候选**：同名、相同 description、词汇重叠和文件年龄检查，供进一步人工或 Agent 复核。
- **维护流程**：指导 Agent 执行 update、merge、split、rename 和元数据再生成；包含暂存、能力映射、备份、diff、哈希复核与验证。
- **验证**：调用本机官方 skill-creator 的 quick_validate.py，提供单元测试与行为评估场景。

维护操作由 Agent 按规范执行；CLI 没有自动修复、删除或覆盖命令。

### 安装

将仓库克隆到本机实际使用的用户级 skills 目录，目录名保持为 `skill-manager`。本项目遵循本机 skill-creator 的位置约定：设置了 `CODEX_HOME` 时使用其下的 `skills`，否则使用 `~/.codex/skills`。如果目标已存在，先检查差异，不要覆盖。

PowerShell 示例：

```powershell
$skillRoot = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $HOME '.codex' 'skills' }
git clone https://github.com/TokaiTieo/skill-manager.git (Join-Path $skillRoot 'skill-manager')
```

CLI 需要 **Python 3.10+ 和 PyYAML**。如当前环境没有 PyYAML，可在自己选择的 Python 环境安装：

```text
python -m pip install PyYAML
```

### 使用

在 Codex 中请求：

```text
$skill-manager 检查我当前的 skills，输出健康报告和修改计划，先不要修改。
$skill-manager 为这两个 skill 制定合并方案，保留全部能力并给出 diff。
```

也可以在本仓库根目录运行 CLI。下面的路径是占位符，需要替换为真实路径；报告放在被审计的 skills 目录之外。

```text
python -X utf8 -B scripts/skill_manager.py inventory --root "<skills-root>"
python -X utf8 -B scripts/skill_manager.py audit --root "<skills-root>" --validator "<skill-creator>/scripts/quick_validate.py"
python -X utf8 -B scripts/skill_manager.py snapshot --root "<skills-root>"
python -X utf8 -B scripts/skill_manager.py diff --before "<before.json>" --after "<after.json>"
```

前三个命令支持重复传入 `--root`。将 snapshot 的标准输出保存为 UTF-8 JSON，可作为 diff 的输入。省略 `--validator` 时，官方验证状态为 Unknown。退出码 0 只表示命令完成，健康状态应查看 `findings`；JSON 报告的解释见[审计规范](references/audit.md)。

### 验证与边界

```text
python -X utf8 -B "<skill-creator>/scripts/quick_validate.py" .
python -X utf8 -B -m unittest discover -s tests -v
```

初始版本已通过官方结构验证与 **10 项单元测试**。[5 个行为评估场景](evals/cases.json)已提供，尚未运行独立模型评估。这些是已执行的本地验证结果，不是持续集成状态。

- 不自动执行其他 Skill 的脚本或测试；不把 fixture 内容当作真实用户事实。
- 词汇重叠不证明语义冲突，文件年龄不证明内容过期；远端链接与依赖可用性需另行核验。
- 静态链接检查覆盖 Markdown inline links；示例、动态路径及其他链接语法需要复核。
- 系统和插件管理的 Skills 只读处理。修改流程保留元数据中的 policy/dependencies。
- 快照可能包含源码与本地路径；不要自动公开。大于 2 MB 或非 UTF-8 的文件仅提供哈希差异。

## English

### Features

- **Read-only CLI**: inventory, audit, snapshot, and diff; JSON output without modifying audited directories.
- **Structure and resource checks**: SKILL.md frontmatter, agents/openai.yaml, local Markdown links, Python script syntax, and missing tests/evals.
- **Conflict and freshness candidates**: duplicate names, identical descriptions, lexical overlap, and file age for human or agent review.
- **Maintenance workflows**: agent guidance for updates, merges, splits, renames, and metadata regeneration, including staging, capability mapping, backups, diffs, hash rechecks, and validation.
- **Validation**: integration with the locally installed official skill-creator quick_validate.py, plus unit tests and behavioral evaluation scenarios.

Maintenance is performed by the agent following the documented workflow. The CLI has no automatic repair, deletion, or overwrite command.

### Installation

Clone this repository into your active user-level skills directory, keeping the folder name `skill-manager`. This project follows the local skill-creator location convention: `$CODEX_HOME/skills` when configured, otherwise `~/.codex/skills`. Inspect differences before updating an existing installation; do not overwrite it blindly.

PowerShell example:

```powershell
$skillRoot = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $HOME '.codex' 'skills' }
git clone https://github.com/TokaiTieo/skill-manager.git (Join-Path $skillRoot 'skill-manager')
```

The CLI requires **Python 3.10+ and PyYAML**. If PyYAML is unavailable, install it in your chosen Python environment:

```text
python -m pip install PyYAML
```

### Usage

Ask Codex:

```text
$skill-manager Audit my installed skills and produce a health report and maintenance plan without making changes.
$skill-manager Plan a merge of these two skills, preserving all capabilities and showing a diff.
```

Or run the CLI from the repository root. Replace placeholder paths with actual paths and keep reports outside audited skills directories.

```text
python -X utf8 -B scripts/skill_manager.py inventory --root "<skills-root>"
python -X utf8 -B scripts/skill_manager.py audit --root "<skills-root>" --validator "<skill-creator>/scripts/quick_validate.py"
python -X utf8 -B scripts/skill_manager.py snapshot --root "<skills-root>"
python -X utf8 -B scripts/skill_manager.py diff --before "<before.json>" --after "<after.json>"
```

The first three commands accept repeated `--root` arguments. Save snapshot stdout as UTF-8 JSON to use it as diff input. Omitting `--validator` leaves official validation Unknown. Exit code 0 means command completion, not a clean health assessment; inspect `findings`. See the [audit rules](references/audit.md) for report interpretation.

### Validation and limitations

```text
python -X utf8 -B "<skill-creator>/scripts/quick_validate.py" .
python -X utf8 -B -m unittest discover -s tests -v
```

The initial version passed official structural validation and **10 unit tests**. [Five behavioral evaluation scenarios](evals/cases.json) are included; independent model evaluations have not been run. These are recorded local validation results, not a CI status.

- Other skills' scripts/tests are not executed automatically, and fixture content must not become real user facts.
- Lexical overlap does not establish semantic conflict; file age does not establish obsolescence. Remote links and dependency availability require separate checks.
- Static link checks cover Markdown inline links; examples, dynamic paths, and other link syntax require review.
- System/plugin-managed skills are handled read-only. Maintenance workflows preserve metadata policy/dependencies.
- Snapshots may contain source text and local paths; do not publish them automatically. Files larger than 2 MB or not encoded as UTF-8 receive hash-only diffs.

## 目录 / Repository layout

```text
skill-manager/
├── README.md
├── SKILL.md
├── agents/openai.yaml
├── scripts/skill_manager.py
├── references/
│   ├── audit.md
│   ├── maintenance.md
│   └── validation.md
├── evals/cases.json
└── tests/test_skill_manager.py
```

[审计 / Audit](references/audit.md) · [维护 / Maintenance](references/maintenance.md) · [验证 / Validation](references/validation.md)
