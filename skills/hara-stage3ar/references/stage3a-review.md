# Stage 3AR 场景评审

本文件只定义 Stage3A 场景评审。SEC 评级评审见 `hara-stage3br`，Stage3A/3B 合并一致性由 `check_stage_json.py --stage stage3` 校验。

## 输出结构

`output/<RUN_ID>_stage3a_<MF_ID>_review.json`

```json
{
  "meta": {
    "run_id": "<RUN_ID>",
    "stage": "stage3a_review",
    "mf_id": "<MF_ID>",
    "target_file": "output/<RUN_ID>_stage3a_<MF_ID>_scenarios.json",
    "generated_at": "ISO时间戳"
  },
  "overall_result": "pass/failed",
  "issues": [],
  "fixes": [],
  "per_scenario_reviews": []
}
```

## 检查点

- `max_asil_planning` 是否围绕当前 MF 的可信最高风险路径，不是随机组合场景。
- 每条场景是否真实、独立、不重复。
- 场景是否在功能运行域内。
- 六大场景字段是否与 `scenario_reasoning.场景条件相关性检查` 一致。
- 危害事件是否由 MF、整车危害和场景条件自然推出。
- 运动方向、道路条件、风险对象位置、驾驶员是否在车上是否自洽。
- 当前 MF 故障是否是危害事件的必要原因；如果没有该故障，天气、路面或交通条件本身是否仍会导致同一事件。
- 非预期纵向移动/溜车是否有真实力源：坡道重力、驱动/传动输出或外力推动。低附着路面、降雨、冰雹、视线受阻不能单独作为 EPB 驻车溜车原因。
- `道路条件` 与 `附加条件` 是否一致：写了下坡、上坡、坡度或陡坡时，不能把道路条件选成 `直道`。
- 风险对象是否与碰撞对象一致：前车/停放车辆、对向来车、行人不能混写。
- 天气、能见度、玻璃起雾等条件如果改变当前 MF 到危害事件的链路，应标为危害事件因果相关；如果不改变因果链但影响 SEC 阶段 S/E/C，也必须标为 `相关`，并写明“相关，不影响危害事件因果链，但影响SEC的X评级，理由”。只有既不影响因果链也不影响 SEC，或与其他条件互斥时，才可标为 `不涉及`。
- 检查条件互斥：例如 `道路类型=城市支路` 与 `特殊要素=维修车间/维修间` 不能同时保留；保留维修场所时，道路类型应改为 `不涉及`，或改写成真实道路场景。

## 修正原则

- 结构、枚举、`不涉及` 一致性优先用 `check_stage_json.py --stage stage3a --fix`。
- 语义问题只修 Stage3A 文件，不修改 Stage3B 或合并 HARA。
- 如果高风险路径覆盖不足，退回 Stage3A 重新生成相关场景。
