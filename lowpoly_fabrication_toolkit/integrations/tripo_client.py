from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass


@dataclass
class TripoClientConfig:
    endpoint_base: str
    api_key: str = ""
    generate_path: str = "/v2/openapi/task"
    status_path: str = "/v2/openapi/task/{task_id}"


class TripoClient:
    def __init__(self, config: TripoClientConfig):
        self.config = config

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        url = self.config.endpoint_base.rstrip("/") + path
        data = json.dumps(payload).encode("utf-8") if payload else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if self.config.api_key:
            req.add_header("Authorization", f"Bearer {self.config.api_key}")
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def test_connection(self) -> bool:
        return bool(self.config.endpoint_base)

    def send_generation_request(self, prompt: str, **settings) -> dict:
        return self._request("POST", self.config.generate_path, {"prompt": prompt, **settings})

    def check_status(self, task_id: str) -> dict:
        return self._request("GET", self.config.status_path.format(task_id=task_id))

    def download_model(self, url: str, target_path: str) -> str:
        urllib.request.urlretrieve(url, target_path)
        return target_path
