#!/usr/bin/env python3
"""Use the bundled engine when installed, or the source tree during development."""
from pathlib import Path
import sys
if not (Path(__file__).parent / "jev_context").exists():
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from jev_context.cli import main
raise SystemExit(main())
