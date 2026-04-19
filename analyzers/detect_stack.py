#!/usr/bin/env python3
"""
Detect tech stack từ project files — chạy hoàn toàn local, không gửi code ra ngoài.
"""

import json
import os
import re
from pathlib import Path


def detect_stack(project_root: str) -> dict:
    root = Path(project_root)
    stack = {
        "frontend": [],
        "backend": [],
        "db": [],
        "infra": [],
        "test": [],
        "language": [],
    }

    _detect_javascript(root, stack)
    _detect_python(root, stack)
    _detect_ruby(root, stack)
    _detect_go(root, stack)
    _detect_java(root, stack)
    _detect_infra(root, stack)

    # Deduplicate
    return {k: list(dict.fromkeys(v)) for k, v in stack.items()}


# ── JavaScript / TypeScript ──────────────────────────────────────────────────

def _detect_javascript(root: Path, stack: dict):
    pkg = root / "package.json"
    if not pkg.exists():
        return

    try:
        data = json.loads(pkg.read_text())
    except json.JSONDecodeError:
        return

    all_deps = {
        **data.get("dependencies", {}),
        **data.get("devDependencies", {}),
    }

    # Language
    if (root / "tsconfig.json").exists() or any(all_deps.get(p) for p in ["typescript", "ts-node"]):
        stack["language"].append("TypeScript")
    else:
        stack["language"].append("JavaScript")

    # Frontend frameworks
    _match_deps(all_deps, stack["frontend"], {
        "react": "React",
        "next": "Next.js",
        "nuxt": "Nuxt.js",
        "vue": "Vue",
        "@angular/core": "Angular",
        "svelte": "Svelte",
        "solid-js": "SolidJS",
        "astro": "Astro",
    })

    # Build tools
    _match_deps(all_deps, stack["frontend"], {
        "vite": "Vite",
        "webpack": "Webpack",
        "esbuild": "esbuild",
        "parcel": "Parcel",
        "turbopack": "Turbopack",
    })

    # Backend (Node)
    _match_deps(all_deps, stack["backend"], {
        "express": "Express",
        "fastify": "Fastify",
        "hono": "Hono",
        "koa": "Koa",
        "@nestjs/core": "NestJS",
        "trpc": "tRPC",
    })

    # ORM / DB client
    _match_deps(all_deps, stack["db"], {
        "prisma": "Prisma",
        "@prisma/client": "Prisma",
        "drizzle-orm": "Drizzle",
        "typeorm": "TypeORM",
        "sequelize": "Sequelize",
        "mongoose": "Mongoose",
        "pg": "PostgreSQL",
        "mysql2": "MySQL",
        "better-sqlite3": "SQLite",
        "redis": "Redis",
        "ioredis": "Redis",
    })

    # Testing
    _match_deps(all_deps, stack["test"], {
        "vitest": "Vitest",
        "jest": "Jest",
        "mocha": "Mocha",
        "@playwright/test": "Playwright",
        "cypress": "Cypress",
        "@testing-library/react": "Testing Library",
    })


# ── Python ───────────────────────────────────────────────────────────────────

def _detect_python(root: Path, stack: dict):
    deps = _read_python_deps(root)
    if not deps:
        return

    stack["language"].append("Python")

    _match_deps(deps, stack["backend"], {
        "fastapi": "FastAPI",
        "flask": "Flask",
        "django": "Django",
        "tornado": "Tornado",
        "aiohttp": "aiohttp",
        "litestar": "Litestar",
        "starlette": "Starlette",
    })

    _match_deps(deps, stack["db"], {
        "sqlalchemy": "SQLAlchemy",
        "alembic": "Alembic",
        "tortoise-orm": "Tortoise ORM",
        "databases": "databases",
        "psycopg2": "PostgreSQL",
        "psycopg": "PostgreSQL",
        "pymysql": "MySQL",
        "motor": "MongoDB",
        "pymongo": "MongoDB",
        "redis": "Redis",
        "aioredis": "Redis",
    })

    _match_deps(deps, stack["test"], {
        "pytest": "pytest",
        "unittest": "unittest",
        "hypothesis": "Hypothesis",
    })

    # ML / Data
    _match_deps(deps, stack["backend"], {
        "torch": "PyTorch",
        "tensorflow": "TensorFlow",
        "scikit-learn": "scikit-learn",
        "pandas": "pandas",
        "numpy": "numpy",
    })


