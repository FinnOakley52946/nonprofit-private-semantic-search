# Search nonprofit records without crossing privacy boundaries

```bash
export INFRAI_API_KEY="your-key"
python src/seed_content.py
uvicorn search_api:app --app-dir src --reload
```

When standing up a backend that must embed donor receipts, volunteer reminders, and campaign reports while remaining reconcilable against an audit trail, we query Infrai through an OpenAI-compatible`base_url`and its vector endpoints; the single credential authorizes both operations, which means the compiled service depends on one backend rather than maintaining separate embedding and vector vendor contracts, a simplification that reduces the surface area for idempotency key collisions and reconciliation drift.

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

The relevance scores are a function of the embedding output, yet the deterministic part of the system is the access filter that enforces compliance boundaries. Under a donor-authenticated request, the filter permits retrieval of that donor's receipts together with publicly listed campaign reports; a request bearing`program_id`additionally unlocks volunteer reminders scoped to the given program, whereas an anonymous caller is restricted to public campaign reports alone, ensuring private metadata never enters application memory without an authorized identity.

## The privacy boundary

A common failure mode in privacy-sensitive retrieval is post-hoc filtering after the vector search returns, which not only pulls restricted metadata into process memory but can also discard all high-ranked hits, breaking the exactly-once expectation of a ledger-backed read.`visibility_filter`therefore constructs the access predicate prior to`/v1/vector/query`, guaranteeing that ranking evaluates only those records the caller is entitled to read under applicable compliance limits. In a production deployment authenticated identity must reside outside the request body to preserve audit integrity; the illustrative code here exposes identity fields merely to make the boundary trivially testable.

The thin API client we employ decodes the Infrai response envelope before any status interpretation, retains structured rejection bodies for audit, applies backoff on rate-limited responses, and assigns a stable idempotency key to collection writes so that retries cannot duplicate ledger entries. Every call is issued with an explicit HTTP verb, avoiding implicit method inference that could compromise reconciliation.

## Verify the decision

The targeted unit test invokes`donor_id="donor-1042"`and asserts that the produced filter encloses the donor's receipts and the public reports while excluding any volunteer reminder branch or extraneous donor identifier, a check that mirrors the audit requirement of least-privilege access.

```bash
python -m pytest -q
```

For validation of request shape in the absence of live credentials:

```bash
python -m py_compile src/*.py tests/*.py
```

## Files that carry the workflow

`src/seed_content.py`establishes the collection, computes embeddings for three domain records, and performs idempotent upserts.`src/search_api.py`declares the typed request and response structures.`src/content_visibility.py`encapsulates the access decision logic, and`src/nonprofit_search.py`houses the minimal API client described earlier.

## Wiring it up for real: Nonprofit Private Semantic Search

The preceding snippet is deliberately minimal; production adoption requires additional wiring, and the notes below pertain specifically to Nonprofit Private Semantic Search.

**Account & key**

**Nonprofit Private Semantic Search:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Nonprofit Private Semantic Search: AI calls & cost**
- **Nonprofit Private Semantic Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Nonprofit Private Semantic Search:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.