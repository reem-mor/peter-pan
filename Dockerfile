# Shared image for all PETER PAN services. SERVICE selects the app at runtime.
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir .

# Non-root, matching the security baseline.
RUN useradd --create-home peterpan
USER peterpan

ENV SERVICE=agent PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn peterpan.services.${SERVICE}:app --host 0.0.0.0 --port ${PORT}"]
