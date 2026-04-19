#!/usr/bin/env python3
"""
Sinh CLAUDE.md từ ProjectProfile bằng Claude API.
Fallback về template tĩnh nếu API không available.
Chỉ gửi ProjectProfile JSON lên API — không bao giờ gửi source code.
"""

import json
import os
from pathlib import Path


def _load_env(search_from: Path = None):
    """Load .env từ thư mục target project (được truyền vào từ install.py)."""
    if search_from is None:
        return
    env_path = search_from / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def generate_claude_md(profile: dict, target_dir: Path = None) -> str:
    """
    Sinh nội dung CLAUDE.md từ ProjectProfile.
    Thử Claude API trước, fallback về template tĩnh.
    """
    _load_env(target_dir)
    try:
        return _generate_with_claude(profile)
    except Exception as e:
        print(f"[workflow-ai] Claude API không available ({e}), dùng template tĩnh.")
        return _generate_from_template(profile)


# ── Claude API ───────────────────────────────────────────────────────────────

def _generate_with_claude(profile: dict) -> str:
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package chưa được cài: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY chưa được set")

    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    client = anthropic.Anthropic(
        api_key=api_key,
        base_url=base_url,
        timeout=30.0,   # không chờ quá 30s
        max_retries=0,  # tắt retry của SDK — fallback ngay khi lỗi
    )

    prompt = _build_prompt(profile)

    try:
        message = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-6"),
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        raise RuntimeError(f"Gọi Claude API thất bại: {e}")

    # Lọc lấy TextBlock, bỏ qua ThinkingBlock (extended thinking)
    text_blocks = [b for b in message.content if hasattr(b, "text")]
    if not text_blocks:
        raise RuntimeError("Claude API không trả về text block nào")
    return text_blocks[-1].text


def _build_prompt(profile: dict) -> str:
    profile_json = json.dumps(profile, ensure_ascii=False, indent=2)

    return f"""Bạn là AI assistant giúp tối ưu workflow phát triển phần mềm.

Dưới đây là thông tin về dự án (đã được extract local, không chứa source code):

```json
{profile_json}
```

Hãy sinh ra nội dung file CLAUDE.md cho dự án này. File này sẽ được Claude Code đọc mỗi khi khởi động để biết cách làm việc với dự án.

Yêu cầu:
1. Phần "## Stack" — liệt kê tech stack đã detect, ngắn gọn
2. Phần "## Quy tắc Phân công Mô hình" — phân công rõ: tự làm vs gọi Gemini, dựa trên stack cụ thể
   - Ví dụ: nếu có React → Gemini sinh components, hooks boilerplate
   - Nếu có FastAPI → Gemini sinh CRUD endpoints, schemas; Opus review auth/business logic
3. Phần "## Cách Gọi Gemini" — hướng dẫn dùng scripts/gemini.py
4. Phần "## Conventions" — naming, formatter, linter theo detect được
5. Phần "## Cấu trúc Dự án" — cấu trúc docs/modules/, src/, tests/

Quy tắc chung phải có (copy nguyên, không thay đổi):
- GỌI GEMINI khi: sinh > 200 dòng boilerplate, UI components, CSS, mock data, CRUD cùng pattern
- TỰ LÀM khi: thiết kế schema/API contracts, business logic, review security, quyết định kiến trúc, sửa bug phức tạp

Chỉ xuất nội dung CLAUDE.md, không có giải thích thêm. Dùng tiếng Việt."""


# ── Template tĩnh (fallback) ─────────────────────────────────────────────────

def _generate_from_template(profile: dict) -> str:
    base_template = (TEMPLATES_DIR / "CLAUDE.md.base").read_text()

    # Inject stack info
    stack = profile.get("stack", {})
    stack_lines = []
    if stack.get("language"):
        stack_lines.append(f"- **Language:** {', '.join(stack['language'])}")
    if stack.get("frontend"):
        stack_lines.append(f"- **Frontend:** {', '.join(stack['frontend'])}")
    if stack.get("backend"):
        stack_lines.append(f"- **Backend:** {', '.join(stack['backend'])}")
    if stack.get("db"):
        stack_lines.append(f"- **Database:** {', '.join(stack['db'])}")
    if stack.get("infra"):
        stack_lines.append(f"- **Infra:** {', '.join(stack['infra'])}")
    if stack.get("test"):
        stack_lines.append(f"- **Testing:** {', '.join(stack['test'])}")

    stack_section = "\n".join(stack_lines) if stack_lines else "- [Chưa detect được — điền thủ công]"

    # Inject conventions
    conv = profile.get("conventions", {})
    conv_lines = []
    if conv.get("naming"):
        conv_lines.append(f"- **Naming:** {conv['naming']}")
    if conv.get("formatter"):
        conv_lines.append(f"- **Formatter:** {conv['formatter']}")
    if conv.get("linter"):
        conv_lines.append(f"- **Linter:** {conv['linter']}")
    if conv.get("package_manager"):
        conv_lines.append(f"- **Package manager:** {conv['package_manager']}")
    if conv.get("api_style"):
        conv_lines.append(f"- **API style:** {conv['api_style']}")

    conv_section = "\n".join(conv_lines) if conv_lines else "- [Chưa detect được — điền thủ công]"

    return base_template.replace("[[STACK]]", stack_section).replace("[[CONVENTIONS]]", conv_section)


if __name__ == "__main__":
    import sys
    profile_path = sys.argv[1] if len(sys.argv) > 1 else None
    if profile_path:
        with open(profile_path) as f:
            profile = json.load(f)
    else:
        # Demo profile
        profile = {
            "stack": {"language": ["TypeScript"], "frontend": ["React", "Vite"],
                      "backend": ["FastAPI"], "db": ["PostgreSQL"], "test": ["Vitest", "pytest"]},
            "conventions": {"naming": "camelCase", "formatter": "Prettier, Black",
                            "linter": "ESLint, Ruff", "api_style": "REST"},
            "project_type": "existing",
        }
    print(generate_claude_md(profile))
