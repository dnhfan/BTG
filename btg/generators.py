"""Test Generation Engine — SRS FE-02.

- Equivalence Partitioning (FR-2.1): 1 case hop le + cac case khong hop le
  theo Single Fault Assumption (moi case chi co dung 1 tham so sai).
- Boundary Value Analysis (FR-2.2): min-1, min, min+1, max-1, max, max+1
  (voi string: ap dung len do dai chuoi).
- Pairwise (FR-2.3): phu moi cap (tham so, gia tri) voi so case gon nhat
  bang thuat toan tham lam (greedy covering).
- Tag + khử trùng (FR-2.4): moi case co reasoning, loai case trung hoan toan.
"""
from __future__ import annotations

import itertools

from .models import FunctionSpec, ParamSpec, ParamType, TestCase
from .validation import validate_spec
from .values import candidate_values, invalid_values, string_of_length, valid_value


def _nominal_inputs(spec: FunctionSpec) -> dict:
    return {p.name: valid_value(p) for p in spec.params}


# --------------------------------------------------------------------- EP ---

def generate_ep(spec: FunctionSpec) -> list[TestCase]:
    cases: list[TestCase] = []
    nominal = _nominal_inputs(spec)

    cases.append(
        TestCase(
            inputs=dict(nominal),
            technique="EP",
            reasoning="[EP] Valid_Partition",
        )
    )
    # Single Fault Assumption: lan luot cho tung tham so mang gia tri sai
    for param in spec.params:
        for bad_value, label in invalid_values(param):
            inputs = dict(nominal)
            inputs[param.name] = bad_value
            cases.append(
                TestCase(
                    inputs=inputs,
                    technique="EP",
                    reasoning=f"[EP] Invalid_Partition_{label}",
                    expected_exception="Exception",
                )
            )
    return cases


# -------------------------------------------------------------------- BVA ---

def _bva_points(param: ParamSpec) -> list[tuple[object, str]]:
    """[(gia_tri, nhan), ...] cac diem bien cua 1 tham so."""
    points: list[tuple[object, str]] = []
    if param.type == ParamType.INT and param.min_value is not None and param.max_value is not None:
        lo, hi = int(param.min_value), int(param.max_value)
        raw = [
            (lo - 1, "Min_Minus_1", "Exception"),
            (lo, "Min", None),
            (lo + 1, "Min_Plus_1", None),
            (hi - 1, "Max_Minus_1", None),
            (hi, "Max", None),
            (hi + 1, "Max_Plus_1", "Exception"),
        ]
        points = [(v, f"{param.name}_{label}") for v, label, _ in raw]
    elif param.type == ParamType.FLOAT and param.min_value is not None and param.max_value is not None:
        lo, hi = float(param.min_value), float(param.max_value)
        step = 1.0
        raw = [(lo - step, "Min_Minus_1"), (lo, "Min"), (lo + step, "Min_Plus_1"),
               (hi - step, "Max_Minus_1"), (hi, "Max"), (hi + step, "Max_Plus_1")]
        points = [(round(v, 2), f"{param.name}_{label}") for v, label in raw]
    elif param.type == ParamType.STRING:
        lo = param.min_length or 0
        hi = param.max_length
        lengths: list[tuple[int, str]] = []
        lengths += [(lo - 1, "MinLen_Minus_1"), (lo, "MinLen"), (lo + 1, "MinLen_Plus_1")]
        if hi is not None:
            lengths += [(hi - 1, "MaxLen_Minus_1"), (hi, "MaxLen"), (hi + 1, "MaxLen_Plus_1")]
        for length, label in lengths:
            if length < 0:
                continue
            points.append((string_of_length(param, length), f"{param.name}_{label}"))
    return points


def _is_out_of_bounds(param: ParamSpec, value: object) -> bool:
    if param.type in (ParamType.INT, ParamType.FLOAT) and isinstance(value, (int, float)):
        if param.min_value is not None and value < param.min_value:
            return True
        if param.max_value is not None and value > param.max_value:
            return True
    if param.type == ParamType.STRING and isinstance(value, str):
        if param.min_length is not None and len(value) < param.min_length:
            return True
        if param.max_length is not None and len(value) > param.max_length:
            return True
    return False


