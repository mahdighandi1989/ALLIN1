"""Personal notes: the email button must not be a surprise raw error."""
from httpx import AsyncClient


async def test_list_says_whether_email_can_work(client: AsyncClient, auth_headers, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    r = await client.get("/api/personal/notes", headers=auth_headers)
    assert r.status_code == 200 and r.json()["email_ready"] is False
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.test")
    r = await client.get("/api/personal/notes", headers=auth_headers)
    assert r.json()["email_ready"] is True


async def test_unconfigured_smtp_gives_an_actionable_persian_message(client: AsyncClient, auth_headers, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    r = await client.post("/api/personal/notes/send-email", headers=auth_headers)
    assert r.status_code == 400
    d = r.json()["detail"]
    assert "SMTP_HOST" in d and "ارسال‌نشده" in d


async def test_note_can_be_added_and_deleted(client: AsyncClient, auth_headers):
    n = (await client.post("/api/personal/notes", json={"content": "x"}, headers=auth_headers)).json()
    d = await client.delete(f"/api/personal/notes/{n['id']}", headers=auth_headers)
    assert d.status_code == 200 and d.json()["deleted"] is True
    items = (await client.get("/api/personal/notes", headers=auth_headers)).json()["items"]
    assert all(i["id"] != n["id"] for i in items)
