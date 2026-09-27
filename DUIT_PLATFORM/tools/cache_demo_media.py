from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "listings" / "management" / "commands" / "seed_demo.py"
SERVICE_DIR = ROOT / "static" / "demo" / "services"
AVATAR_DIR = ROOT / "static" / "demo" / "avatars"


def read_photo_ids() -> list[int]:
    text = SEED.read_text(encoding="utf-8")
    block = text.split("CATEGORY_PHOTO_IDS = {", 1)[1].split("}\n#", 1)[0]
    ids = [int(x) for x in re.findall(r"\b\d{6,8}\b", block)]
    return sorted(set(ids))


def download(url: str, target: Path) -> None:
    if target.exists() and target.stat().st_size > 25_000:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 DUIT-demo-cache"})
    tmp = target.with_suffix(target.suffix + ".part")
    with urllib.request.urlopen(request, timeout=45) as response, tmp.open("wb") as out:
        content_type = response.headers.get("Content-Type", "")
        if "image" not in content_type:
            raise RuntimeError(f"Expected image, got {content_type}: {url}")
        out.write(response.read())
    if tmp.stat().st_size < 25_000:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Downloaded file is suspiciously small: {url}")
    tmp.replace(target)


def main() -> int:
    photo_ids = read_photo_ids()
    print(f"DUIT offline media: service photos {len(photo_ids)}")
    for index, photo_id in enumerate(photo_ids, 1):
        url = (
            f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg"
            "?auto=compress&cs=tinysrgb&w=1200&h=900&fit=crop"
        )
        target = SERVICE_DIR / f"{photo_id}.jpg"
        print(f"[{index:02d}/{len(photo_ids)}] {target.name}")
        download(url, target)

    # Provider portraits stay on fixed RandomUser URLs. We do not pre-download them
    # because RandomUser may return tiny anti-bot/error payloads to Python clients.
    # The UI has a local SVG fallback for every profile, so a blocked remote avatar
    # cannot break the page or the verification process.
    print("DUIT demo avatars: fixed live URLs + local SVG fallback (no pre-download)")
    print("DUIT offline service-photo cache READY")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: cannot cache demo media: {exc}", file=sys.stderr)
        raise SystemExit(1)
