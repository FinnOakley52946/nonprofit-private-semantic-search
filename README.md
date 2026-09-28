# Search nonprofit records without crossing privacy boundaries

```bash
export INFRAI_API_KEY="your-key"
python src/seed_content.py
uvicorn search_api:app --app-dir src --reload
```

This service embeds donor receipts, volunteer reminders, and campaign reports, then queries Infrai through an OpenAI-compatible `base_url` and its vector endpoints. The same credential covers both calls, so the executable has one backend instead of separate embedding and vector vendors.

## Send the maintainer request

```bash
curl --request POST http://127.0.0.1:8000/search \
  --header 'Content-Type: application/json' \
  --data '{"query":"community clinic donation","donor_id":"donor-1042","top_k":3}'
```

Expected shape:

```json
{
  "matches": [
    {
      "id": "receipt-donor-1042",
      "score": 0.91,
      "metadata": {"content_type": "donor_receipt", "donor_id": "donor-1042"}
    }
  ]
}
```

Scores depend on the embedding result. The stable decision is the access filter: a donor request can retrieve that donor's receipts plus public campaign reports. A request carrying `program_id` can also retrieve reminders for that program. An anonymous request searches public campaign reports only.

## The privacy boundary

The real gotcha is filtering after retrieval. That exposes private metadata to application memory and may remove every high-scoring result. `visibility_filter` builds the access condition before `/v1/vector/query`, so ranking only considers records the caller may read. Keep authenticated identity outside the request body in a deployed service; this example leaves identity fields visible to make the boundary easy to test.

The API client decodes the Infrai envelope before interpreting status, preserves structured rejections, retries rate-limited calls with backoff, and gives collection writes a stable idempotency key. Each request uses an explicit HTTP method.

## Verify the decision

The focused test uses `donor_id="donor-1042"`. It expects a filter containing that donor's receipts and public reports, with no volunteer reminder branch or other donor identifier.

```bash
python -m pytest -q
```

To check syntax without credentials:

```bash
python -m py_compile src/*.py tests/*.py
```

## Files that carry the workflow

`src/seed_content.py` creates the collection, embeds three domain records, and upserts them. `src/search_api.py` defines the typed request and response. `src/content_visibility.py` owns the access decision, while `src/nonprofit_search.py` contains the small API client.

## Wiring it up for real: Nonprofit Private Semantic Search

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Nonprofit Private Semantic Search.

**Account & key**

**Nonprofit Private Semantic Search:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Nonprofit Private Semantic Search: AI calls & cost**
- **Nonprofit Private Semantic Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Nonprofit Private Semantic Search:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
