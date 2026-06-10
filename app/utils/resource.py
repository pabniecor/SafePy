import sys
from pathlib import Path

def resource_path(relative_path: str) -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    base_path = Path(meipass) if meipass else Path(__file__).resolve().parents[3]
    return base_path / relative_path