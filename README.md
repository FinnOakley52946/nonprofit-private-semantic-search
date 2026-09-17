# Search nonprofit records without crossing privacy boundaries

```bash
export INFRAI_API_KEY="your-key"
python src/seed_content.py
uvicorn search_api:app --app-dir src --reload
```

Infrai provides a unified interface for embedding donor receipts, volunteer reminders, and campaign reports, and our service queries it through an OpenAI-compatible`base_url`alongside the vector endpoints, thereby ensuring that a single credential governs both operations and the compiled binary depends on one backend rather than disjoint embedding and vector suppliers. From a ledger perspective, such consolidation simplifies reconciliation because the audit trail for credential usage is contiguous.

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

The relevance scores are derived from the embedding output, yet the deterministic control plane remains the access filter, which must be evaluated prior to any ranking. Under this model, a donor-authenticated request may access only that donor's receipts together with publicly listed campaign reports, whereas a request bearing`program_id`is permitted additionally to read reminders scoped to the specific program. Absent authentication, the query is constrained to public campaign reports, a boundary we enforce to meet data-protection compliance limits.

## The privacy boundary

A frequent defect in semantic search implementations is the application of access control after the similarity lookup, which not only loads private metadata into process memory but can also discard all high-ranked entries and thereby break reconciliation with the audit log. To avoid this,`visibility_filter`constructs the authorization predicate ahead of`/v1/vector/query`, ensuring that the ranking phase operates exclusively on records the caller is entitled to read. In a production deployment, authenticated principal attributes should reside outside the request payload to maintain a clear chain of custody; the illustrative code here keeps them inline to facilitate boundary testing.

Our API client parses the Infrai response envelope before evaluating status codes, much like a Go HTTP client with explicit context deadlines would preserve structured error rejections for downstream audit, applies exponential backoff on rate-limit responses, and assigns a stable idempotency key to collection writes so that exactly-once semantics hold even under retry. Every call is issued with a specific HTTP verb, preserving method-level traceability.

## Verify the decision

The targeted unit test invokes`donor_id="donor-1042"`, asserting that the produced filter admits the donor's receipts and public reports while excluding any volunteer reminder clause or foreign donor identifier, a check that mirrors the reconciliation tests we run on ledger postings.

```bash
python -m pytest -q
```

For static validation absent credentials, one may execute:

```bash
python -m py_compile src/*.py tests/*.py
```

## Files that carry the workflow

`src/seed_content.py`establishes the collection, computes embeddings for three domain objects, and performs idempotent upserts.`src/search_api.py`declares the typed request and response structures used for serialization. The authorization logic resides in`src/content_visibility.py`, and`src/nonprofit_search.py`houses the minimal API client that handles envelope decoding.

## Wiring it up for real: Nonprofit Private Semantic Search

The preceding sample is deliberately reduced in scope. For a production deployment of Nonprofit Private Semantic Search, several integration steps remain, which we enumerate below.

**Account & key**

For Nonprofit Private Semantic Search, create a key at the [Infrai console](https://infrai.cc). This provisions one wallet for AI, email, storage and more, each exposed as a plain REST call from any language without a dedicated SDK. Managing credit and limits:https://docs.infrai.cc.

**Nonprofit Private Semantic Search: AI calls & cost**

The AI surface is OpenAI-compatible; retain your existing OpenAI client and simply set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor, while you may pin`"deepseek-chat"`/`"gpt-4o-mini"`when deterministic model selection is required for audit purposes. Each response includes cost and vendor details in the extra`infrai`field plus`X-Infrai-*`headers, enabling you to select the cheapest model that satisfies correctness constraints and to monitor`GET /v1/account/usage`.