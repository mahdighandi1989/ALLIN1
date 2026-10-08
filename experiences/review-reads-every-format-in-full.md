---
title: "A reviewer must read every attached format COMPLETELY — and an unread or unheard file must block the answer"
tags: ["file-ingest", "transcription", "review-loop", "archives", "legacy-office", "scheduled-agents"]
topic_canonical: "review-reads-every-format-in-full"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-10-08T00:00:00Z"
created_at: "2026-10-08"
updated_at: "2026-10-08"
merged_from: []
---

# A reviewer must read every attached format completely

## 🎯 چالش / Challenge

An owner attaches files to review sheets for an unattended AI reviewer: documents,
spreadsheets, e-mails, archives, screenshots, voice notes, screen recordings. The
extraction layer read some formats in full, listed only the NAMES inside a zip,
answered «no extractor» for legacy Word/Excel and for any unknown extension, and
called audio/video «no text». Worse, the read-debt rule let the reviewer clear an
audio/video file by merely downloading its bytes — so it could answer a sheet
without ever having heard the recording. The owner's rule was the opposite:
«every format must be read, completely — not a summary, not the beginning».

## 💡 راه‌حل / Solution

1. **A plug-in, not a rewrite.** Keep the project's extractor for what it already
   reads; call a shared module only where it used to say «unsupported». The
   module reads: legacy Word (the OLE piece table), legacy Excel (every sheet),
   RTF, OpenDocument, EPUB in spine order, e-mail with every attachment, archives
   RECURSIVELY (each member back through the project's own extractor), SVG as
   text, and anything whose bytes decode as text regardless of extension.
2. **Audio/video become text.** A multimodal model produces a verbatim,
   time-stamped transcript (video: plus every scene and on-screen text), large
   files go through the provider's file API, and an answer that stops before an
   explicit end marker is continued from where it stopped — so output-token
   limits cannot truncate it silently. Hitting the round cap is reported.
3. **`pending` is a debt that opening the bytes does not clear.** It clears only
   when the full transcript exists and has been read. If transcription is
   impossible (no key/model), the status becomes `failed` WITH the reason, so the
   queue never jams and the reviewer never claims to have heard.
4. **Make the visible parts visible.** The reviewer's CLI converts every image
   format its viewer cannot show (HEIC, TIFF pages, BMP, AVIF, SVG…), unpacks
   archives to disk, samples video frames, and reminds it to look at every PDF page.
5. **Code attachments**: read them fully and write your own implementation; never
   paste the attachment into the repo — the coding agent's safety check refuses
   that ("untrusted code integration"), and permission settings do not lift it.

## 🧪 نمونه کد (Anonymized)

```python
def extract(src, filename, mime):
    ...
    if ext == ".doc":
        return extra()                      # was: unsupported
    found = extra()                         # rtf, odt, epub, eml, msg, real text…
    return found if found is not None else done("unsupported", ...)

def extra():
    return formats.extract_extra(data, filename, mime,
                                 base=lambda d, n, m: extract_bytes(d, n, m))  # members recurse
```

## ⚠️ نکات حیاتی / Pitfalls

- A list of names inside an archive is not "reading the archive".
- "Downloaded the bytes" is not "read" for audio/video.
- A transcript capped by output tokens looks complete unless the model must print
  an end marker — require one and continue until it appears.
- Unknown extension ≠ unknown content: sniff for text before giving up.
- Cleanup of a working folder must handle sub-folders (unpacked archives, frames).

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere

1. Find every place the extractor answers "unsupported" and route it to the
   shared readers; keep the project's own readers for everything else.
2. Add `pending` for media, make it a read debt that viewing cannot clear, and a
   re-extract endpoint that finishes it (transcription), resetting the read counter.
3. Teach the reviewer CLI to call that endpoint before writing its brief, and to
   convert/unpack/sample what must be looked at.
4. Version the reviewer's instructions with a per-format "read/see completely" table.

## 🔗 References
- Same change applied across the owner's projects on 2026-10-08 (inspection_formats.py,
  inspection_media.py, scripts/supervisor/inspection_view.py).