def _read_python_deps(root: Path) -> dict:
    """Đọc dependencies từ pyproject.toml hoặc requirements.txt."""
    # pyproject.toml (poetry / hatch / uv)
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text()
        # Extract package names (không parse TOML để tránh dependency)
        names = re.findall(r'^\s*"?([a-zA-Z0-9_\-]+)"?\s*[=<>!~]', text, re.MULTILINE)
        return {n.lower(): True for n in names}

    # requirements.txt
    req = root / "requirements.txt"
    if req.exists():
        names = re.findall(r'^([a-zA-Z0-9_\-]+)', req.read_text(), re.MULTILINE)
        return {n.lower(): True for n in names}

    return {}


# ── Ruby ─────────────────────────────────────────────────────────────────────

def _detect_ruby(root: Path, stack: dict):
    gemfile = root / "Gemfile"
    if not gemfile.exists():
        return

    stack["language"].append("Ruby")
    text = gemfile.read_text()

    gems = {
        "rails": "Rails",
        "sinatra": "Sinatra",
        "rspec": "RSpec",
        "minitest": "Minitest",
        "activerecord": "ActiveRecord",
        "pg": "PostgreSQL",
        "mysql2": "MySQL",
        "redis": "Redis",
    }
    for gem, label in gems.items():
        if re.search(rf"gem ['\"]?{gem}['\"]?", text):
            target = _gem_target(gem)
            stack[target].append(label)


def _gem_target(gem: str) -> str:
    if gem in ("rails", "sinatra"):
        return "backend"
    if gem in ("rspec", "minitest"):
        return "test"
    if gem in ("pg", "mysql2", "activerecord", "redis"):
        return "db"
    return "backend"


# ── Go ───────────────────────────────────────────────────────────────────────

def _detect_go(root: Path, stack: dict):
    gomod = root / "go.mod"
    if not gomod.exists():
        return

    stack["language"].append("Go")
    text = gomod.read_text()

    packages = {
        "gin-gonic/gin": "Gin",
        "labstack/echo": "Echo",
        "gofiber/fiber": "Fiber",
        "go-chi/chi": "Chi",
        "gorilla/mux": "Gorilla Mux",
        "gorm.io/gorm": "GORM",
        "jackc/pgx": "PostgreSQL",
        "go-redis/redis": "Redis",
        "stretchr/testify": "Testify",
    }
    for pkg, label in packages.items():
        if pkg in text:
            target = "backend" if label not in ("Testify",) else "test"
            stack[target].append(label)


# ── Java / Kotlin ────────────────────────────────────────────────────────────

def _detect_java(root: Path, stack: dict):
    pom = root / "pom.xml"
    gradle = root / "build.gradle"
    gradle_kts = root / "build.gradle.kts"

    if not any(f.exists() for f in [pom, gradle, gradle_kts]):
        return

    lang = "Kotlin" if gradle_kts.exists() else "Java"
    stack["language"].append(lang)

    text = ""
    for f in [pom, gradle, gradle_kts]:
        if f.exists():
            text += f.read_text()

    if "spring-boot" in text or "springframework" in text:
        stack["backend"].append("Spring Boot")
    if "junit" in text.lower():
        stack["test"].append("JUnit")
    if "postgresql" in text.lower():
        stack["db"].append("PostgreSQL")
    if "mysql" in text.lower():
        stack["db"].append("MySQL")
    if "redis" in text.lower():
        stack["db"].append("Redis")


# ── Infrastructure ───────────────────────────────────────────────────────────

def _detect_infra(root: Path, stack: dict):
    checks = {
        "Dockerfile": "Docker",
        "docker-compose.yml": "Docker Compose",
        "docker-compose.yaml": "Docker Compose",
        ".github/workflows": "GitHub Actions",
        ".gitlab-ci.yml": "GitLab CI",
        "Jenkinsfile": "Jenkins",
        "terraform": "Terraform",
        "k8s": "Kubernetes",
        "kubernetes": "Kubernetes",
        "helm": "Helm",
        ".env.example": "dotenv",
    }
    for path_str, label in checks.items():
        if (root / path_str).exists():
            stack["infra"].append(label)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _match_deps(deps: dict, target: list, mapping: dict):
    for key, label in mapping.items():
        if key.lower() in deps:
            target.append(label)


if __name__ == "__main__":
    import sys
    import pprint
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    pprint.pprint(detect_stack(path))
