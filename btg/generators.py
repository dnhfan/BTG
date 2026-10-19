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

BVA_VARIANTS = ("robust", "basic5", "min4")


def _dedupe_points(points: list[tuple[object, str]]) -> list[tuple[object, str]]:
    seen: set = set()
    out: list[tuple[object, str]] = []
    for value, label in points:
        key = repr(value)
        if key in seen:
            continue
        seen.add(key)
        out.append((value, label))
    return out


def _bva_points(param: ParamSpec, variant: str = "robust") -> list[tuple[object, str]]:
    """[(gia_tri, nhan), ...] cac diem bien cua 1 tham so theo bien the:

    - "robust" (mac dinh, dung SRS FR-2.2): 6 diem min-1, min, min+1,
      max-1, max, max+1 — gom ca diem ngoai mien (bat loi lech bien).
    - "basic5": 5 diem kieu co dien min, min+1, nominal, max-1, max
      (chi trong mien hop le).
    - "min4": 4 diem toi thieu min, min+1, max-1, max (2 gia tri moi
      bien, phia hop le).
    """
    if variant not in BVA_VARIANTS:
        raise ValueError(f"BVA variant khong hop le: {variant}")
    points: list[tuple[object, str]] = []
    if param.type in (ParamType.INT, ParamType.FLOAT) \
            and param.min_value is not None and param.max_value is not None:
        is_int = param.type == ParamType.INT
        lo = int(param.min_value) if is_int else float(param.min_value)
        hi = int(param.max_value) if is_int else float(param.max_value)
        step = 1 if is_int else 1.0
        nominal = valid_value(param)
        if not is_int:
            nominal = round(float(nominal), 2)
        catalog = {
            "Min_Minus_1": lo - step, "Min": lo, "Min_Plus_1": lo + step,
            "Nominal": nominal,
            "Max_Minus_1": hi - step, "Max": hi, "Max_Plus_1": hi + step,
        }
        if variant == "robust":
            labels = ["Min_Minus_1", "Min", "Min_Plus_1",
                      "Max_Minus_1", "Max", "Max_Plus_1"]
        elif variant == "basic5":
            labels = ["Min", "Min_Plus_1", "Nominal", "Max_Minus_1", "Max"]
        else:  # min4
            labels = ["Min", "Min_Plus_1", "Max_Minus_1", "Max"]
        raw = [(catalog[label], label) for label in labels]
        if not is_int:
            raw = [(round(v, 2), label) for v, label in raw]
        points = [(v, f"{param.name}_{label}") for v, label in raw]
    elif param.type == ParamType.STRING:
        lo = param.min_length or 0
        hi = param.max_length
        nominal_len = len(valid_value(param))
        if variant == "robust":
            lengths: list[tuple[int, str]] = [
                (lo - 1, "MinLen_Minus_1"), (lo, "MinLen"), (lo + 1, "MinLen_Plus_1")]
            if hi is not None:
                lengths += [(hi - 1, "MaxLen_Minus_1"), (hi, "MaxLen"),
                            (hi + 1, "MaxLen_Plus_1")]
        elif variant == "basic5":
            lengths = [(lo, "MinLen"), (lo + 1, "MinLen_Plus_1"),
                       (nominal_len, "NominalLen")]
            if hi is not None:
                lengths += [(hi - 1, "MaxLen_Minus_1"), (hi, "MaxLen")]
        else:  # min4
            lengths = [(lo, "MinLen"), (lo + 1, "MinLen_Plus_1")]
            if hi is not None:
                lengths += [(hi - 1, "MaxLen_Minus_1"), (hi, "MaxLen")]
        for length, label in lengths:
            if length < 0:
                continue
            points.append((string_of_length(param, length), f"{param.name}_{label}"))
    return _dedupe_points(points)


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


def generate_bva(spec: FunctionSpec, variant: str = "robust") -> list[TestCase]:
    cases: list[TestCase] = []
    nominal = _nominal_inputs(spec)
    for param in spec.params:
        for value, label in _bva_points(param, variant):
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

def generate_pairwise(spec: FunctionSpec, strength: int = 2) -> list[TestCase]:
    """Greedy t-way covering (strength=2 la Pairwise chuan FR-2.3;
    strength=3 la 3-way: phu moi bo 3 (tham so, gia tri))."""
    if len(spec.params) < 2:
        return []
    strength = max(2, min(strength, len(spec.params)))
    cand = {p.name: candidate_values(p) for p in spec.params}
    names = [p.name for p in spec.params]

    # Tat ca bo can phu: ((ten, gia tri) x strength) tren cac nhom tham so
    uncovered: set = set()
    for idxs in itertools.combinations(range(len(names)), strength):
        for combo in itertools.product(*[cand[names[i]] for i in idxs]):
            uncovered.add(tuple((names[i], repr(v)) for i, v in zip(idxs, combo)))

    def tuples_of(inputs: dict) -> set:
        found = set()
        for idxs in itertools.combinations(range(len(names)), strength):
            found.add(tuple((names[i], repr(inputs[names[i]])) for i in idxs))
        return found

    def partial_tuples(trial: dict) -> set:
        keys = list(trial.keys())
        found = set()
        for combo_keys in itertools.combinations(keys, strength):
            found.add(tuple((k, repr(trial[k])) for k in combo_keys))
        return found

    cases: list[TestCase] = []
    guard = 0
    while uncovered and guard < 2000:
        guard += 1
        # Xay dung 1 case tham lam: chon tung tham so sao cho phu nhieu nhat
        chosen: dict = {}
        for name in names:
            best_val, best_gain = cand[name][0], -1
            for val in cand[name]:
                trial = dict(chosen)
                trial[name] = val
                gain = len(partial_tuples(trial) & uncovered)
                if gain > best_gain:
                    best_val, best_gain = val, gain
            chosen[name] = best_val
        covered = tuples_of(chosen)
        if not (covered & uncovered):
            # Khong tien trien duoc nua -> lay to hop tiep theo trong product
            for combo in itertools.product(*[cand[n] for n in names]):
                trial = dict(zip(names, combo))
                if tuples_of(trial) & uncovered:
                    chosen = trial
                    covered = tuples_of(chosen)
                    break
            else:
                break
        uncovered -= covered
        reasoning = ("[Pairwise] Pair_Coverage" if strength == 2
                     else f"[Pairwise] {strength}-Way_Coverage")
        cases.append(
            TestCase(inputs=chosen, technique="Pairwise", reasoning=reasoning)
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
    bva_variant: str = "robust",
    pairwise_strength: int = 2,
) -> list[TestCase]:
    errors = validate_spec(spec)
    if errors:
        raise ValueError("Spec khong hop le:\n- " + "\n- ".join(errors))

    cases: list[TestCase] = []
    if use_ep:
        cases.extend(generate_ep(spec))
    if use_bva:
        cases.extend(generate_bva(spec, variant=bva_variant))
    # SRS FR-2.3: Pairwise chi chay khi nguoi dung bat tuy chon nay
    # (khuyen nghi dung khi ham co > 3 tham so).
    if use_pairwise:
        cases.extend(generate_pairwise(spec, strength=pairwise_strength))
    return deduplicate(cases)
