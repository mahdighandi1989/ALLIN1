"""Background AI-import job — extraction of a big PDF can run for minutes (split
into page-chunks), far longer than the HTTP gateway will hold a request open. So
``POST /api/imports/analyze`` records a job here and returns its id immediately;
the browser polls ``GET /api/imports/jobs/{id}`` until it is done.

State lives in the database (not process memory) so the poll is answered
correctly even when the API runs several workers (gunicorn ``-w 4``) — the upload
may land on one worker and a later poll on another. The heavy extraction itself
runs as an in-process task on the worker that accepted the upload, writing its
final status/result back to this row.
"""
from datetime import datetime

from sqlalchemy import Column, String, Text, Integer, DateTime, LargeBinary
from sqlalchemy.sql import func

from app.database import Base


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id = Column(String(32), primary_key=True)  # short hex token, also the poll key
    status = Column(String(12), nullable=False, default="running")  # running|done|error
    filename = Column(String(300))
    username = Column(String(80))
    result_json = Column(Text)        # JSON of the extraction result (on success)
    http_status = Column(Integer)     # mirrored error status (on failure)
    detail_json = Column(Text)        # JSON of the error detail (str or dict)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))
    # v106 — restart-survivable jobs: the upload + its parameters ride WITH the
    # job row, so an instance restart mid-extraction (Render OOM / autodeploy)
    # RESUMES the job on boot instead of erroring it. ``file_data`` is cleared
    # the moment the job finishes (done or error) so the table never bloats;
    # ``attempts`` caps resumes (a file that keeps killing the instance must
    # not create a restart loop).
    mime = Column(String(120))
    model_id = Column(Integer)
    instructions = Column(Text)
    attempts = Column(Integer, default=0)
    file_data = Column(LargeBinary)

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<ImportJob {self.id} {self.status} {self.filename!r}>"
