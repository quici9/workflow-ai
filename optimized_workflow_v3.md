# Quy trình Phát triển Đa Mô hình — Phiên bản Đơn giản

> **Ý tưởng cốt lõi:** Bạn chỉ tương tác với MỘT nơi duy nhất — Claude Code.
> Claude Code tự quyết định khi nào cần gọi Gemini, tự truyền context, tự nhận kết quả.
> Bạn không copy-paste gì cả.

---

## Tại sao Phiên bản Trước Vẫn Phức tạp

Phiên bản trước yêu cầu bạn:
- Tự mở Opus ở một tab, Gemini ở tab khác
- Tự copy `design.md` từ Opus sang Gemini
- Tự cập nhật `.handoff/context.md` mỗi lần chuyển
- Tự nhớ gửi đúng file cho đúng mô hình

→ Bạn trở thành "router thủ công" — chậm, dễ quên, không nhất quán.

**Giải pháp:** Dùng Claude Code (chạy trên terminal, truy cập filesystem trực tiếp) làm orchestrator duy nhất. Claude Code tự gọi Gemini API khi cần sinh code nhanh/rẻ.

---

## Kiến trúc Mới

```
┌─────────────────────────────────────────────────┐
│                   BẠN (con người)                │
│          Chỉ nói chuyện với Claude Code          │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              CLAUDE CODE (Orchestrator)           │
│                                                   │
│  ┌───────────┐  ┌────────────┐  ┌─────────────┐ │
│  │  Opus 4   │  │  Sonnet 4  │  │ Gemini API  │ │
│  │ (tự dùng  │  │ (sub-agent │  │ (gọi qua    │ │
│  │  khi cần) │  │  nhẹ)      │  │  script)    │ │
│  └───────────┘  └────────────┘  └─────────────┘ │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │           Filesystem (repo dự án)            │ │
│  │  - Đọc/ghi trực tiếp, không cần copy-paste  │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**Khác biệt then chốt:** Context không truyền qua file `.handoff/` nữa — Claude Code đã CÓ context trong đầu vì nó là người tạo ra design, gọi Gemini, nhận code, rồi review. Mọi thứ diễn ra trong cùng một phiên làm việc.

---

## Thiết lập Một Lần

### 1. Cài Claude Code
```bash
npm install -g @anthropic-ai/claude-code
```

### 2. Tạo script gọi Gemini
Lưu vào repo dự án tại `scripts/gemini.py`:

```python
#!/usr/bin/env python3
"""Script để Claude Code gọi Gemini API sinh code.

Yêu cầu: pip install -q -U google-genai
Dùng: python scripts/gemini.py "prompt" [file1] [file2] ...
      GEMINI_MODEL=gemini-3-flash-preview python scripts/gemini.py "prompt"  # rẻ hơn
"""

import re
import sys
import os
from google import genai

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-pro-preview")


