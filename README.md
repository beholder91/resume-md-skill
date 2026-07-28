<div align="center">

# ResumeMD

**把简历材料交给 Agent，得到真正好看的 Markdown 与 PDF。**

[![CI](https://github.com/beholder91/resume-md-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/beholder91/resume-md-skill/actions/workflows/ci.yml)
[![MIT License](https://img.shields.io/badge/license-MIT-697C73.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-697C73.svg)](https://www.python.org/)
[![macOS & Linux](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-697C73.svg)](#限制)

[English](README.en.md) · [示例](examples) · [参与贡献](CONTRIBUTING.md)

</div>

> Markdown 是最适合与 LLM 交互的文件形式，但普通 Markdown 转 PDF 往往不好看；ResumeMD 开源一套中文优先、自然分页、结果稳定的简历渲染方案。

ResumeMD 是给 Codex、Claude Code 等 AI Agent 使用的本地 Skill。Agent 负责读取 PDF、DOCX、图片或文本并保真转换为 Markdown；ResumeMD 只负责确定性排版，不调用 LLM、不上传文件。

<table>
  <tr>
    <th align="center">中文</th>
    <th align="center">English</th>
  </tr>
  <tr>
    <td><img src="docs/assets/resume-zh.png" alt="ResumeMD 中文简历效果" width="440"></td>
    <td><img src="docs/assets/resume-en.png" alt="ResumeMD English resume preview" width="440"></td>
  </tr>
</table>

<br>

<p align="center"><strong>✦ 推荐安装方式 ✦</strong></p>

<h2 align="center">一句话，交给 Agent 安装</h2>

<p align="center">
  <strong>不用打开终端，不用记命令。</strong><br>
  复制下面这段话给 Codex 或 Claude Code，它会自动安装并完成渲染自检。
</p>

<p align="center">
  <kbd>复制提示词</kbd>
  &nbsp;→&nbsp;
  <kbd>Agent 自动安装</kbd>
  &nbsp;→&nbsp;
  <kbd>渲染自检通过</kbd>
</p>

```text
请安装这个项目为全局 Skill，并完成一次渲染自检：
https://github.com/beholder91/resume-md-skill
```

<p align="center"><strong>安装完成。现在直接把任务交给 Agent：</strong></p>

```text
根据 ./resume.pdf 输出一份中文简历 PDF
把 ./profile.docx 排版成英文简历，不要修改内容
重新渲染 ./resume.md，标题使用衬线字体
```

Skill 默认把结果写入 `resume-output/<name>.md` 和
`resume-output/<name>.pdf`。内容存在歧义时，Agent 会停下来询问，不自行猜测。

## 手动安装插件

### Codex

```bash
codex plugin marketplace add beholder91/resume-md-skill
codex plugin add resume-md@resume-md
```

### Claude Code

```bash
claude plugin marketplace add beholder91/resume-md-skill
claude plugin install resume-md@resume-md
```

也可以只安装本地渲染器：

```bash
git clone https://github.com/beholder91/resume-md-skill
python3 resume-md-skill/plugins/resume-md/skills/resume-md/scripts/install.py
~/.local/bin/resume-md doctor
```

安装器会创建独立虚拟环境，并执行一次真实 PDF 冒烟测试。macOS 需要
Pango；Linux/WSL 会按需下载经过 SHA-256 校验、固定版本的 Noto
Sans/Serif SC 字体。

## CLI

```bash
resume-md render resume.md \
  --output resume.pdf \
  --language auto \
  --style auto \
  --json
```

可用参数：

- `--language auto|zh-CN|en`
- `--style auto|sans|serif|hybrid`
- `--font-size 10.5`
- `--json`

诊断环境：

```bash
resume-md doctor
resume-md doctor --download-fonts
```

Python API：

```python
from resume_md import RenderOptions, TypographyStyle, render_pdf

result = render_pdf(
    markdown,
    RenderOptions(style=TypographyStyle.HYBRID),
)
open("resume.pdf", "wb").write(result.pdf)
```

## 工作原理

```text
PDF / DOCX / 图片 / 文本
           │  Agent 读取与保真转换
           ▼
      标准 Markdown
           │  ResumeMD 本地渲染
           ▼
 PDF/UA + 嵌入字体 + 自然分页
```

- 格式契约只规定结构，不润色、不翻译、不补充事实。
- WeasyPrint 负责 A4 排版，章节与条目按语义自然分页。
- PDF 输出可提取文本、保留安全链接并嵌入字体。
- macOS 保留 Apple Preview 的 CFF 字体兼容修复，避免中文乱码。
- 六份虚构中英文样例会在 macOS 与 Ubuntu CI 中真实渲染并检查。

## 隐私

- 完全本地运行，无账号、无上传、无遥测。
- ResumeMD 本身不调用任何 LLM。
- 输入和输出只存在于用户指定的本地目录。
- 示例数据全部虚构。

## 限制

首版支持 macOS、Linux 和 WSL，不支持原生 Windows、头像、多栏模板或云端服务。ResumeMD 不强制一页，也不会为了塞进一页而缩小字体、删除内容。

## 开发

```bash
python3 -m venv .venv
.venv/bin/pip install -e 'plugins/resume-md[dev]'
.venv/bin/pytest -q
```

项目采用 [MIT License](LICENSE)。按需下载的 Noto 字体采用
[SIL Open Font License 1.1](plugins/resume-md/licenses/OFL-1.1.txt)，详情见
[第三方声明](THIRD_PARTY_NOTICES.md)。
