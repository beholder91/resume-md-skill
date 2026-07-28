# 参与贡献

感谢你改进 ResumeMD。项目优先保证内容保真、中文排版质量、自然分页和跨平台稳定性。

## 开发环境

```bash
git clone https://github.com/beholder91/resume-md
cd resume-md
python3 -m venv .venv
.venv/bin/pip install -e 'plugins/resume-md[dev]'
.venv/bin/pytest -q
```

macOS 首次运行可能需要 `brew install pango poppler`；Ubuntu/WSL 需要
`libpango-1.0-0`、`libpangoft2-1.0-0` 和 `poppler-utils`。

## 提交要求

- 示例和测试只能使用虚构身份与联系方式。
- 变更渲染逻辑后，必须渲染六份 `examples/` 样例并逐页检查。
- 不加入前端、远程服务、遥测或隐式 LLM 调用。
- 不为强制一页而缩小字号或删减内容。
- 新依赖需说明用途，并保持 CLI 可在隔离虚拟环境中安装。

提交 Pull Request 前请运行：

```bash
.venv/bin/pytest -q
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/resume-md/skills/resume-md
```

