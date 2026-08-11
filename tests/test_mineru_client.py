from __future__ import annotations

import io
import os
import sys
import zipfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".agents" / "skills" / "manage-literature-repository" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from configure_mineru_token import install_token
from mineru_client import MinerUClient, load_user_settings


class FakeResponse:
    def __init__(
        self,
        payload=None,
        content: bytes = b"",
        status_code: int = 200,
        text: str = "",
    ) -> None:
        self.payload = payload
        self.content = content
        self.status_code = status_code
        self.text = text

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload

    def iter_content(self, chunk_size: int):
        yield self.content


class FakeSession:
    def __init__(self, zip_bytes: bytes) -> None:
        self.zip_bytes = zip_bytes
        self.polls = 0
        self.uploaded = False
        self.upload_headers = None

    def request(self, method, url, **kwargs):
        if method == "POST":
            return FakeResponse(
                {"code": 0, "data": {"batch_id": "batch-1", "file_urls": ["https://upload"]}}
            )
        self.polls += 1
        state = "running" if self.polls == 1 else "done"
        result = {"state": state}
        if state == "done":
            result["full_zip_url"] = "https://download"
        return FakeResponse({"code": 0, "data": {"extract_result": [result]}})

    def put(self, url, **kwargs):
        self.uploaded = True
        self.upload_headers = kwargs.get("headers")
        return FakeResponse()

    def get(self, url, **kwargs):
        return FakeResponse(content=self.zip_bytes)


def test_mineru_signed_upload_poll_and_download(tmp_path: Path) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("full.md", "# Parsed\n\n## Method\n\nContent")
    session = FakeSession(buffer.getvalue())
    client = MinerUClient(token="test-token", session=session)
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n" + b"0" * 700)
    output = tmp_path / "result.zip"

    result = client.extract_local_pdf(
        pdf,
        output,
        data_id="paper-1",
        poll_interval=0,
        timeout_seconds=10,
    )

    assert session.uploaded
    assert session.upload_headers is None
    assert result["batch_id"] == "batch-1"
    assert output.is_file()


def test_user_level_token_configuration_and_loading(tmp_path: Path) -> None:
    config_path, bashrc_path = install_token("test-token-value", tmp_path)

    if os.name != "nt":
        assert config_path.stat().st_mode & 0o777 == 0o600
    assert "Paper Reader MinerU" in bashrc_path.read_text(encoding="utf-8")
    settings = load_user_settings(config_path)
    assert settings["MINERU_API_TOKEN"] == "test-token-value"

    client = MinerUClient(
        token=None,
        settings_path=config_path,
        session=FakeSession(b""),
    )
    assert client.token == "test-token-value"

    install_token("replacement-token", tmp_path)
    assert bashrc_path.read_text(encoding="utf-8").count("Paper Reader MinerU >>>") == 1
    if os.name != "nt":
        assert os.stat(config_path).st_mode & 0o777 == 0o600
