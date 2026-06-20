from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "COMMERCIAL_READY.md",
    "FEASIBILITY.md",
    "docs/ARCHITECTURE.md",
    "docs/DEPLOYMENT.md",
    ".github/workflows/tests.yml",
    ".env.example",
    ".env.production.example",
    ".gitignore",
]

FORBIDDEN_TRACKED_PATTERNS = [
    re.compile(r"(^|/)\.env$"),
    re.compile(r"\.db(-wal|-shm)?$"),
    re.compile(r"\.sqlite(3)?$"),
    re.compile(r"(^|/)data/(?!\.gitkeep$).+"),
    re.compile(r"\.log$"),
    re.compile(r"__pycache__/"),
    re.compile(r"\.pyc$"),
]

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
]

ALLOWED_SECRET_PLACEHOLDERS = {
    "change-me-now",
    "change-this-session-secret",
    "change-this-webhook-secret",
    "change-this-unsubscribe-secret",
    "replace-with-a-strong-password",
    "replace-with-a-long-random-session-secret",
    "replace-with-a-long-random-webhook-secret",
    "replace-with-a-long-random-unsubscribe-secret",
    "smoke-test-session-secret",
    "smoke-webhook-secret",
    "smoke-unsubscribe-secret",
    "feasibility-unsubscribe-secret",
    "test-secret",
    "test-session-secret",
    "secret-password",
}


def git_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=PROJECT_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def check_required_files(errors: list[str]) -> None:
    for relative in REQUIRED_FILES:
        if not (PROJECT_ROOT / relative).exists():
            errors.append(f"Missing required file: {relative}")


def check_forbidden_tracked_files(files: list[str], errors: list[str]) -> None:
    for relative in files:
        normalized = relative.replace("\\", "/")
        for pattern in FORBIDDEN_TRACKED_PATTERNS:
            if pattern.search(normalized):
                errors.append(f"Forbidden tracked file: {relative}")
                break


def check_secret_patterns(files: list[str], errors: list[str]) -> None:
    for relative in files:
        path = PROJECT_ROOT / relative
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico"}:
            continue
        text = read_text(path)
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"Potential secret pattern in {relative}: {pattern.pattern}")


def check_env_examples(errors: list[str]) -> None:
    for relative in [".env.example", ".env.production.example"]:
        path = PROJECT_ROOT / relative
        if not path.exists():
            continue
        for lineno, line in enumerate(read_text(path).splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            name, value = stripped.split("=", 1)
            if name.endswith("_HEADER"):
                continue
            if any(token in name for token in ["PASSWORD", "SECRET", "TOKEN", "API_KEY"]) and value:
                if value not in ALLOWED_SECRET_PLACEHOLDERS and not value.startswith("replace-with-"):
                    errors.append(f"{relative}:{lineno} has a non-placeholder secret value for {name}.")


def check_requirements_pinned(errors: list[str]) -> None:
    requirements = PROJECT_ROOT / "requirements.txt"
    if not requirements.exists():
        errors.append("Missing requirements.txt")
        return
    for lineno, line in enumerate(read_text(requirements).splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "==" not in stripped:
            errors.append(f"requirements.txt:{lineno} is not pinned with ==: {stripped}")


def check_markdown_links(files: list[str], errors: list[str]) -> None:
    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for relative in files:
        if not relative.lower().endswith(".md"):
            continue
        text = read_text(PROJECT_ROOT / relative)
        for match in link_re.finditer(text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#", 1)[0]
            if not target:
                continue
            linked = (PROJECT_ROOT / Path(relative).parent / target).resolve()
            if not str(linked).startswith(str(PROJECT_ROOT.resolve())) or not linked.exists():
                errors.append(f"{relative} has broken local link: {target}")


def main() -> int:
    errors: list[str] = []
    files = git_files()
    check_required_files(errors)
    check_forbidden_tracked_files(files, errors)
    check_secret_patterns(files, errors)
    check_env_examples(errors)
    check_requirements_pinned(errors)
    check_markdown_links(files, errors)

    if errors:
        print("Release check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Release check passed")
    print(f"Tracked files checked: {len(files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
