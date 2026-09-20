#!/usr/bin/env python3
"""Build a self-contained skill archive from the current engine sources."""
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from install_skill import install
out = ROOT / 'dist/dynamic-context-skill.zip'
out.parent.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as temp:
    skill = install(Path(temp))
    shutil.copy2(ROOT/'LICENSE',skill/'LICENSE')
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(skill.rglob('*')):
            if path.is_file(): archive.write(path,path.relative_to(temp))
print(out)
