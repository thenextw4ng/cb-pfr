from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINTS = [
    ROOT / "app.py",
    ROOT / "pages" / "01_C5G7_Layout_Explorer.py",
    ROOT / "pages" / "02_Physics_Field_Explorer.py",
    ROOT / "pages" / "03_Monte_Carlo_Reliability.py",
    ROOT / "pages" / "04_QUBO_Optimization.py",
    ROOT / "pages" / "05_Provenance_Validation.py",
]


def test_dashboard_entrypoints_render_without_streamlit_exceptions():
    for entrypoint in ENTRYPOINTS:
        app = AppTest.from_file(str(entrypoint), default_timeout=60).run(timeout=60)
        errors = [str(item.value) for item in app.exception]
        assert not errors, (
            f"{entrypoint.relative_to(ROOT)} raised Streamlit exceptions:\n"
            + "\n".join(errors)
        )
