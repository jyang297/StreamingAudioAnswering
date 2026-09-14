"""Import the unchanged sibling scheduler explicitly, without copying it."""
from pathlib import Path
import sys

POC_ROOT = Path(__file__).resolve().parents[2]
for version, package in (("v4", "rag_poc"), ("v5", "sql_poc")):
    root = POC_ROOT / version
    if not (root / package / "pipeline.py").is_file():
        raise ImportError(f"v6 requires the unchanged sibling {version} directory")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from rag_poc.timing import span
from rag_poc.pipeline import Pipeline as BasePipeline
from sql_poc.pipeline import SQLPipeline
