# HARA JSON 契约 - Stage 0

所有阶段文件必须是 UTF-8 JSON object。不要输出 Markdown 表格、代码围栏、额外说明文本或数组作为顶层结构。

## 完整输出 Schema（严格遵循）

```json
{
  "meta": {
    "run_id": "<RUN_ID>",
    "stage": "stage0",
    "generated_at": "ISO时间戳",
    "source_file": "<输入文件路径或direct_text>",
    "system": "<识别到的系统或unknown>",
    "knowledge_files_used": []
  },
  "function_mapping": [
    {
      "Function_ID": "F001",
      "extracted_function_name": "<源文档中的功能名称>",
      "detail_text": "<匹配功能标题及其全部子级标题和内容，图片除外>"
    }
  ],
  "review_log": []
}
```

## 本阶段文件

文件：`output/<run_id>_stage0_function_mapping.json`

只允许顶层 key：`meta`、`function_mapping`、`review_log`。

### function_mapping 字段

- `Function_ID`
- `extracted_function_name`
- `detail_text`

字段含义：

- `Function_ID`：脚本按功能清单顺序生成的连续编号，格式 `F001`、`F002`。
- `extracted_function_name`：来自“功能清单”表格中列头为“功能”的单元格原文。
- `detail_text`：从功能文档中匹配到的功能标题及其所有子级标题和内容；不包含图片。找不到匹配章节时填 `nan`，并在 `review_log` 记录 warning。

Stage0 行级字段保持最小化，不再输出类别、备注、证据块、系统匹配等冗余字段。下游 Stage1/2/3 只依赖 `Function_ID`、`extracted_function_name` 和 `detail_text`。
