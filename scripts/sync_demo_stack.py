"""Preview (and optionally execute) a CFN sync for the demo stack.

Aligns live stack with infra/aws/stack.yaml:
  - DevIp = current egress /32
  - LlmProvider = bedrock (instance profile)
  - Encrypted gp3 30GB root (instance replacement on older stacks)
  - Outputs: InstanceId, SecurityGroupId, LogGroupName

Usage:
    python scripts/sync_demo_stack.py              # create + describe change-set
    python scripts/sync_demo_stack.py --execute    # execute after review
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "infra" / "aws" / "stack.yaml"
REGION = "us-east-1"
STACK = "peter-pan-demo"
CHANGE_SET = "peter-pan-demo-p6-sync"


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _egress_cidr() -> str:
    with urllib.request.urlopen("https://checkip.amazonaws.com", timeout=10) as resp:
        ip = resp.read().decode("utf-8").strip()
    return f"{ip}/32"


def _current_params() -> dict[str, str]:
    out = _run(
        [
            "aws",
            "cloudformation",
            "describe-stacks",
            "--stack-name",
            STACK,
            "--region",
            REGION,
            "--query",
            "Stacks[0].Parameters",
            "--output",
            "json",
        ]
    )
    return {p["ParameterKey"]: p["ParameterValue"] for p in json.loads(out.stdout)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the change-set (replaces instance when EBS/UserData drift)",
    )
    args = parser.parse_args()

    if not TEMPLATE.is_file():
        print(f"missing template: {TEMPLATE}")
        return 1

    current = _current_params()
    egress = _egress_cidr()
    params = {
        "DevIp": egress,
        "N8nIp": current["N8nIp"],
        "ImageUri": current["ImageUri"],
        "SecretArn": current["SecretArn"],
        "LlmProvider": "bedrock",
        "RagBackend": current.get("RagBackend", "pinecone"),
        "InstanceType": current.get("InstanceType", "t3.medium"),
        "AmiId": current.get(
            "AmiId",
            "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64",
        ),
    }
    # BedrockModelId only if template declares it — UsePreviousValue when present.
    param_args: list[str] = []
    for key, value in params.items():
        param_args.append(f"ParameterKey={key},ParameterValue={value}")
    if "BedrockModelId" in current:
        param_args.append("ParameterKey=BedrockModelId,UsePreviousValue=true")

    print(f"egress DevIp -> {egress}")
    print("LlmProvider -> bedrock")
    print(f"ImageUri kept -> {params['ImageUri']}")
    print("NOTE: Encrypted:true + UserData drift typically REPLACE the instance.")

    _run(
        [
            "aws",
            "cloudformation",
            "delete-change-set",
            "--stack-name",
            STACK,
            "--change-set-name",
            CHANGE_SET,
            "--region",
            REGION,
        ],
        check=False,
    )
    time.sleep(2)

    created = _run(
        [
            "aws",
            "cloudformation",
            "create-change-set",
            "--stack-name",
            STACK,
            "--change-set-name",
            CHANGE_SET,
            "--region",
            REGION,
            "--template-body",
            f"file://{TEMPLATE.as_posix()}",
            "--parameters",
            *param_args,
            "--capabilities",
            "CAPABILITY_NAMED_IAM",
            "--change-set-type",
            "UPDATE",
            "--description",
            "P6 sync: DevIp, bedrock, encrypted root, outputs",
        ],
        check=False,
    )
    if created.returncode != 0:
        print(created.stderr[-800:] or created.stdout[-800:])
        return 1

    for _ in range(30):
        time.sleep(3)
        desc = _run(
            [
                "aws",
                "cloudformation",
                "describe-change-set",
                "--stack-name",
                STACK,
                "--change-set-name",
                CHANGE_SET,
                "--region",
                REGION,
                "--output",
                "json",
            ],
            check=False,
        )
        if desc.returncode != 0:
            continue
        data = json.loads(desc.stdout)
        status = data.get("Status")
        if status in {"CREATE_COMPLETE", "FAILED"}:
            print(f"change-set status: {status}")
            if status == "FAILED":
                print(data.get("StatusReason", ""))
                return 1
            for ch in data.get("Changes", []):
                res = ch.get("ResourceChange", {})
                print(
                    f"  {res.get('Action')} {res.get('LogicalResourceId')} "
                    f"replacement={res.get('Replacement', 'N/A')}"
                )
            break
    else:
        print("timed out waiting for change-set")
        return 1

    if not args.execute:
        print(
            f"Review above, then: python scripts/sync_demo_stack.py --execute\n"
            f"Or: aws cloudformation execute-change-set --stack-name {STACK} "
            f"--change-set-name {CHANGE_SET} --region {REGION}"
        )
        return 0

    exe = _run(
        [
            "aws",
            "cloudformation",
            "execute-change-set",
            "--stack-name",
            STACK,
            "--change-set-name",
            CHANGE_SET,
            "--region",
            REGION,
        ],
        check=False,
    )
    if exe.returncode != 0:
        print(exe.stderr[-800:])
        return 1
    print("change-set executing — wait for UPDATE_COMPLETE, then verify Encrypted=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
