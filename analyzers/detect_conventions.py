#!/usr/bin/env python3
"""
Detect coding conventions từ config files — chạy hoàn toàn local.
"""

import json
import re
from pathlib import Path


def detect_conventions(project_root: str) -> dict:
    root = Path(project_root)
    conventions = {
        "naming": _detect_naming(root),
        "formatter": _detect_formatter(root),
        "linter": _detect_linter(root),
        "api_style": _detect_api_style(root),
        "test_style": _detect_test_style(root),
        "package_manager": _detect_package_manager(root),
    }
    return {k: v for k, v in conventions.items() if v}


# ── Naming conventions ───────────────────────────────────────────────────────

def _detect_naming(root: Path) -> str:
    """Heuristic: đọc tên files trong src/ để đoán naming convention."""
    src_dirs = ["src", "app", "lib", "pkg"]
    files = []
    for d in src_dirs:
        src = root / d
        if src.exists():
            files = [f.stem for f in src.rglob("*") if f.is_file() and f.suffix in
                     (".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rb")][:30]
            if files:
                break

    if not files:
        return ""

    snake = sum(1 for f in files if "_" in f and f == f.lower())
    kebab = sum(1 for f in files if "-" in f)
    pascal = sum(1 for f in files if f and f[0].isupper() and "_" not in f)
    camel = sum(1 for f in files if f and f[0].islower() and "_" not in f and "-" not in f
                and any(c.isupper() for c in f))

    scores = {"snake_case": snake, "kebab-case": kebab, "PascalCase": pascal, "camelCase": camel}
    dominant = max(scores, key=scores.get)
    return dominant if scores[dominant] > 0 else ""


# ── Formatter ────────────────────────────────────────────────────────────────

def _detect_formatter(root: Path) -> str:
    formatters = []

    # Prettier
    prettier_files = [".prettierrc", ".prettierrc.json", ".prettierrc.js",
                      ".prettierrc.yaml", ".prettierrc.yml", "prettier.config.js"]
    if any((root / f).exists() for f in prettier_files):
        formatters.append("Prettier")

    # Black / Ruff (Python)
    if _pyproject_has(root, "black") or (root / ".black").exists():
        formatters.append("Black")
    if _pyproject_has(root, "ruff"):
        formatters.append("Ruff")

    # gofmt (implicit nếu là Go project)
    if (root / "go.mod").exists():
        formatters.append("gofmt")

    return ", ".join(formatters)


# ── Linter ───────────────────────────────────────────────────────────────────

def _detect_linter(root: Path) -> str:
    linters = []

    eslint_files = [".eslintrc", ".eslintrc.json", ".eslintrc.js",
                    ".eslintrc.yaml", ".eslintrc.yml", "eslint.config.js", "eslint.config.mjs"]
    if any((root / f).exists() for f in eslint_files):
        linters.append("ESLint")

    if _pyproject_has(root, "flake8") or (root / ".flake8").exists() or (root / "setup.cfg").exists():
        linters.append("flake8")
    if _pyproject_has(root, "ruff"):
        if "Ruff" not in linters:
            linters.append("Ruff")
    if _pyproject_has(root, "mypy") or (root / "mypy.ini").exists():
        linters.append("mypy")

    if (root / ".rubocop.yml").exists():
        linters.append("RuboCop")

    if (root / "golangci.yml").exists() or (root / ".golangci.yml").exists():
        linters.append("golangci-lint")

    return ", ".join(linters)


# ── API style ────────────────────────────────────────────────────────────────

def _detect_api_style(root: Path) -> str:
    styles = []

    # GraphQL
    graphql_files = list(root.rglob("*.graphql")) + list(root.rglob("*.gql"))
    if graphql_files or (root / "schema.graphql").exists():
        styles.append("GraphQL")

    # gRPC
    proto_files = list(root.rglob("*.proto"))
    if proto_files:
        styles.append("gRPC")

    # OpenAPI / REST
    openapi_files = ["openapi.yaml", "openapi.json", "swagger.yaml", "swagger.json"]
    if any((root / f).exists() for f in openapi_files):
        styles.append("REST (OpenAPI)")
    elif not styles:
        styles.append("REST")

    return ", ".join(styles)


# ── Test style ───────────────────────────────────────────────────────────────

def _detect_test_style(root: Path) -> str:
    styles = []

    test_dirs = ["tests", "test", "__tests__", "spec"]
    for d in test_dirs:
        if (root / d).exists():
            # Unit vs integration vs e2e
            td = root / d
            if any(td.rglob("*.e2e.*")) or (td / "e2e").exists():
                styles.append("e2e")
            if any(td.rglob("*.integration.*")) or (td / "integration").exists():
                styles.append("integration")
            styles.append("unit")
            break

    return ", ".join(dict.fromkeys(styles))


# ── Package manager ──────────────────────────────────────────────────────────

def _detect_package_manager(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        return "bun"
    if (root / "package-lock.json").exists():
        return "npm"
    if (root / "uv.lock").exists():
        return "uv"
    if (root / "poetry.lock").exists():
        return "poetry"
    if (root / "Pipfile.lock").exists():
        return "pipenv"
    return ""


# ── Helpers ──────────────────────────────────────────────────────────────────

def _pyproject_has(root: Path, tool: str) -> bool:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return False
    return tool in pyproject.read_text()


if __name__ == "__main__":
    import sys
    import pprint
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    pprint.pprint(detect_conventions(path))
