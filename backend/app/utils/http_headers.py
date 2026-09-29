"""Header values built from user-supplied text.

v152 — extracted from `routers/crm.py`, where it already existed and was already
correct, after the inspection download shipped its own naive version and returned
**500** for every file with a Persian name. HTTP headers are latin-1: a Persian
filename raises `UnicodeEncodeError` while the response is being encoded, which
the framework can only turn into a server error. The owner's own two samples —
«فرمت خلاصه پرونده.pdf» and «آقا تریدینگ…docx» — were undownloadable for exactly
this reason, and looked lost when they were merely unreachable.

It lives here so the next download does not have to rediscover any of it.
"""
from __future__ import annotations

from urllib.parse import quote


def content_disposition(kind: str, filename: str) -> str:
    """RFC 6266 header with a user-supplied name made header-safe.

    Two distinct hazards, both real:

    * **Encoding** — a non-Latin name cannot go in the legacy `filename`
      parameter at all. RFC 5987's `filename*=UTF-8''…` carries it, with an
      ASCII fallback for anything that does not understand it.
    * **Injection** — the name comes from whoever uploaded the file. A double
      quote breaks out of the quoted parameter, and a CR/LF aborts the whole
      response at the ASGI layer. Both are neutralised before use.
    """
    safe = (filename or "document").replace("\r", " ").replace("\n", " ")
    ascii_fallback = safe.encode("ascii", "replace").decode("ascii").replace('"', "'")
    return (
        f'{kind}; filename="{ascii_fallback}"; '
        f"filename*=UTF-8''{quote(safe, safe='')}"
    )
