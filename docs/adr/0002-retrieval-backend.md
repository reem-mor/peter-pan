# ADR-0002: Canonical retrieval backend

Status: accepted · Date: 2026-07-22

## Context

PETER PAN needs one canonical cloud retrieval backend and one deterministic
local fallback. Candidates:

| Option | Path |
|---|---|
| A | S3 → Bedrock Knowledge Base → AWS-native vectors (S3 Vectors) → RAG |
| B | S3 → Bedrock Knowledge Base → Pinecone → RAG |
| C | App-managed ingestion → standalone Pinecone (+ Voyage) → RAG |
| D | Local `knowledge/` → lexical retrieval |

Audit evidence (2026-07-22):

- Option C is implemented (`pinecone_store.py`, ingest script, CFN default
  `RagBackend=pinecone`), unit-tested with mocks, and Secrets Manager–wired.
- Options A/B have **no** PETER PAN adapter code. The account has unrelated
  Bedrock KBs (e.g. IncidentIQ on `S3_VECTORS`) that must not be reused as
  the product corpus without a dedicated bucket and sync.
- Option D is the fixture-first default and CI retrieval-eval gate.

## Decision

1. **Canonical cloud (live demo now):** Option C — **standalone Pinecone**
   with Voyage embeddings. Label it `pinecone` in APIs/UI/OS — never
   “Bedrock Knowledge Base”.
2. **Canonical local fallback:** Option D — **lexical** over `knowledge/`.
3. **Strategic target:** migrate the demo path to **Option A** (Bedrock KB +
   S3 Vectors) when the adapter, curated S3 corpus, IAM, and retrieval eval
   parity land. Keep Pinecone as optional legacy until then; do not delete
   indexes, secrets, or adapters automatically.
4. **Never** run two active canonical cloud backends for the same demo path.
5. Failures must report `backend=fallback` with a reason — never silently
   present lexical results as Pinecone or Bedrock KB.

## Consequences

- `PP_RAG_BACKEND=lexical|pinecone` remains the env contract for now.
- A future `bedrock-kb` value is additive and requires PR-scoped adapter work.
- UI / PETER PAN OS must display the actual provider from `RagResult.backend`
  and `IncidentStory.providers`.