def generate_bva(spec: FunctionSpec) -> list[TestCase]:
    cases: list[TestCase] = []
    nominal = _nominal_inputs(spec)
    for param in spec.params:
        for value, label in _bva_points(param):
            inputs = dict(nominal)
            inputs[param.name] = value
            out = _is_out_of_bounds(param, value)
            cases.append(
                TestCase(
                    inputs=inputs,
                    technique="BVA",
                    reasoning=f"[BVA] {label}",
                    expected_exception="Exception" if out else None,
                )
            )
    return cases


# --------------------------------------------------------------- Pairwise ---

def generate_pairwise(spec: FunctionSpec) -> list[TestCase]:
    """Greedy all-pairs: moi case moi phu nhieu cap chua duoc phu nhat."""
    if len(spec.params) < 2:
        return []
    cand = {p.name: candidate_values(p) for p in spec.params}
    names = [p.name for p in spec.params]

    # Tat ca cap can phu: ((param_i, val_i), (param_j, val_j)), i < j
    uncovered: set = set()
    for i, j in itertools.combinations(range(len(names)), 2):
        for vi in cand[names[i]]:
            for vj in cand[names[j]]:
                uncovered.add(((names[i], repr(vi)), (names[j], repr(vj))))
    def pairs_of(inputs: dict) -> set:
        pairs = set()
        for i, j in itertools.combinations(range(len(names)), 2):
            pairs.add(((names[i], repr(inputs[names[i]])), (names[j], repr(inputs[names[j]]))))
        return pairs

    cases: list[TestCase] = []
    guard = 0
    while uncovered and guard < 500:
        guard += 1
        # Xay dung 1 case tham lam: chon tung tham so sao cho phu nhieu nhat
        chosen: dict = {}
        for name in names:
            best_val, best_gain = cand[name][0], -1
            for val in cand[name]:
                trial = dict(chosen)
                trial[name] = val
                # Dem so cap chua phu ma (cac tham so da chon + gia tri nay) tao ra
                partial_pairs = set()
                keys = list(trial.keys())
                for i, j in itertools.combinations(range(len(keys)), 2):
                    partial_pairs.add(((keys[i], repr(trial[keys[i]])), (keys[j], repr(trial[keys[j]]))))
                gain = len(partial_pairs & uncovered)
                if gain > best_gain:
                    best_val, best_gain = val, gain
            chosen[name] = best_val
        covered = pairs_of(chosen)
        if not (covered & uncovered):
            # Khong tien trien duoc nua -> lay to hop tiep theo trong product
            for combo in itertools.product(*[cand[n] for n in names]):
                trial = dict(zip(names, combo))
                if pairs_of(trial) & uncovered:
                    chosen = trial
                    covered = pairs_of(chosen)
                    break
            else:
                break
        uncovered -= covered
        cases.append(
            TestCase(inputs=chosen, technique="Pairwise",
                     reasoning="[Pairwise] Pair_Coverage")
        )
    return cases


# ----------------------------------------------------------------- Engine ---

def deduplicate(cases: list[TestCase]) -> list[TestCase]:
    seen: set = set()
    unique: list[TestCase] = []
    for case in cases:
        key = case.key()
        if key in seen:
            continue
        seen.add(key)
        unique.append(case)
    for idx, case in enumerate(unique, start=1):
        case.test_id = f"TC_{idx:03d}"
    return unique


def generate_test_cases(
    spec: FunctionSpec,
    use_ep: bool = True,
    use_bva: bool = True,
    use_pairwise: bool = False,
) -> list[TestCase]:
    errors = validate_spec(spec)
    if errors:
        raise ValueError("Spec khong hop le:\n- " + "\n- ".join(errors))

    cases: list[TestCase] = []
    if use_ep:
        cases.extend(generate_ep(spec))
    if use_bva:
        cases.extend(generate_bva(spec))
    # SRS FR-2.3: Pairwise chi chay khi nguoi dung bat tuy chon nay
    # (khuyen nghi dung khi ham co > 3 tham so).
    if use_pairwise:
        cases.extend(generate_pairwise(spec))
    return deduplicate(cases)
