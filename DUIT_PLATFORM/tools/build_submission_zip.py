from __future__ import annotations
import zipfile
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "DUIT_PLATFORM_OFFLINE_SUBMISSION.zip"
SKIP_PARTS = {".venv", "__pycache__", ".git"}
SKIP_NAMES = {"db.sqlite3"}

seed_text = (ROOT / "listings" / "management" / "commands" / "seed_demo.py").read_text(encoding="utf-8")
block = seed_text.split("CATEGORY_PHOTO_IDS = {", 1)[1].split("}\n#", 1)[0]
expected_ids = sorted({int(x) for x in re.findall(r"\b\d{6,8}\b", block)})
if len(expected_ids) != 60:
    raise SystemExit(f"Expected exactly 60 curated service photo IDs, found {len(expected_ids)}.")

service_dir = ROOT / "static" / "demo" / "services"
missing = []
for photo_id in expected_ids:
    path = service_dir / f"{photo_id}.jpg"
    if not path.exists() or path.stat().st_size < 25_000:
        missing.append(path.name)
if missing:
    raise SystemExit(f"Missing/corrupt curated service photos: {missing[:10]}")

avatar_dir = ROOT / "static" / "demo" / "avatars"
expected_avatars = [avatar_dir / f"{gender}_{i}.jpg" for gender in ("women", "men") for i in range(30)]
missing_avatars = [p.name for p in expected_avatars if not p.exists() or p.stat().st_size < 10_000]
if missing_avatars:
    raise SystemExit(f"Missing/corrupt demo avatars: {missing_avatars[:10]}")

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        if path.name in SKIP_NAMES or path.suffix == ".pyc" or path.name.endswith(".part"):
            continue
        z.write(path, Path("DUIT_PLATFORM") / rel)
print(OUT)
