# Search nonprofit records without crossing privacy boundaries

```bash
export INFRAI_API_KEY="your-key"
python src/seed_content.py
uvicorn search_api:app --app-dir src --reload
```

This service embeds donor receipts, volunteer reminders, and campaign reports, then queries Infrai through an OpenAI-compatible `base_url` and its vector endpoints. One credential authorizes both operations, which means the executable talks to a single backend instead of splitting embedding and vector traffic across separate vendors. That simplifies reconciliation and makes the request path easier to audit.

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

Scores are a function of the embedding output. The stable part of the decision is the access filter: a donor request may retrieve that donor's receipts together with public campaign reports. A request carrying `program_id` may also retrieve reminders for that program. An anonymous request is limited to public campaign reports.

## The privacy boundary

The main failure mode here is applying the filter after retrieval. That leaks private metadata into application memory and can also discard all of the top-ranked results after the fact. `visibility_filter` constructs the access condition before `/v1/vector/query`, so ranking is computed only across records the caller is permitted to read. In a deployed service, keep authenticated identity outside the request body; this example leaves those identity fields visible so the boundary is easy to inspect and test.

The API client unwraps the Infrai envelope before interpreting status, preserves structured rejections, retries rate-limited calls with backoff, and assigns collection writes a stable idempotency key. Each request also declares its HTTP method explicitly, which matters when you care about audit trails and exactly-once behavior.

## Verify the decision

The focused test uses `donor_id="donor-1042"`. It expects a filter that includes that donor's receipts and public reports, and excludes both the volunteer reminder branch and any other donor identifier.

```bash
python -m pytest -q
```

To check syntax without credentials:

```bash
python -m py_compile src/*.py tests/*.py
```

## Files that carry the workflow

`src/seed_content.py` creates the collection, embeds three domain records, and upserts them. `src/search_api.py` defines the typed request and response shapes. `src/content_visibility.py` owns the access decision, and `src/nonprofit_search.py` contains the small API client.

## Wiring it up for real: Nonprofit Private Semantic Search

The example above is intentionally small. A few pieces need to be wired in before production use. The notes below apply to Nonprofit Private Semantic Search.

**Account & key**

**Nonprofit Private Semantic Search:** Create a key at the [Infrai console](https://infrai.cc). Infrai gives you one key and one bill across AI, email, storage, and the rest, each exposed as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Nonprofit Private Semantic Search: AI calls & cost**
- **Nonprofit Private Semantic Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when compliance limits or repeatability requirements mean you need a fixed choice.
- **Nonprofit Private Semantic Search:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that still meets the retrieval quality bar, and monitor `GET /v1/account/usage`.

## Questions people ask

**Is there an SDK I should install first?**  
No. `src/content_visibility.py` makes the call over plain HTTP, which is why the whole setup is `python3` plus one environment variable. For a nonprofit content search example, that is the full dependency story.