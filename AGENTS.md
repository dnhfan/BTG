# Repository Guidelines

## Project Structure & Module Organization

BTG generates black-box test cases using Equivalence Partitioning (EP), Boundary Value Analysis (BVA), and Pairwise testing.

- `app.py`: CustomTkinter desktop interface; delegate algorithms to the core.
- `btg/`: UI-independent models, validation, AST parsing, representative values, generators, execution/oracle logic, and exporters.
- `tests/test_btg.py`: core unit tests; `pytest.ini` limits default discovery to `tests/`.
- `examples/`: sample functions and a command-line demo. Generated artifacts go into ignored `output/`.
- `assets/`: application imagery and icons; SVG sources live in `assets/icons/svg/`.
- `tools/build_icons.py`: generates icon PNGs. `docs/HUONG_DAN_SU_DUNG.md` contains detailed usage and team conventions.

## Build, Test, and Development Commands

Use Python 3.10+ and run commands from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                         # Launch desktop UI
pytest -q                             # Run core tests
python examples/demo.py               # Generate CSV, Excel, and pytest artifacts
pytest output/test_generated.py -q    # Verify generated tests explicitly
```

Linux requires the system Tkinter package matching the Python version. There is no separate application build command. To regenerate icons, install optional `cairosvg`, then run `python tools/build_icons.py`.

## Coding Style & Naming Conventions

Use four-space indentation, `snake_case` functions and variables, `PascalCase` classes, and uppercase constants. Follow existing type hints and module docstrings. Keep core logic independent of Tkinter; reuse `FunctionSpec`, `ParamSpec`, and `TestCase`. No formatter or linter is configured.

Keep interface labels and messages in Vietnamese, data-table columns in English, and oracle terminology consistent with the team guide. Edit SVG sources and regenerate PNGs rather than editing PNGs manually.

## Testing Guidelines

Every core change requires unit tests and a passing full `pytest -q` run before pushing. Use descriptive `test_*` functions in `tests/test_btg.py`. Cover relevant boundaries, invalid specifications, pairwise coverage, deduplication, execution results, and exports. No numeric coverage threshold is configured. Manually check affected desktop flows for UI changes.

## Commit & Pull Request Guidelines

History uses `Feature: ...`, `Fix: ...`, and `Remove: ...`. Write specific subjects and explain key changes in the body. PRs should describe behavior, reference relevant issues or SRS requirements, report validation commands/results, and include screenshots for visible UI changes.

## Execution Safety

Reference functions execute through Python `exec` without sandboxing. Only run trusted local code. Keep generated reports and local environments out of commits.
