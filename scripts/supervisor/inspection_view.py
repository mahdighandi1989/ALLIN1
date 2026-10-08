"""Make every attached file something the supervisor can actually SEE.

Shared by `inspection.py` (pull / urgent). The text of a file is read through the
API; this is the other half of «کامل خوانده بشه … و ببینه» — the parts that are
only visible, not readable:

  * images the Read tool cannot show (HEIC/HEIF, TIFF — every page, BMP, AVIF,
    ICO, …) → PNG; SVG → rendered in the headless browser;
  * archives → unpacked to disk, every member, with the same treatment inside;
  * videos → one frame every 5 seconds (≤ 360), to look at alongside the full
    transcript;
  * PDFs → a reminder to look at EVERY page (tables, figures, scans).

Optional tools (scripts/supervisor/requirements.txt): Pillow, pillow-heif,
imageio-ffmpeg, playwright. A missing one is reported, never skipped silently.
"""
from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path
from typing import Callable

VIEWABLE = (".png", ".jpg", ".jpeg", ".gif", ".webp")
CONVERT = (".heic", ".heif", ".tif", ".tiff", ".bmp", ".avif", ".ico", ".svg", ".jfif", ".jp2", ".psd")
VIDEO_EXT = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".3gp", ".m4v", ".wmv", ".mpeg", ".mpg", ".mts")
INSTALL = "`python3 -m pip install -r scripts/supervisor/requirements.txt`"


def viewable(path: Path) -> Path | None:
    """A copy the Read tool can show, or None (with nothing installed)."""
    ext = path.suffix.lower()
    if ext in VIEWABLE:
        return path
    out = path.with_name(path.name + ".png")
    if ext == ".svg":
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                b = pw.chromium.launch()
                pg = b.new_page()
                pg.goto(path.resolve().as_uri())
                pg.screenshot(path=str(out), full_page=True)
                b.close()
            return out
        except Exception:  # noqa: BLE001
            return None
    try:
        from PIL import Image
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except Exception:  # noqa: BLE001
            pass
        with Image.open(path) as im:
            frames = getattr(im, "n_frames", 1)
            im.seek(0)
            im.convert("RGB").save(out)
            for i in range(1, min(frames, 50)):          # multi-page TIFF: every page
                im.seek(i)
                im.convert("RGB").save(path.with_name(f"{path.name}.p{i + 1}.png"))
        return out
    except Exception:  # noqa: BLE001
        return None


def video_frames(path: Path, rel: Callable[[Path], str] = str) -> tuple[str, int]:
    """One frame every 5 s (≤ 360) so the supervisor SEES the video too."""
    try:
        import imageio_ffmpeg
        dest = path.with_name(path.name + ".frames")
        dest.mkdir(exist_ok=True)
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-i", str(path),
                        "-vf", "fps=1/5,scale='min(1280,iw)':-2", "-frames:v", "360",
                        str(dest / "t%04d.jpg")], check=True, timeout=1200)
        return rel(dest), len(list(dest.glob("*.jpg")))
    except Exception as exc:  # noqa: BLE001
        return f"(فریم گرفته نشد: {type(exc).__name__} — {INSTALL})", 0


def unzip(path: Path, rel: Callable[[Path], str] = str) -> tuple[str, list[str]]:
    """Every member on disk (no path escapes); images made viewable, videos framed."""
    dest = path.with_name(path.name + ".d")
    notes: list[str] = []
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            target = (dest / info.filename).resolve()
            if info.is_dir() or not str(target).startswith(str(dest.resolve())):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(info))
            ext = target.suffix.lower()
            if ext in VIDEO_EXT:
                d, n = video_frames(target, rel)
                notes.append(f"{info.filename}: {n} فریم در `{d}`")
            elif ext == ".zip":
                _d, inner = unzip(target, rel)
                notes += [f"{info.filename}/ {x}" for x in inner]
            elif ext in CONVERT:
                v = viewable(target)
                notes.append(f"{info.filename}: برای دیدن ← `{rel(v)}`" if v else
                             f"{info.filename}: تبدیل نشد — {INSTALL}")
    return rel(dest), notes


def look_notes(path: Path, filename: str, status: str, rel: Callable[[Path], str] = str) -> tuple[list[str], Path | None]:
    """What else there is to SEE in this file — `(notes, better_path_to_open)`."""
    low = (filename or path.name).lower()
    if low.endswith(".zip"):
        d, inner = unzip(path, rel)
        return [f"همهٔ محتوای آرشیو باز شد در `{d}`" + (" — " + "؛ ".join(inner) if inner else "")], None
    if low.endswith(VIDEO_EXT):
        d, n = video_frames(path, rel)
        return [f"{n} فریم (هر ۵ ثانیه) در `{d}` — **نگاهشان کن**؛ متنِ کامل (گفتار + شرحِ تصویر) جداست"], None
    if low.endswith(".pdf"):
        return ["PDF را با ابزارِ Read و پارامترِ `pages` ببین — **همهٔ صفحه‌ها** (۲۰ تا ۲۰ تا)؛ "
                "جدول، شکل و صفحهٔ اسکن فقط آن‌جا دیده می‌شوند"], None
    if status == "image" or low.endswith(CONVERT):
        v = viewable(path)
        if v is None:
            return [f"تبدیل به قالبِ قابلِ دیدن نشد — {INSTALL}"], None
        if v != path:
            return [f"برای دیدن: `{rel(v)}`"], v
    return [], None


def needs_bytes(filename: str) -> bool:
    """Files whose text is complete but which must ALSO be looked at."""
    return (filename or "").lower().endswith((".zip", ".pdf") + VIDEO_EXT)