def strip_markdown_fence(text: str) -> str:
    """Xóa markdown code fence mà Gemini thường thêm vào."""
    text = text.strip()
    text = re.sub(r"^```[^\n]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    return text


def call_gemini(prompt: str, context_files: list[str] = None) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY chưa được set")

    client = genai.Client(api_key=api_key)

    # Đọc các file context nếu có
    full_prompt = ""
    if context_files:
        for f in context_files:
            try:
                with open(f) as fh:
                    full_prompt += f"\n--- {f} ---\n{fh.read()}\n"
            except FileNotFoundError:
                print(f"CẢNH BÁO: Không tìm thấy file {f}", file=sys.stderr)

    full_prompt += f"\n--- NHIỆM VỤ ---\n{prompt}"

    response = client.models.generate_content(
        model=MODEL,
        contents=full_prompt,
    )
    return strip_markdown_fence(response.text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Dùng: python scripts/gemini.py \"prompt\" [file1] [file2] ...", file=sys.stderr)
        sys.exit(1)

    try:
        prompt = sys.argv[1]
        files = sys.argv[2:] if len(sys.argv) > 2 else []
        print(call_gemini(prompt, files))
    except Exception as e:
        print(f"GEMINI_ERROR: {e}", file=sys.stderr)
        sys.exit(1)
```

### 3. Tạo file CLAUDE.md (hướng dẫn cho Claude Code)
Đặt ở thư mục gốc repo — Claude Code tự đọc file này mỗi khi khởi động:

```markdown
# Hướng dẫn Dự án

## Quy tắc Phân công Mô hình
- TỰ LÀM (Opus): Thiết kế kiến trúc, API contracts, review logic/security
- GỌI GEMINI (qua scripts/gemini.py): Sinh UI components, boilerplate, CRUD code
- TỰ LÀM (Sonnet sub-agent): Unit tests, lint fixes, code review cơ bản

## Cách Gọi Gemini
```
python scripts/gemini.py "prompt" [file1] [file2] ...
```
Gemini sẽ nhận nội dung các file + prompt. Output là code thuần.

## Cấu trúc Dự án
- docs/modules/{name}/design.md — thiết kế từng module
- src/ — mã nguồn
- tests/ — unit tests

## Stack
[Điền stack cụ thể của bạn]
```

---

## Cách Sử dụng Hàng Ngày

### Bạn chỉ cần nói với Claude Code bằng ngôn ngữ tự nhiên:

**Ví dụ 1 — Xây module mới từ đầu:**
```
> Thiết kế và xây module authentication.
  Yêu cầu: JWT + refresh token, PostgreSQL, rate limiting.
  Dùng Gemini để sinh code UI, tự review logic auth.
```

Claude Code sẽ tự động:
1. Tự viết `docs/modules/auth/design.md` (dùng reasoning Opus)
2. Gọi `python scripts/gemini.py` với design.md để Gemini sinh code
3. Nhận code từ Gemini, ghi vào `src/`
4. Tự review phần auth logic (Opus review)
5. Sửa lỗi nếu phát hiện
6. Báo cáo kết quả cho bạn

**Ví dụ 2 — Chỉ cần sinh code nhanh:**
```
> Dùng Gemini tạo component React cho trang product listing.
  Theo design trong docs/modules/products/design.md.
```

**Ví dụ 3 — Chỉ cần review:**
```
> Review security cho src/auth/. So sánh với design gốc.
```

### Không cần nữa:
- ❌ Copy-paste giữa các tab
- ❌ Tự cập nhật `.handoff/context.md`
- ❌ Nhớ file nào gửi cho mô hình nào
- ❌ Viết prompt chuyển giao

---

## Khi nào Claude Code Tự Gọi Gemini vs Tự Làm

Viết quy tắc này vào `CLAUDE.md` để Claude Code tuân theo:

```markdown
## Quy tắc Tự động

### GỌI GEMINI khi:
- Sinh > 200 dòng code boilerplate/UI
- Tạo components React/Vue từ wireframe hoặc mô tả
- Viết CSS/styling phức tạp
- Sinh mock data hoặc seed scripts
- Tạo nhiều file CRUD cùng pattern

### TỰ LÀM khi:
- Thiết kế database schema, API contracts
- Viết business logic (tính toán, state machine, workflow)
- Review code (logic, security, edge cases)
- Quyết định kiến trúc (caching, scaling, service boundaries)
- Sửa bug logic phức tạp
- Viết migration scripts có ảnh hưởng data integrity
```

---

## So sánh 3 Phiên bản

| Tiêu chí | V1 (ban đầu) | V2 (tối ưu chi phí) | V3 (đơn giản) |
|-----------|---------------|----------------------|----------------|
| Số công cụ bạn mở | 2-3 | 2-3 | 1 (Claude Code) |
| Copy-paste thủ công | Nhiều | Có, nhưng có checklist | Không |
| Rủi ro mất context | Cao | Trung bình | Thấp |
| Thời gian setup | 0 | 30 phút | 15 phút (1 lần) |
| Chi phí Opus | Cao (3 giai đoạn) | Thấp (phân tầng) | Thấp (phân tầng) |
| Tốc độ sinh code | Phụ thuộc Gemini | Phụ thuộc Gemini | Tương đương |
| Phù hợp với | Team quy mô lớn | Dev solo/nhỏ, dùng API | Dev solo/nhỏ, muốn đơn giản |

---

## Hạn chế và Giải pháp

### Hạn chế 1: Claude Code dùng Opus → vẫn tốn tiền cho việc nhỏ
**Giải pháp:** Khởi động Claude Code với model phù hợp theo từng loại task:
```bash
# Task nhẹ (lint, test, boilerplate) — dùng Sonnet
claude --model claude-sonnet-4-6

# Task nặng (thiết kế, review security) — dùng Opus
claude --model claude-opus-4-6
```
Hoặc đặt biến môi trường mặc định trong shell:
```bash
export ANTHROPIC_MODEL=claude-sonnet-4-6
```

### Hạn chế 2: Gemini output có thể không đúng format mong muốn
**Giải pháp:** Thêm vào prompt template trong `scripts/gemini.py`:
```python
SYSTEM_PROMPT = """
Bạn là code generator. Quy tắc:
- Chỉ xuất code, không giải thích
- Dùng TypeScript strict mode
- Tuân theo ESLint config trong dự án
- Mỗi file bắt đầu bằng comment: // Generated by Gemini — cần review
"""
```

### Hạn chế 3: Gọi Gemini nhiều lần liên tiếp → rate limit
**Giải pháp:** Gemini API có quota theo phút. Nếu Claude Code gọi nhiều lần trong workflow dài, thêm retry đơn giản vào script:
```python
import time

for attempt in range(3):
    try:
        response = client.models.generate_content(model=MODEL, contents=full_prompt)
        break
    except Exception as e:
        if attempt == 2:
            raise
        time.sleep(10 * (attempt + 1))
```

### Hạn chế 4: Context window của Gemini khi dự án lớn
**Giải pháp:** Script `gemini.py` chỉ gửi file liên quan, không gửi toàn bộ repo:
```bash
# Claude Code chỉ truyền file cần thiết
python scripts/gemini.py "Tạo component UserProfile" \
  docs/modules/users/design.md \
  src/types/user.ts \
  src/components/shared/Layout.tsx
```

---

## Checklist Bắt đầu Dự án Mới

```
[ ] 1. Cài Claude Code: npm install -g @anthropic-ai/claude-code
[ ] 2. Cài dependency: pip install -q -U google-genai
[ ] 3. Set API keys: export GEMINI_API_KEY=xxx (thêm vào ~/.zshrc để persist)
[ ] 4. Thêm .env vào .gitignore nếu lưu key trong file
[ ] 5. Copy scripts/gemini.py vào repo
[ ] 6. Viết CLAUDE.md với stack + quy tắc phân công
[ ] 7. Chạy: claude (trong thư mục dự án)
[ ] 8. Nói: "Thiết kế module đầu tiên: [tên]. Dùng Gemini sinh code."
[ ] 9. Ngồi xem Claude Code tự chạy.
```

---

## Tóm tắt

> **Đừng làm router thủ công giữa các AI.** Để Claude Code làm orchestrator —
> nó có filesystem, có terminal, có khả năng gọi API bên ngoài.
> Bạn chỉ cần mô tả cái bạn muốn, Claude Code tự phân công.
