#!/usr/bin/env python3
"""
workflow-ai installer — cài workflow vào dự án mới hoặc đang chạy.

Dùng:
  python install.py --target /path/to/project              # dự án mới (detect từ codebase)
  python install.py --target /path/to/project --docs design.md  # có system design doc
  python install.py --target /path/to/project --update     # update managed section

Yêu cầu:
  pip install anthropic google-genai>=1.0
  export ANTHROPIC_API_KEY=xxx
  export GEMINI_API_KEY=xxx
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

# Thêm repo root vào sys.path để import local modules
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))

from analyzers.detect_stack import detect_stack
from analyzers.detect_conventions import detect_conventions
from analyzers.detect_conflicts import (
    detect_conflicts,
    write_managed_section,
    append_gitignore_entries,
)
from generators.generate_claude_md import generate_claude_md


def main():
    parser = argparse.ArgumentParser(
        description="workflow-ai: cài AI workflow vào dự án của bạn"
    )
    parser.add_argument(
        "--target", "-t",
        default=".",
        help="Đường dẫn đến dự án (mặc định: thư mục hiện tại)",
    )
    parser.add_argument(
        "--docs", "-d",
        help="Đường dẫn đến file system design doc (optional)",
    )
    parser.add_argument(
        "--update", "-u",
        action="store_true",
        help="Update managed section trong CLAUDE.md (không tạo lại từ đầu)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ hiển thị sẽ làm gì, không ghi file",
    )
    parser.add_argument(
        "--profile-only",
        action="store_true",
        help="Chỉ in ProjectProfile JSON, không sinh CLAUDE.md",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.exists():
        print(f"[workflow-ai] Lỗi: Thư mục '{target}' không tồn tại.")
        sys.exit(1)

    print(f"\n[workflow-ai] Phân tích dự án: {target}")
    print("=" * 60)

    # ── Bước 1: Analyze ──────────────────────────────────────────
    print("\n[1/4] Detect stack và conventions (local)...")
    stack = detect_stack(str(target))
    conventions = detect_conventions(str(target))

    # Đọc docs nếu có
    docs_content = None
    if args.docs:
        docs_path = Path(args.docs)
        if docs_path.exists():
            docs_content = docs_path.read_text()
            print(f"      Đọc docs: {args.docs} ({len(docs_content)} chars)")
        else:
            print(f"      CẢNH BÁO: Không tìm thấy docs '{args.docs}', bỏ qua.")

    # ── Bước 2: Build ProjectProfile ─────────────────────────────
    project_type = "existing" if _has_source_code(target) else "new"
    profile = {
        "stack": {k: v for k, v in stack.items() if v},
        "conventions": conventions,
        "project_type": project_type,
        "has_docs": docs_content is not None,
        "docs_summary": docs_content[:2000] if docs_content else None,  # Giới hạn 2000 chars
    }

    _print_profile(profile)

    if args.profile_only:
        print("\n[workflow-ai] Profile JSON:")
        print(json.dumps(profile, ensure_ascii=False, indent=2))
        return

    # ── Bước 3: Detect conflicts ─────────────────────────────────
    print("\n[2/4] Kiểm tra conflicts...")
    conflicts = detect_conflicts(str(target))
    _print_conflicts(conflicts)

    # ── Bước 4: Generate CLAUDE.md ───────────────────────────────
    print("\n[3/4] Sinh CLAUDE.md...")
    claude_md_content = generate_claude_md(profile, target_dir=target)

    # ── Bước 5: Write files ──────────────────────────────────────
    print("\n[4/4] Ghi files...")

    if args.dry_run:
        print("\n[DRY RUN] Sẽ thực hiện:")
        _print_dry_run(target, conflicts)
        print("\n[DRY RUN] Nội dung CLAUDE.md sẽ được ghi:")
        print("-" * 40)
        print(claude_md_content[:500] + "..." if len(claude_md_content) > 500 else claude_md_content)
        return

    # Ghi CLAUDE.md
    _write_claude_md(target, claude_md_content, conflicts["claude_md"], args.update)

    # Tạo cấu trúc docs/modules/
    _setup_docs_structure(target)

    # Tạo .env.example
    _setup_env_files(target)

    # Update .gitignore
    _update_gitignore(target, conflicts["gitignore"])

    print("\n[workflow-ai] Hoàn thành!")
    print("=" * 60)
    _print_next_steps(target)


# ── Write operations ──────────────────────────────────────────────────────────

def _write_claude_md(target: Path, content: str, conflict_info: dict, update_mode: bool):
    path = target / "CLAUDE.md"
    action = conflict_info["action"]

    if action == "create":
        path.write_text(content)
        print(f"      ✓ Tạo mới CLAUDE.md")

    elif action == "update_managed_section" or update_mode:
        write_managed_section(path, content)
        print(f"      ✓ Update managed section trong CLAUDE.md")

    elif action == "append":
        write_managed_section(path, content)
        print(f"      ✓ Append vào CLAUDE.md hiện có ({conflict_info['size_lines']} dòng)")

    else:
        write_managed_section(path, content)
        print(f"      ✓ Ghi CLAUDE.md")


def _setup_docs_structure(target: Path):
    """Tạo cấu trúc docs/modules/ nếu chưa có."""
    docs_dir = target / "docs" / "modules"
    if not docs_dir.exists():
        docs_dir.mkdir(parents=True)
        # Tạo file README làm hướng dẫn
        (docs_dir / "README.md").write_text(
            "# Module Design Specs\n\n"
            "Mỗi module có một thư mục riêng với file `design.md`.\n\n"
            "## Cấu trúc\n"
            "```\n"
            "docs/modules/\n"
            "├── auth/\n"
            "│   └── design.md   ← Claude Code viết, Antigravity đọc để implement\n"
            "├── users/\n"
            "│   └── design.md\n"
            "└── ...\n"
            "```\n\n"
            "## Quy trình\n"
            "1. Claude Code viết `design.md` (schema, API contracts, security notes)\n"
            "2. Antigravity đọc `design.md` + toàn bộ repo → implement\n"
            "3. Claude Code review output → commit\n"
        )
        print("      ✓ Tạo docs/modules/ structure")
    else:
        print("      ✓ docs/modules/ đã tồn tại")


def _setup_env_files(target: Path):
    """Tạo .env.example nếu chưa có, đảm bảo .env không bị commit."""
    env_example = target / ".env.example"
    env_file = target / ".env"

    if not env_example.exists():
        env_example.write_text(
            "# API key cho Claude Code (workflow-ai installer)\n"
            "# Copy file này thành .env rồi điền giá trị thật\n"
            "ANTHROPIC_API_KEY=\n"
            "\n"
            "# Model tuỳ chọn (mặc định: claude-opus-4-6)\n"
            "# ANTHROPIC_MODEL=claude-sonnet-4-6\n"
            "\n"
            "# Proxy tuỳ chọn\n"
            "# ANTHROPIC_BASE_URL=https://your-proxy.example.com\n"
        )
        print("      ✓ Tạo .env.example")
    else:
        print("      ✓ .env.example đã tồn tại")

    if not env_file.exists():
        print("      ℹ Tạo .env từ .env.example rồi điền API keys:")
        print(f"        cp {env_example} {env_file}")


def _update_gitignore(target: Path, conflict_info: dict):
    entries_needed = [".env", ".env.local", "*.pyc", "__pycache__/", ".DS_Store"]
    missing = conflict_info.get("missing_entries", entries_needed)

    if conflict_info["action"] == "create":
        (target / ".gitignore").write_text("\n".join(entries_needed) + "\n")
        print(f"      ✓ Tạo .gitignore")
    elif conflict_info["action"] == "append_missing":
        append_gitignore_entries(target, missing)
        print(f"      ✓ Thêm {len(missing)} entries vào .gitignore: {', '.join(missing)}")
    else:
        print(f"      ✓ .gitignore OK")


# ── Display helpers ───────────────────────────────────────────────────────────

def _print_profile(profile: dict):
    stack = profile["stack"]
    print(f"\n      Kết quả detect:")
    print(f"      - Project type: {profile['project_type']}")
    if stack.get("language"):
        print(f"      - Language:  {', '.join(stack['language'])}")
    if stack.get("frontend"):
        print(f"      - Frontend:  {', '.join(stack['frontend'])}")
    if stack.get("backend"):
        print(f"      - Backend:   {', '.join(stack['backend'])}")
    if stack.get("db"):
        print(f"      - Database:  {', '.join(stack['db'])}")
    if stack.get("infra"):
        print(f"      - Infra:     {', '.join(stack['infra'])}")
    if stack.get("test"):
        print(f"      - Testing:   {', '.join(stack['test'])}")

    conv = profile["conventions"]
    if conv.get("formatter"):
        print(f"      - Formatter: {conv['formatter']}")
    if conv.get("linter"):
        print(f"      - Linter:    {conv['linter']}")
    if conv.get("package_manager"):
        print(f"      - Pkg mgr:   {conv['package_manager']}")


def _print_conflicts(conflicts: dict):
    claude_status = conflicts["claude_md"]["status"]
    gi_status = conflicts["gitignore"]["status"]
    docs_status = "missing" if not (Path(".") / "docs" / "modules").exists() else "exists"

    status_icon = {"missing": "○", "exists": "●", "managed": "◉", "exists_unmanaged": "●"}
    print(f"      {status_icon.get(claude_status, '?')} CLAUDE.md: {claude_status}")
    print(f"      {status_icon.get(docs_status, '?')} docs/modules/: {docs_status}")
    print(f"      {status_icon.get(gi_status, '?')} .gitignore: {gi_status}")

    existing = conflicts["existing_configs"]
    if existing:
        print(f"      → Configs đã có: {', '.join(existing)}")


def _print_dry_run(target: Path, conflicts: dict):
    actions = {
        "CLAUDE.md": conflicts["claude_md"]["action"],
        "docs/modules/": "create nếu chưa có",
        ".gitignore": conflicts["gitignore"]["action"],
    }
    for f, action in actions.items():
        print(f"      - {f}: {action}")


def _print_next_steps(target: Path):
    print("\nBước tiếp theo:")
    print(f"  1. Mở dự án trong Antigravity IDE")
    print(f"  2. Mở terminal riêng, vào dự án và chạy Claude Code:")
    print(f"       cd {target} && claude")
    print("  3. Nói với Claude Code:")
    print("       \"Thiết kế module đầu tiên: [tên]. Ghi vào docs/modules/[tên]/design.md\"")
    print("  4. Sau khi có design.md → chuyển sang Antigravity để implement")
    print("\n  Để update sau khi stack thay đổi:")
    print(f"       python3 {REPO_ROOT}/install.py --target {target} --update")


def _has_source_code(root: Path) -> bool:
    src_dirs = ["src", "app", "lib", "pkg", "api"]
    return any((root / d).exists() for d in src_dirs)


if __name__ == "__main__":
    main()
