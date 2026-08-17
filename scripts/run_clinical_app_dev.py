"""Run the clinical FastAPI app from the local Windows dev environment."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_PACKAGES = ROOT / ".venv" / "Lib" / "site-packages"

for path in (
    ROOT,
    SITE_PACKAGES,
    SITE_PACKAGES / "win32",
    SITE_PACKAGES / "win32" / "lib",
):
    sys.path.insert(0, str(path))

if hasattr(os, "add_dll_directory"):
    os.add_dll_directory(str(SITE_PACKAGES / "pywin32_system32"))

import uvicorn  # noqa: E402


if __name__ == "__main__":
    uvicorn.run("clinical_app.app:app", host="127.0.0.1", port=8000, log_level="info")
