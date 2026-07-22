"""Push the deploy keys from .env into AWS Secrets Manager — values never printed.

Usage:  python scripts/put_deploy_secret.py

Creates/updates the JSON secret `peter-pan/deploy` (ANTHROPIC_API_KEY,
PINECONE_API_KEY, VOYAGE_API_KEY, optional PP_API_TOKEN) that
infra/aws/stack.yaml reads at boot. Prints the secret ARN (needed as the
SecretArn stack parameter) and which key NAMES were included — never a value.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SECRET_NAME = "peter-pan/deploy"
REQUIRED_KEYS = ("ANTHROPIC_API_KEY", "PINECONE_API_KEY", "VOYAGE_API_KEY")
OPTIONAL_KEYS = ("PP_API_TOKEN",)
KEY_NAMES = REQUIRED_KEYS + OPTIONAL_KEYS
ENV_PATH = Path(__file__).parent.parent / ".env"


def read_env_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            if name.strip() in KEY_NAMES and value.strip():
                values[name.strip()] = value.strip()
    return values


def main() -> int:
    if not ENV_PATH.exists():
        print(f".env not found at {ENV_PATH}")
        return 2
    values = read_env_values()
    missing = [k for k in REQUIRED_KEYS if k not in values]
    if missing:
        print(f"missing in .env: {', '.join(missing)} — run set_api_keys.py first")
        return 2
    if "PP_API_TOKEN" not in values:
        print("warning: PP_API_TOKEN unset — mesh will stay open (CIDR-only)")

    # file:// keeps the values out of the process command line (visible in
    # any process listing); the temp file is chmod-narrow and always deleted.
    payload_path = ENV_PATH.parent / ".deploy-secret.tmp.json"
    payload_path.write_text(json.dumps(values), encoding="utf-8")
    payload_ref = f"file://{payload_path.as_posix()}"
    create = subprocess.run(
        [
            "aws",
            "secretsmanager",
            "create-secret",
            "--region",
            "us-east-1",
            "--name",
            SECRET_NAME,
            "--secret-string",
            payload_ref,
            "--query",
            "ARN",
            "--output",
            "text",
        ],
        capture_output=True,
        text=True,
    )
    if create.returncode == 0:
        payload_path.unlink(missing_ok=True)
        arn = create.stdout.strip()
    else:
        if "ResourceExistsException" not in create.stderr:
            payload_path.unlink(missing_ok=True)
            print(f"create-secret failed: {create.stderr.strip()[:200]}")
            return 1
        update = subprocess.run(
            [
                "aws",
                "secretsmanager",
                "put-secret-value",
                "--region",
                "us-east-1",
                "--secret-id",
                SECRET_NAME,
                "--secret-string",
                payload_ref,
                "--query",
                "ARN",
                "--output",
                "text",
            ],
            capture_output=True,
            text=True,
        )
        payload_path.unlink(missing_ok=True)
        if update.returncode != 0:
            print(f"put-secret-value failed: {update.stderr.strip()[:200]}")
            return 1
        arn = update.stdout.strip()

    print(f"secret: {SECRET_NAME}")
    print(f"keys included (names only): {', '.join(sorted(values))}")
    print(f"ARN: {arn}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
