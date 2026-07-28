---
name: resume-md
description: 将 Markdown、文本、PDF、DOCX 或图片中的中英文简历材料转换为保真 Markdown，并用本地 ResumeMD 渲染成美观、自然分页、可提取文本的 PDF。适用于用户要求根据现有简历生成、排版、重新渲染或导出 PDF；也适用于只要求把任意简历材料规范化为 ResumeMD Markdown 的场景。
---

# ResumeMD

把 Agent 的内容识别能力与本地确定性排版器组合起来。ResumeMD 不调用 LLM，也不上传文件。

## 处理流程

1. 读取用户明确指定的输入文件。支持 Markdown、纯文本、PDF、DOCX 和图片；使用当前环境已有的文件读取能力提取文字。
2. 根据原始材料自动判断中文或英文。若用户明确指定语言，遵循用户要求；翻译只在用户明确要求时进行。
3. 读取对应格式契约：
   - 中文：`references/format-zh.md`
   - 英文：`references/format-en.md`
4. 只做信息提取和结构转换。不得擅自润色、删减、补充、合并或虚构内容。无法可靠识别的文字必须标记并询问用户，不得猜测。
5. 默认创建 `resume-output/`，并写入 `<输入文件名>.md` 与 `<输入文件名>.pdf`。若同名文件已存在且用户未要求覆盖，选择带数字后缀的新文件名。
6. 检查 `resume-md` 是否可执行。若缺失，运行本 Skill 的 `scripts/install.py`。安装失败时，把脚本给出的系统依赖修复命令告诉用户并执行用户允许的修复。
7. 执行：

   ```bash
   resume-md render INPUT.md --output OUTPUT.pdf --language auto --style auto --json
   ```

8. 检查命令成功、PDF 页数大于零、文本可提取且字体已嵌入。有 PDF 视觉检查能力时逐页检查裁切、重叠、乱码和异常分页。
9. 返回 Markdown 与 PDF 两个文件，并简要报告页数、识别语言、字体和样式。

## 用户选项

- 用户要求衬线标题时使用 `--style hybrid`。
- 用户要求全部衬线时使用 `--style serif`。
- 用户要求无衬线时使用 `--style sans`。
- 用户指定正文字号时使用 `--font-size`；允许范围为 8.5–14pt。
- 用户只要求重新渲染现成 Markdown 时，不修改其内容。

## 边界

- 不把 ResumeMD 描述成简历写作、评价或 ATS 优化工具。
- 不强制一页，不为塞进一页缩小字体或删除内容。
- 不使用远程图片、原生 HTML、JavaScript 链接或本地文件链接。
- 原材料存在关键信息歧义时停止转换并询问用户。

