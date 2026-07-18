# Shared image for all PETER PAN services. SERVICE selects the app at runtime.
FROM python:3.14-slim

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
RUN pip install --no-cache-dir -e .

# Non-root, matching the security baseline.
RUN useradd --create-home peterpan
USER peterpan

ENV SERVICE=agent PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn peterpan.services.${SERVICE}:app --host 0.0.0.0 --port ${PORT}"]
