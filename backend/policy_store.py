import yaml
from pathlib import Path
from typing import Dict


def load_policies(path: str) -> Dict:
    """Load policies YAML and return as dict. Raise on error."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"policies file not found: {path}")
    try:
        with p.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
            return raw
    except Exception as e:
        raise RuntimeError(f"failed to load policies: {e}")
