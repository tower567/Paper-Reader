#!/usr/bin/env python3
from __future__ import annotations

import os
import shlex
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests


class MinerUError(RuntimeError):
    pass


DEFAULT_USER_ENV = Path.home() / ".config" / "paper-reader" / "mineru.env"


def load_user_settings(path: Path | None = None) -> dict[str, str]:
    settings_path = path or Path(
        os.environ.get("PAPER_READER_MINERU_ENV", DEFAULT_USER_ENV)
    ).expanduser()
    if not settings_path.is_file():
        return {}
    settings: dict[str, str] = {}
    try:
        lines = settings_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise MinerUError(f"Cannot read MinerU settings: {settings_path}: {exc}") from exc
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parts = shlex.split(line, comments=True, posix=True)
        except ValueError as exc:
            raise MinerUError(f"Invalid MinerU settings line in {settings_path}") from exc
        if parts and parts[0] == "export":
            parts = parts[1:]
        if len(parts) != 1 or "=" not in parts[0]:
            continue
        key, value = parts[0].split("=", 1)
        if key in {"MINERU_API_TOKEN", "MINERU_API_BASE"}:
            settings[key] = value
    return settings


class MinerUClient:
    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
        request_timeout: int = 120,
        session: requests.Session | None = None,
        settings_path: Path | None = None,
    ) -> None:
        user_settings = load_user_settings(settings_path)
        self.token = (
            token
            or os.environ.get("MINERU_API_TOKEN", "")
            or user_settings.get("MINERU_API_TOKEN", "")
        )
        if not self.token:
            raise MinerUError(
                "MINERU_API_TOKEN is not set. Run configure_mineru_token.py "
                "from the Paper-Reader skill scripts directory."
            )
        self.base_url = (
            base_url
            or os.environ.get("MINERU_API_BASE")
            or user_settings.get("MINERU_API_BASE")
            or "https://mineru.net/api/v4"
        ).rstrip("/")
        self.request_timeout = request_timeout
        self.session = session or requests.Session()

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _json_request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        response = self.session.request(
            method,
            f"{self.base_url}{path}",
            headers=self.headers,
            timeout=self.request_timeout,
            **kwargs,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise MinerUError("MinerU returned a non-object JSON response")
        if payload.get("code") not in (0, None):
            raise MinerUError(
                f"MinerU API error {payload.get('code')}: {payload.get('msg') or payload.get('message')}"
            )
        return payload

    def request_upload_url(
        self,
        pdf_path: Path,
        data_id: str,
        model_version: str = "vlm",
        language: str = "en",
        page_ranges: str | None = None,
    ) -> tuple[str, str]:
        options: dict[str, Any] = {
            "files": [{"name": pdf_path.name, "data_id": data_id}],
            "model_version": model_version,
            "enable_formula": True,
            "enable_table": True,
            "language": language,
        }
        if page_ranges:
            options["page_ranges"] = page_ranges
        payload = self._json_request("POST", "/file-urls/batch", json=options)
        data = payload.get("data") or {}
        batch_id = data.get("batch_id")
        urls = data.get("file_urls") or []
        if not batch_id or not urls:
            raise MinerUError("MinerU did not return batch_id and file_urls")
        return str(batch_id), str(urls[0])

    def upload_file(self, upload_url: str, pdf_path: Path) -> None:
        with pdf_path.open("rb") as stream:
            response = self.session.put(
                upload_url,
                data=stream,
                timeout=max(self.request_timeout, 300),
            )
        if not 200 <= response.status_code < 300:
            detail = str(getattr(response, "text", "")).strip()[:500]
            suffix = f": {detail}" if detail else ""
            raise MinerUError(
                f"MinerU signed upload failed with HTTP {response.status_code}{suffix}"
            )

    def get_batch_result(self, batch_id: str) -> dict[str, Any]:
        payload = self._json_request("GET", f"/extract-results/batch/{batch_id}")
        data = payload.get("data") or {}
        results = data.get("extract_result") or data.get("extract_results") or []
        if not results:
            return {"state": "pending", "batch_id": batch_id}
        result = results[0]
        if not isinstance(result, dict):
            raise MinerUError("MinerU returned an invalid batch result")
        return result

    def wait_for_batch(
        self,
        batch_id: str,
        timeout_seconds: int = 1800,
        poll_interval: float = 5.0,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        last_state = ""
        while time.monotonic() < deadline:
            result = self.get_batch_result(batch_id)
            state = str(result.get("state") or result.get("status") or "pending").lower()
            last_state = state
            if state in {"done", "completed", "success", "succeeded"}:
                if not result.get("full_zip_url"):
                    raise MinerUError("MinerU completed without full_zip_url")
                return result
            if state in {"failed", "error", "cancelled", "canceled"}:
                raise MinerUError(
                    f"MinerU parsing failed: {result.get('err_msg') or result.get('message') or state}"
                )
            time.sleep(max(1.0, poll_interval))
        raise MinerUError(f"MinerU parsing timed out; last state: {last_state or 'unknown'}")

    def download_result(self, url: str, target: Path) -> None:
        hostname = (urlparse(url).hostname or "").lower()
        download_session = self.session
        if hostname == "cdn-mineru.openxlab.org.cn":
            download_session = requests.Session()
            download_session.trust_env = False

        last_error = ""
        for attempt in range(3):
            try:
                response = download_session.get(
                    url,
                    timeout=max(self.request_timeout, 300),
                    stream=True,
                )
                if not 200 <= response.status_code < 300:
                    detail = str(getattr(response, "text", "")).strip()[:500]
                    suffix = f": {detail}" if detail else ""
                    raise MinerUError(
                        f"MinerU result download failed with HTTP "
                        f"{response.status_code}{suffix}"
                    )
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("wb") as stream:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            stream.write(chunk)
                return
            except MinerUError:
                raise
            except requests.RequestException as exc:
                last_error = type(exc).__name__
                if attempt < 2:
                    time.sleep(2**attempt)
        raise MinerUError(
            f"MinerU result download failed after 3 attempts: {last_error or 'network error'}"
        )

    def extract_local_pdf(
        self,
        pdf_path: Path,
        output_zip: Path,
        data_id: str,
        model_version: str = "vlm",
        language: str = "en",
        page_ranges: str | None = None,
        timeout_seconds: int = 1800,
        poll_interval: float = 5.0,
    ) -> dict[str, Any]:
        batch_id, upload_url = self.request_upload_url(
            pdf_path,
            data_id=data_id,
            model_version=model_version,
            language=language,
            page_ranges=page_ranges,
        )
        self.upload_file(upload_url, pdf_path)
        result = self.wait_for_batch(
            batch_id,
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
        )
        self.download_result(str(result["full_zip_url"]), output_zip)
        result = dict(result)
        result["batch_id"] = batch_id
        return result
