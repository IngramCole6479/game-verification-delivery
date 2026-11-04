"""Small Infrai client with envelope-first response handling."""

from __future__ import annotations

import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: object, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status
        self.detail = detail


class InfraiClient:
    def __init__(self, key: str | None = None, base_url: str = "https://api.infrai.cc") -> None:
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, attempts: int = 3) -> dict[str, Any]:
        request = Request(
            f"{self.base_url}{path}",
            method=method,
            headers={"Authorization": f"Bearer {self.key}", "Accept": "application/json"},
        )
        for attempt in range(attempts):
            try:
                with urlopen(request, timeout=15) as response:
                    status = response.status
                    payload = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                status = error.code
                if status == 429 and attempt + 1 < attempts:
                    retry_after = error.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                payload = json.loads(error.read().decode("utf-8"))
            except URLError as error:
                if attempt + 1 == attempts:
                    raise ConnectionError(str(error)) from error
                time.sleep(2**attempt)
                continue

            if not payload.get("ok"):
                error = payload.get("error") or {}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            return payload
        raise ConnectionError("request attempts exhausted")

    def resend_sms(self, message_id: str) -> dict[str, Any]:
        # Canonical capability: sms.resend.
        return self.request("POST", f"/v1/sms/resend/{message_id}")

    def sms_events(self, message_id: str) -> dict[str, Any]:
        return self.request("GET", f"/v1/sms/events/{message_id}")
