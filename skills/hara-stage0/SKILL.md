---
name: hara-stage0
description: Stage 0 脚本式功能提取。用于从功能文档或 source_extraction JSON 的“功能清单”表格中读取“功能”列，并按功能名匹配正文标题生成最小 output/<RUN_ID>_stage0_function_mapping.json。不要用于故障、危害、SEC、ASIL 或安全目标分析。
---

# Stage 0：功能提取

## 职责边界

只提取功能。不要读取 HARA 风险知识库，不要推导功能故障，不要生成整车危害。Stage 0 不调用大模型做功能识别，标准路径必须使用脚本生成。

## 输入输出

- 输入：功能文档路径或 `output/<RUN_ID>_source_extraction.json`。
- 输出：`output/<RUN_ID>_stage0_function_mapping.json`。
- 必读契约：`references/json-contracts.md`。

## 上下文加载

1. 读取 `references/json-contracts.md`，确认 Stage0 最小字段。
2. 读取 `references/stage0-function-extraction.md`，确认脚本匹配规则。
3. 本阶段不要读取 `knowledge-base/automotive/hara`。

## 规则

- 功能全集只来自包含“功能清单”的表格，且只读取列头精确为“功能”的那一列。
- 不从正文子标题中新增功能；正文只用于匹配清单功能并生成描述。
- 匹配正文标题时忽略标题行中的空格，功能名允许与标题名在“功能”后缀上有无差异。
- 匹配到某个功能标题后，将该标题及其所有子级标题和内容放入 `detail_text`；图片不进入描述。
- 将“工作电源挡位”“功能逻辑”“触发条件”“边界条件”等子章节合并进父功能的 `detail_text`，不要作为独立功能。
- `Function_ID` 连续编号：`F001`、`F002`、`F003`，不得跳号。
- `detail_text` 必须保留源文档原始技术表述，不要摘要改写。
- Stage0 行级字段只保留 `Function_ID`、`extracted_function_name`、`detail_text`。

## 执行流程

1. 如果输入是原始文档，直接运行 Stage0 生成脚本；需要留存抽取中间件时加 `--source-out`。
2. 如果已有 source extraction JSON，用 `--source-extraction` 运行 Stage0 生成脚本。
3. 标准流程加 `--write-contexts`，同时生成 `output/<RUN_ID>_stage1_context_<Function_ID>.json`，供 Stage1/2/3 直接引用对应功能描述。
4. 只写 UTF-8 JSON，不输出 Markdown 包裹。
5. 返回前运行验证并修正结构问题；验证失败时修 JSON 文件，不用解释代替修复。

## 验证

```text
python tools/hara/generate_stage0_function_mapping.py --input <function_doc_path> --out output/<RUN_ID>_stage0_function_mapping.json --run-id <RUN_ID> --write-contexts
# 或：
python tools/hara/generate_stage0_function_mapping.py --source-extraction output/<RUN_ID>_source_extraction.json --out output/<RUN_ID>_stage0_function_mapping.json --run-id <RUN_ID> --write-contexts
python tools/hara/check_stage_json.py --stage stage0 --json output/<RUN_ID>_stage0_function_mapping.json
```

## 返回

返回 `status`、`function_count`、识别到的 `system`、`output_file` 和生成的单功能 context 文件。Stage 0 通过机器校验后直接进入 Stage 1，不再进入 Stage 0R。
