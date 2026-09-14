#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Any


ID_RE = re.compile(r"\b(?:REQ|AC|TEST)-\d+(?:-\d+)?\b")
REQUIRED_FILES = (
    "specification.md",
    "traceability.md",
    "delivery-log.md",
    "conformance.md",
)
PROFILES = {"development", "topic-learning"}
LEARNING_POLICIES = {"auto", "on", "off-with-reason"}


class ValidationResult:
    def __init__(self, ok=True, messages=None, status="LOCAL VERIFIED"):
        self.ok = ok
        self.messages = messages or []
        self.status = status

    def error(self, message: List[Any]) -> None:
        self.ok = False
        self.status = "BLOCKED"
        self.messages.append(message)

    def note(self, message):
        self.messages.append(message)


def load_config(root):
    path = root / "vibe-discipline" / "config.json"
    if not path.is_file():
        raise ValueError(
            "Missing vibe-discipline/config.json; repository is UNCONFIGURED"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid config.json: {exc}") from exc
    return data


def validate_config(config, result):
    if config.get("schema_version") != 1:
        result.error("schema_version must be 1")
    if config.get("profile") not in PROFILES:
        result.error("profile must be development or topic-learning")
    if not isinstance(config.get("active_packages", []), list):
        result.error("active_packages must be a list")
    if config.get("development_learning", "auto") not in LEARNING_POLICIES:
        result.error("development_learning must be auto, on, or off-with-reason")
    commands = config.get("commands", {})
    if not isinstance(commands, dict):
        result.error("commands must be an object")
        return
    for name, argv in commands.items():
        if (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(item, str) and item for item in argv)
        ):
            result.error(f"command {name} must be a non-empty argv string array")


def package_ids(package):
    text_by_file = {}
    all_ids = []
    for name in REQUIRED_FILES:
        path = package / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        text_by_file[name] = text
        if name == "specification.md":
            for line in text.splitlines():
                if line.lstrip().startswith("|"):
                    cells = [
                        cell.strip() for cell in line.strip().strip("|").split("|")
                    ]
                    if cells and ID_RE.fullmatch(cells[0]):
                        all_ids.append(cells[0])
    return text_by_file, all_ids


def validate_package(root, relative, result):
    package = (root / relative).resolve()
    try:
        package.relative_to(root.resolve())
    except ValueError:
        result.error(f"Active package escapes repository: {relative}")
        return
    if not package.is_dir():
        result.error(f"Active package missing: {relative}")
        return
    for name in REQUIRED_FILES:
        if not (package / name).is_file():
            result.error(f"{relative} missing {name}")
    texts, identities = package_ids(package)
    duplicates = sorted({item for item in identities if identities.count(item) > 1})
    if duplicates:
        result.error(f"Duplicate IDs in {relative}: {', '.join(duplicates)}")
    declared = set(identities)
    trace = texts.get("traceability.md", "")
    referenced = set(ID_RE.findall(trace))
    dangling = sorted(referenced - declared)
    if dangling:
        result.error(f"Dangling traceability IDs in {relative}: {', '.join(dangling)}")


def run_configured_command(root, argv, label, result):
    completed = subprocess.run(
        argv, cwd=root, text=True, capture_output=True, shell=False
    )
    if completed.returncode:
        result.error(
            f"{label} failed with exit {completed.returncode}: {completed.stderr.strip() or completed.stdout.strip()}"
        )
    else:
        result.note(f"{label} passed")


def validate_repository(root, phase="fast", run_commands=False):
    root = Path(root).resolve()
    result = ValidationResult()
    try:
        config = load_config(root)
    except ValueError as exc:
        result.error(str(exc))
        return result
    validate_config(config, result)
    if not result.ok:
        return result
    profile = config["profile"]
    active = config.get("active_packages", [])
    if profile == "development":
        for relative in active:
            if not isinstance(relative, str):
                result.error("active package entries must be strings")
            else:
                validate_package(root, relative, result)
    if phase == "full" and run_commands and result.ok:
        integration = config.get("commands", {}).get("integration")
        if integration:
            run_configured_command(root, integration, "integration", result)
        elif profile == "development":
            result.ok = False
            result.status = "UNVERIFIED"
            result.note("No integration command configured; status is UNVERIFIED")
        else:
            result.note(
                "Topic profile has no integration command; lightweight validation only"
            )
    validate_bypasses(root, result)
    return result


