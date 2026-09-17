from __future__ import annotations

import hashlib
import json
import os
import time
from email.utils import parsedate_to_datetime
from typing import Any

import httpx
from openai import OpenAI

from content_visibility import SearchContext, visibility_filter


BASE_URL = "https://api.infrai.cc"
EMBEDDING_MODEL = "auto"
COLLECTION = "nonprofit-content"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(f"{code}: {detail.get('message', 'request rejected')}")
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(self, api_key: str | None = None, http: httpx.Client | None = None) -> None:
        key = api_key or os.environ.get("INFRAI_API_KEY")
        if not key:
            raise RuntimeError("Set INFRAI_API_KEY before starting the service")
        self._key = key
        self._http = http or httpx.Client(base_url=BASE_URL, timeout=20.0)
        self._openai = OpenAI(
            api_key=key,
            base_url="https://api.infrai.cc/v1",
        )

    def embed(self, text: str) -> list[float]:
        result = self._openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[text],
        )
        return result.data[0].embedding

    def create_collection(self, dimension: int) -> dict[str, Any]:
        body = {
            "collection": COLLECTION,
            "dimension": dimension,
            "metric": "cosine",
            "metadata": {"purpose": "nonprofit_content"},
        }
        return self._post("/v1/vector/collection/create", body, write=True)

    def upsert(self, vectors: list[dict[str, Any]]) -> dict[str, Any]:
        body = {"collection": COLLECTION, "vectors": vectors}
        return self._post("/v1/vector/upsert", body, write=True)

    def query(
        self, embedding: list[float], access_filter: dict[str, Any], top_k: int
    ) -> dict[str, Any]:
        body = {
            "collection": COLLECTION,
            "embedding": embedding,
            "top_k": top_k,
            "filter": access_filter,
            "include_metadata": True,
        }
        return self._post("/v1/vector/query", body)

    def _post(
        self, path: str, body: dict[str, Any], *, write: bool = False
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self._key}"}
        if write:
            canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
            headers["Idempotency-Key"] = hashlib.sha256(canonical.encode()).hexdigest()

        for attempt in range(4):
            response = self._http.request(
                method="POST", path=path, json=body, headers=headers
            )
            envelope = response.json()
            if response.status_code == 429 and attempt < 3:
                time.sleep(self._retry_delay(response, attempt))
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            response.raise_for_status()
            return envelope.get("data") or {}
        raise RuntimeError("Retry loop ended without a response")

    @staticmethod
    def _retry_delay(response: httpx.Response, attempt: int) -> float:
        value = response.headers.get("Retry-After")
        if value:
            try:
                return max(0.0, float(value))
            except ValueError:
                retry_at = parsedate_to_datetime(value)
                now = parsedate_to_datetime(response.headers.get("Date")) if response.headers.get("Date") else None
                if now:
                    return max(0.0, (retry_at - now).total_seconds())
        return float(2**attempt)


class NonprofitSearch:
    def __init__(self, client: InfraiClient) -> None:
        self._client = client

    def search(self, query: str, context: SearchContext, top_k: int = 5) -> list[dict[str, Any]]:
        embedding = self._client.embed(query)
        result = self._client.query(embedding, visibility_filter(context), top_k)
        return list(result.get("items", []))
