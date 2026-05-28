# Stage 0: 功能提取

目标：用确定性脚本从功能文档提取完整功能清单和每个功能的背景材料。Stage 0 不读取任何 HARA 知识库，也不调用大模型判断功能边界。

## 输入文档预处理

如果输入是 `.docx`、`.doc`、`.pdf`、`.txt` 或 `.md` 文件，可以先规范化为抽取 JSON：

```text
python tools/hara/extract_function_doc.py --input <function_doc_path> --out output/<run_id>_source_extraction.json
```

也可以直接让 Stage0 生成脚本读取原始文件：

```text
python tools/hara/generate_stage0_function_mapping.py --input <function_doc_path> --out output/<run_id>_stage0_function_mapping.json --run-id <run_id> --write-contexts
```

已有抽取 JSON 时：

```text
python tools/hara/generate_stage0_function_mapping.py --source-extraction output/<run_id>_source_extraction.json --out output/<run_id>_stage0_function_mapping.json --run-id <run_id> --write-contexts
```

抽取 JSON 包含 `blocks` 和 `full_text`。常见 block 类型：

- `heading`：章节标题，例如 `2.3.1 <功能名称>功能`
- `table`：表格行，例如功能清单表
- `paragraph`：正文段落，例如 `2.3.1.2 功能逻辑` 下的条款

如果 PDF 无法抽取文本，说明需要 OCR 或可复制文本版文档；如果旧版 `.doc` 无法抽取，说明需要转换为 `.docx` 或安装本地 `antiword/catdoc`。不要凭文件名猜测功能。

## 提取规则

1. 功能全集只来自包含“功能清单”的表格。
2. 在该表格内查找列头精确为 `功能` 的列，该列每一行就是一个功能名称。
3. 不从正文标题中新增功能；正文标题只用于给清单功能绑定描述。
4. **功能标题匹配**：
   - 正文标题格式通常是 `<编号> <功能名称>`，如 `2.2 静态开关拉起` 或 `2.2 静态开关拉起功能`。
   - 标题编号不固定，只要求是数字章节号。
   - 匹配时忽略标题行和功能名中的空格。
   - 功能名与标题名允许在末尾 `功能` 二字上有无差异。
5. **detail_text 汇总**：
   - 对每个清单功能，找到匹配功能标题后，将该标题及其所有子级标题和内容汇总为 `detail_text`。
   - 包括：工作电源挡位、功能逻辑、触发条件、状态前提、动作结果、例外处理、提示信息、不响应条件等。
   - 图片不放入 `detail_text`。
   - 当出现下一个非该标题子级的标题时停止。
6. 如果清单中有功能但未找到详细章节，也要保留该功能，并在 `detail_text` 填 `nan`，在 `review_log` 记录缺少详细说明。
7. `非功能逻辑类`、诊断、标定、接口、日志、状态判断等不能从功能清单中删除。Stage 1 仍必须对该功能行进行故障分析；若某些引导词不适用，在对应单元格填 `nan`。

`detail_text` 是后续阶段的重要背景。Stage 1/2/3 都必须优先用它判断故障、危害和场景合理性。

## 常见错误

| 错误类型 | 表现 | 正确做法 |
|---------|------|---------|
| 子章节提取为功能 | 把 `工作电源挡位`、`功能逻辑` 等子章节提取为独立功能 | 只提取主功能标题（`...功能`），子章节内容合并到 `detail_text` |
| 过度拆分 | 把一个功能的多个条件拆成多个子功能 | 保持功能完整性，所有描述内容放在一个功能的 `detail_text` 中 |
| 正文新增功能 | 清单没有该功能，但正文有看似功能的子标题 | 不新增；功能全集只来自“功能清单”表格 |
| 编号混淆 | 把 `2.3.1.1`、`2.3.1.2` 当作功能编号 | 这些是子章节编号，应进入父功能 `detail_text` |

## 示例

### 错误示例（不要这样做）

```json
{
  "Function_ID": "EPB_StaticPull_Activation",
  "extracted_function_name": "静态开关拉起功能",
  "sub_functions": [
    {
      "Function_ID": "EPB_StaticPull_PowerRequirement",
      "extracted_function_name": "工作电源挡位要求",
      ...
    }
  ]
}
```

### 正确示例（应该这样做）

```json
{
  "Function_ID": "F001",
  "extracted_function_name": "静态开关拉起功能",
  "detail_text": "2.3.1 静态开关拉起功能\n\n2.3.1.1 工作电源挡位\nON/OK挡电源挡位工作。备注：在EPB休眠后，整车电源处于OFF挡位时，拉起EPB开关，EPB能被唤醒并执行拉起。\n\n2.3.1.2 功能逻辑\n（1）车辆静止（车速≤3km/h）且EPB处于已释放（Released）状态，拉起EPB开关执行拉起，车辆驻车。\n（2）EPB处于已拉起(Applied)状态，EPB开关拉起，仪表上显示文字提示"电子驻车已启动"，EPB不响应。\n..."
}
```
