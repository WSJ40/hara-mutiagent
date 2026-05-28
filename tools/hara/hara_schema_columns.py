from __future__ import annotations

import re
from typing import Any, Mapping

NAN_VALUES = {"", "nan", "none", "null", "n/a", "na", "不适用", "无"}

DERIVE_MF_COLUMNS = [
    "No.",
    "子功能",
    "功能丧失",
    "过大",
    "过早",
    "过小",
    "过晚",
    "非预期激活",
    "卡滞",
    "方向错误",
]

MF_VEHICLE_HAZARDS_COLUMNS = [
    "No.",
    "Milf_ID",
    "故障描述",
    "整车级危害",
    "备注",
]

HARA_COLUMNS = [
    "List_No",
    "MF_ID",
    "故障描述",
    "整车危害",
    "道路类型",
    "道路条件",
    "环境条件",
    "车辆状态",
    "车速(km/h)",
    "特殊要素",
    "附加条件",
    "驾驶员是否在车上",
    "危害事件",
    "E-解释",
    "暴露频率'E'",
    "有风险的人员",
    "可能的后果('S'的理由)",
    "Severity 'S'",
    "C-解释",
    "控制能力 'C'",
    "结果ASIL",
    "安全目标",
    "安全状态",
    "FTTI(ms)",
    "备注",
]

SG_SUM_COLUMNS = [
    "SG_No",
    "安全目标",
    "ASIL Level",
    "安全状态",
    "操作模式",
    "FTTI(ms)",
    "Comments",
]

SHEET_COLUMNS = {
    "DeriveMF": DERIVE_MF_COLUMNS,
    "MF and Vehicle Hazards": MF_VEHICLE_HAZARDS_COLUMNS,
    "HARA": HARA_COLUMNS,
    "SG_Sum": SG_SUM_COLUMNS,
}

FAULT_FIELD_ORDER = [
    "功能丧失",
    "过大",
    "过早",
    "过小",
    "过晚",
    "非预期激活",
    "卡滞",
    "方向错误",
]

SYSTEM_RE = re.compile(r"[^A-Za-z0-9]+")
STAGE1_FAULT_PREFIX_RE = re.compile(r"^\s*MF\d+\s*[:：]?\s*")
STAGE2_MILF_RE = re.compile(r"^(?P<system>[A-Za-z0-9]+)_Milf_(?P<seq>\d+)$", re.IGNORECASE)
STAGE3_MF_RE = re.compile(r"^(?P<system>[A-Za-z0-9]+)_MF_(?P<seq>\d+)$", re.IGNORECASE)
LEGACY_MF_RE = re.compile(r"^MF(?P<seq>\d+)$", re.IGNORECASE)

EXCEL_DISPLAY_HEADERS = {
    "暴露频率'E'": "暴露频率\n'E'",
    "可能的后果('S'的理由)": "可能的后果\n('S'的理由)",
}

ALIASES = {
    "List_No": ["List_No", "List No", "ListNo", "序号"],
    "MF_ID": ["MF_ID", "MF ID", "MFID", "mf_id"],
    "故障描述": ["故障描述", "功能故障", "malfunction", "malfunction_description"],
    "整车危害": ["整车危害", "整车级危害", "vehicle_hazard", "Vehicle Hazard"],
    "整车级危害": ["整车级危害", "整车危害", "vehicle_hazard", "Vehicle Hazard"],
    "道路类型": ["道路类型", "road_type"],
    "道路条件": ["道路条件", "road_condition"],
    "环境条件": ["环境条件", "environment_condition"],
    "车辆状态": ["车辆状态", "vehicle_state"],
    "车速(km/h)": ["车速(km/h)", "车速(km/h)", "车速", "speed", "vehicle_speed"],
    "特殊要素": ["特殊要素", "special_element", "special_elements"],
    "附加条件": ["附加条件", "additional_condition", "additional_conditions"],
    "驾驶员是否在车上": ["驾驶员是否在车上", "driver_present", "driver_in_vehicle"],
    "危害事件": ["危害事件", "hazardous_event"],
    "E-解释": ["E-解释", "E解释", "E_reason", "E rationale"],
    "暴露频率'E'": ["暴露频率'E'", "暴露频率 'E'", "暴露频率\n'E'", "暴露频率‘E’", "暴露频率 E", "暴露频率", "E", "'E'", "Exposure", "exposure"],
    "有风险的人员": ["有风险的人员", "risk_persons", "persons_at_risk"],
    "可能的后果('S'的理由)": ["可能的后果('S'的理由)", "可能的后果\n('S'的理由)", "可能的后果", "('S'的理由)", "S-解释", "S解释", "S_reason", "S rationale"],
    "Severity 'S'": ["Severity 'S'", "Severity\n'S'", "Severity", "S", "'S'", "severity"],
    "C-解释": ["C-解释", "C解释", "C_reason", "C rationale"],
    "控制能力 'C'": ["控制能力 'C'", "控制能力\n'C'", "控制能力", "C", "'C'", "controllability"],
    "结果ASIL": ["结果ASIL", "结果 ASIL", "ASIL", "ASIL等级", "ASIL Level", "asil", "result_asil"],
    "安全目标": ["安全目标", "safety_goal"],
    "安全状态": ["安全状态", "safe_state"],
    "FTTI(ms)": ["FTTI(ms)", "FTTI", "ftti_ms", "FTTI_ms"],
    "备注": ["备注", "comment", "comments", "note", "notes"],
    "Milf_ID": ["Milf_ID", "MF_ID", "MFID", "milf_id"],
    "MF_ID": ["MF_ID", "MF ID", "MFID", "milf_id", "Milf_ID"],
    "ASIL Level": ["ASIL Level", "ASIL", "结果ASIL", "结果 ASIL"],
    "Comments": ["Comments", "备注", "comment", "comments"],
    "过大": ["过大", "过大/过早", "more_than_intended", "too_much"],
    "过早": ["过早", "过大/过早", "too_early"],
    "过小": ["过小", "过小/过晚", "less_than_intended", "too_little"],
    "过晚": ["过晚", "过小/过晚", "too_late"],
}