def validate_bypasses(root, result):
    bypass_dir = Path(root) / "vibe-discipline" / "bypasses"
    if not bypass_dir.is_dir():
        return
    active = []
    for path in sorted(bypass_dir.glob("BYPASS-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            status = payload.get("status")
            expires = date.fromisoformat(payload["expires"])
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
            result.error(f"Invalid bypass record {path.name}: {exc}")
            continue
        if status == "ACTIVE" and expires < date.today():
            result.error(f"Bypass {path.name} expired on {expires.isoformat()}")
        elif status == "ACTIVE":
            active.append(path.stem)
    if active and result.ok:
        result.status = "BYPASSED"
        result.note(f"Active bypasses: {', '.join(active)}")


def create_bypass(root, scope, reason, compensation, expires):
    root = Path(root).resolve()
    expiry = date.fromisoformat(expires)
    if expiry < date.today():
        raise ValueError("bypass expiry must not be in the past")
    bypass_dir = root / "vibe-discipline" / "bypasses"
    bypass_dir.mkdir(parents=True, exist_ok=True)
    used = []
    for path in bypass_dir.glob("BYPASS-*.json"):
        match = re.fullmatch(r"BYPASS-(\d+)\.json", path.name)
        if match:
            used.append(int(match.group(1)))
    identity = f"BYPASS-{max(used, default=0) + 1:03d}"
    payload = {
        "schema_version": 1,
        "id": identity,
        "status": "ACTIVE",
        "scope": scope,
        "reason": reason,
        "compensation": compensation,
        "expires": expiry.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "authority": "explicit-user-declaration-required",
    }
    path = bypass_dir / f"{identity}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def tree_fingerprint(root):
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=root,
        text=True,
        capture_output=True,
        shell=False,
    )
    material = completed.stdout if completed.returncode == 0 else str(root)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def capture(root, phase, test_id, argv):
    root = Path(root).resolve()
    completed = subprocess.run(
        argv, cwd=root, text=True, capture_output=True, shell=False
    )
    evidence_dir = root / "vibe-discipline" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    payload = {
        "schema_version": 1,
        "test_id": test_id,
        "phase": phase.upper(),
        "argv": argv,
        "observed_exit_code": completed.returncode,
        "classification": "unreviewed-red"
        if phase == "red"
        else "observed-green"
        if completed.returncode == 0
        else "failed-green",
        "captured_at": now.isoformat(),
        "tree_fingerprint": tree_fingerprint(root),
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }
    stem = f"{now.strftime('%Y%m%dT%H%M%S%fZ')}-{test_id}-{phase}"
    path = evidence_dir / f"{stem}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path, payload


def build_parser():
    parser = argparse.ArgumentParser(
        description="Validate and capture Vibe Discipline delivery evidence"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--root", default=".")
    validate.add_argument("--phase", choices=("fast", "full"), default="fast")
    validate.add_argument("--run-commands", action="store_true")
    cap = sub.add_parser("capture")
    cap.add_argument("--root", default=".")
    cap.add_argument("--phase", choices=("red", "green"), required=True)
    cap.add_argument("--test-id", required=True)
    cap.add_argument("argv", nargs=argparse.REMAINDER)
    bypass = sub.add_parser("bypass")
    bypass.add_argument("--root", default=".")
    bypass.add_argument("--scope", required=True)
    bypass.add_argument("--reason", required=True)
    bypass.add_argument("--compensation", required=True)
    bypass.add_argument("--expires", required=True)
    return parser


def main():
    args = build_parser().parse_args()
    if args.command == "validate":
        result = validate_repository(args.root, args.phase, args.run_commands)
        for message in result.messages:
            print(message)
        print(result.status)
        return 0 if result.ok else 1
    if args.command == "bypass":
        try:
            path = create_bypass(
                args.root, args.scope, args.reason, args.compensation, args.expires
            )
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 2
        print(path)
        return 0
    argv = args.argv[1:] if args.argv and args.argv[0] == "--" else args.argv
    if not argv:
        print("capture requires an argv after --", file=sys.stderr)
        return 2
    path, payload = capture(args.root, args.phase, args.test_id, argv)
    print(path)
    print(
        f"observed exit: {payload['observed_exit_code']}; classification: {payload['classification']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
