# Quy trình Phát triển Đa Mô hình — Phiên bản Thực tế

> **Ý tưởng cốt lõi:** Bạn có hai AI agent ngang cấp — Claude Code và Antigravity.
> Mỗi bên có điểm mạnh riêng. Filesystem là cầu nối. Không cần API thêm.

---

## Tại sao Không Dùng Gemini API Nữa

Antigravity **đã là Gemini** — chạy trong IDE, đọc được toàn bộ codebase, tự chạy terminal, tự cài thư viện. Gọi thêm Gemini API qua script nghĩa là trả tiền hai lần cho cùng một việc.

| Trước (V3) | Bây giờ (V4) |
|-----------|-------------|
| Claude Code → gọi `gemini.py` → nhận code | Claude Code viết spec → Antigravity đọc → implement |
| Tốn thêm Gemini API | Không tốn thêm |
| Latency gọi API | Chạy trực tiếp trong IDE |
| Context bị giới hạn (gửi từng file) | Antigravity đọc toàn bộ repo |

---

## Kiến trúc V4

```
┌──────────────────────────────────────────────────────────┐
│                      BẠN (con người)                      │
│  Nói chuyện với Claude Code (terminal) hoặc Antigravity  │
│  tùy theo loại task                                       │
└──────────────┬───────────────────────────┬───────────────┘
               │                           │
               ▼                           ▼
┌──────────────────────┐       ┌──────────────────────────┐
│     CLAUDE CODE      │       │       ANTIGRAVITY         │
│     (Terminal)       │       │       (IDE / VS Code)     │
│                      │       │                           │
│  Engine: Opus/Sonnet │       │  Engine: Gemini           │
│  Context: 200k       │       │  Context: 1M+ (toàn repo) │
│                      │       │                           │
│  Mạnh hơn:           │       │  Mạnh hơn:                │
│  - Reasoning sâu     │       │  - Đọc codebase lớn       │
│  - Security audit    │       │  - Scaffolding nhanh      │
│  - Architecture      │       │  - Refactor quy mô lớn   │
│  - API design        │       │  - Unit test tự động      │
│  - Git/CI/CD         │       │  - Debug inline           │
└──────────┬───────────┘       └────────────┬─────────────┘
           │                                │
           └──────────────┬─────────────────┘
                          ▼
              ┌───────────────────────┐
              │   Filesystem (repo)   │
              │  docs/modules/*.md    │  ← giao thức trung gian
              │  src/                 │
              │  tests/               │
              └───────────────────────┘
```

**Khác biệt then chốt:** `docs/modules/{name}/design.md` là giao thức trung gian — Claude Code viết spec vào đó, Antigravity đọc và implement. Không copy-paste, không API thêm.

---

## Phân công Rõ ràng

### Claude Code làm (terminal)

- Thiết kế database schema, API contracts
- Viết `docs/modules/{name}/design.md`
- Review security, logic, edge cases
- Quyết định kiến trúc (caching, service boundaries)
- Sửa bug logic phức tạp
- Migration scripts ảnh hưởng data integrity
- Git operations, CI/CD config
- Bất kỳ thứ gì liên quan đến auth, payment, permissions

### Antigravity làm (IDE)

- Đọc `design.md` → sinh implementation đầy đủ
- Scaffolding toàn bộ module từ đầu
- Refactor quy mô lớn (đổi tên, restructure)
- Viết unit/integration tests tự động
- Debug runtime errors (inline context)
- UI components, CSS, boilerplate
- Cài thư viện, setup môi trường

---

## Cách Sử dụng Hàng Ngày

### Ví dụ 1 — Xây module mới

**Bước 1:** Nói với Claude Code (terminal):
```
> Thiết kế module authentication.
  Yêu cầu: JWT + refresh token, PostgreSQL, rate limiting.
  Ghi vào docs/modules/auth/design.md
```

Claude Code sẽ:
1. Viết `docs/modules/auth/design.md` với schema, API contracts, security notes
2. Báo cáo: "Xong, design sẵn sàng để implement"

**Bước 2:** Chuyển sang Antigravity (IDE), giao task:
```
Đọc docs/modules/auth/design.md và implement toàn bộ module auth.
Bao gồm: models, routes, middleware, unit tests.
```

Antigravity sẽ đọc toàn bộ repo + design.md → sinh code hoàn chỉnh.

**Bước 3:** Quay lại Claude Code để review:
```
> Review security cho src/auth/. So sánh với docs/modules/auth/design.md.
```

---

### Ví dụ 2 — Refactor lớn

```
Antigravity: Refactor toàn bộ src/ để chuyển từ callback sang async/await.
             Đảm bảo không break tests hiện có.
```

→ Antigravity phù hợp hơn vì cần đọc toàn bộ codebase cùng lúc.

---

### Ví dụ 3 — Bug phức tạp

```
Claude Code: Tại sao rate limiting trong src/auth/middleware.ts
             không hoạt động đúng khi có nhiều instance?
```

→ Claude Code phù hợp hơn vì cần reasoning về distributed systems.

---

## Tối ưu Chi phí

Dùng Sonnet thay Opus cho các task không cần reasoning sâu:

```bash
# Mặc định hàng ngày — Sonnet đủ cho 80% task
claude --model claude-sonnet-4-6

# Chỉ dùng Opus khi cần: thiết kế kiến trúc, security review
claude --model claude-opus-4-6
```

| Task | Model | Lý do |
|------|-------|-------|
| Thiết kế kiến trúc, security | Opus | Cần reasoning sâu |
| Viết design.md, API contracts | Opus | Quyết định quan trọng |
| Review code từ Antigravity | Sonnet | Đọc + nhận xét, không cần reasoning nặng |
| Git, CI/CD, lint | Sonnet | Task đơn giản |
| Implementation, tests, UI | Antigravity | Gemini đọc toàn repo |

---

## Setup Một Lần

```
[ ] 1. Cài Claude Code: npm install -g @anthropic-ai/claude-code
[ ] 2. Cài Antigravity (IDE)
[ ] 3. Chạy workflow-ai installer để tạo CLAUDE.md + cấu trúc docs/:
       workflow-ai --target ~/projects/my-app
[ ] 4. Mở dự án trong Antigravity
[ ] 5. Mở terminal riêng, chạy: claude
[ ] 6. Bắt đầu: "Thiết kế module đầu tiên: [tên]. Ghi design.md."
```

---

## Checklist Mỗi Module Mới

```
[ ] 1. Claude Code: viết docs/modules/{name}/design.md
[ ] 2. Antigravity: implement từ design.md
[ ] 3. Claude Code: review security + logic
[ ] 4. Antigravity: sửa theo feedback
[ ] 5. Claude Code: git commit + push
```

---

## Tóm tắt

> **Đừng trả tiền hai lần cho cùng một việc.**
> Claude Code = bộ não (thiết kế, quyết định, review).
> Antigravity = đôi tay (implement, refactor, test).
> `design.md` = ngôn ngữ chung giữa hai bên.