def is_nan_like(value: Any) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in NAN_VALUES


def normalize_value(value: Any) -> Any:
    return "nan" if is_nan_like(value) else value


def compact_key(key: str) -> str:
    return str(key).replace("\n", "").replace(" ", "").replace("　", "").strip()


def build_key_index(row: Mapping[str, Any]) -> dict[str, str]:
    index: dict[str, str] = {}
    for key in row.keys():
        index[str(key)] = str(key)
        index[compact_key(str(key))] = str(key)
    return index


def get_by_alias(row: Mapping[str, Any], canonical: str) -> Any:
    key_index = build_key_index(row)
    candidates = [canonical] + ALIASES.get(canonical, [])
    for candidate in candidates:
        if candidate in row:
            return row[candidate]
        compact = compact_key(candidate)
        if compact in key_index:
            return row[key_index[compact]]
    return None


def normalize_row(row: Mapping[str, Any], columns: list[str]) -> dict[str, Any]:
    normalized = {}
    for column in columns:
        normalized[column] = normalize_value(get_by_alias(row, column))
    return normalized


def normalize_rows(rows: list[Mapping[str, Any]], columns: list[str]) -> list[dict[str, Any]]:
    return [normalize_row(row, columns) for row in rows if isinstance(row, Mapping)]


def normalize_system_code(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    # Prefer the leading ASCII system token, e.g. EPB from "EPB（电子驻车）".
    leading = re.match(r"[A-Za-z0-9]+", text)
    if leading:
        return leading.group(0).upper()
    cleaned = SYSTEM_RE.sub("", text)
    return cleaned.upper()


def infer_system_code(data: Any | None = None, run_id: str | None = None, default: str = "SYS") -> str:
    if isinstance(data, Mapping):
        meta = data.get("meta")
        if isinstance(meta, Mapping):
            for key in ("system", "system_name", "matched_system"):
                system = normalize_system_code(meta.get(key))
                if system:
                    return system
            meta_run_id = str(meta.get("run_id") or "").strip()
            if meta_run_id and not run_id:
                run_id = meta_run_id
        for rows_key in ("function_mapping", "derive_mf", "mf_vehicle_hazards", "hara"):
            value = data.get(rows_key)
            if isinstance(value, list):
                for row in value:
                    if not isinstance(row, Mapping):
                        continue
                    for key in ("matched_system", "system_hint", "system", "source_system"):
                        system = normalize_system_code(row.get(key))
                        if system:
                            return system

    run_text = str(run_id or "").strip()
    if run_text:
        prefix = re.split(r"[_\-]", run_text, maxsplit=1)[0]
        system = normalize_system_code(prefix)
        if system:
            return system
    return default


def stage1_function_no(system_code: str, function_index: int) -> str:
    return f"{normalize_system_code(system_code)}_fc{function_index:02d}"


def stage1_fault_code(function_index: int, fault_index: int) -> str:
    return f"MF{function_index}{fault_index:02d}"


def strip_stage1_fault_code(value: Any) -> str:
    return STAGE1_FAULT_PREFIX_RE.sub("", str(value or "").strip())


def format_stage1_fault_text(value: Any, function_index: int, fault_index: int) -> str:
    text = strip_stage1_fault_code(value)
    if is_nan_like(text):
        return "nan"
    return f"{stage1_fault_code(function_index, fault_index)} {text}".strip()


def stage2_milf_id(system_code: str, sequence: int) -> str:
    return f"{normalize_system_code(system_code)}_Milf_{sequence:03d}"


def stage3_mf_id(system_code: str, sequence: int) -> str:
    return f"{normalize_system_code(system_code)}_MF_{sequence:02d}"


def mf_sequence_from_id(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    for pattern in (STAGE2_MILF_RE, STAGE3_MF_RE, LEGACY_MF_RE):
        match = pattern.match(text)
        if match:
            return int(match.group("seq"))
    match = re.search(r"(\d+)$", text)
    return int(match.group(1)) if match else None


def stage3_mf_id_from_stage2_milf(value: Any, system_code: str) -> str:
    sequence = mf_sequence_from_id(value)
    if sequence is None:
        return str(value or "").strip()
    return stage3_mf_id(system_code, sequence)


def ids_equivalent(left: Any, right: Any) -> bool:
    left_text = str(left or "").strip()
    right_text = str(right or "").strip()
    if not left_text or not right_text:
        return False
    if compact_key(left_text).lower() == compact_key(right_text).lower():
        return True
    left_sequence = mf_sequence_from_id(left_text)
    right_sequence = mf_sequence_from_id(right_text)
    return left_sequence is not None and left_sequence == right_sequence
