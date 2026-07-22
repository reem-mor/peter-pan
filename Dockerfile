# Shared image for all PETER PAN services. SERVICE selects the app at runtime.
# Pinned to match CI's python-version (3.12); pyproject requires >=3.12. Plain
# tag (not digest-pinned) so dependabot's docker ecosystem can bump it.
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ src/
# Runtime assets resolved relative to the package root (see peterpan.knowledge,
# peterpan.llm, peterpan.ml): the corpus, versioned prompts, and model artifacts.
COPY knowledge/ knowledge/
COPY prompts/ prompts/
COPY data/models/ data/models/
# Editable install keeps peterpan importing from /app/src, so the repo-root
# asset paths above resolve; a site-packages install pointed them into the
# interpreter tree and shipped an empty corpus (rag corpus_size=0).
# llm+rag+aws extras: without them PP_LLM/PP_RAG_BACKEND silently fall back
# to the deterministic paths in cloud deploys (torch/ml stays out — image
# size). aws ships boto3 so PP_LLM=bedrock works under the instance profile.
RUN pip install --no-cache-dir -e ".[llm,rag,aws]"

# Non-root, matching the security baseline. WORKDIR /app itself stays
# root-owned; knowledge/ stays writable for the memory feed (POST /memory
# writes incident docs), usage-shared/ stays writable so log_usage()
# (called on every metered LLM call) can append usage.jsonl, and data/
# stays writable because feedback.jsonl / leads.jsonl / prompt_log.jsonl
# default there (COPY data/models/ above created it root-owned, which made
# POST /feedback and POST /leads 500 with PermissionError in-container).
RUN useradd --create-home peterpan \
    && mkdir -p /app/usage-shared /app/data \
    && chown -R peterpan /app/knowledge /app/usage-shared /app/data
USER peterpan

ENV SERVICE=agent PORT=8000
ENV PP_USAGE_LOG_PATH=/app/usage-shared/usage.jsonl
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request;urllib.request.urlopen('http://localhost:8000/healthz',timeout=3)"]
CMD ["sh", "-c", "uvicorn peterpan.services.${SERVICE}:app --host 0.0.0.0 --port ${PORT}"]
