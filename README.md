# workflow-ai

Cài AI workflow (Claude Code + Antigravity) vào bất kỳ dự án nào — tự động detect stack, sinh CLAUDE.md tương thích, tạo cấu trúc `docs/modules/` làm giao thức trung gian giữa hai agent.

## Workflow

```
Claude Code (terminal)          Antigravity (IDE)
        │                               │
        │  viết design.md               │
        ├──────────────────────────────>│
        │                               │  implement
        │                               │  (đọc toàn repo)
        │         review output         │
        │<──────────────────────────────│
        │                               │
        │  git commit + push            │
        ▼                               ▼
                  Filesystem (repo)
```

- **Claude Code** = bộ não: thiết kế, quyết định, review security, git
- **Antigravity** = đôi tay: implement, refactor, test, scaffolding
- **`docs/modules/{name}/design.md`** = giao thức trung gian, không copy-paste

## Cài đặt (một lần)

```bash
git clone https://github.com/quici9/workflow-ai.git ~/Projects/workflow-ai
cd ~/Projects/workflow-ai

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Thêm alias vào `~/.zshrc`:
```bash
alias workflow-ai='source ~/Projects/workflow-ai/.venv/bin/activate && python3 ~/Projects/workflow-ai/install.py'
```

```bash
source ~/.zshrc
```

## Dùng

### Dự án mới
```bash
workflow-ai --target ~/projects/new-project
```

### Dự án có system design doc
```bash
workflow-ai --target ~/projects/my-app --docs ~/docs/system-design.md
```

### Dự án đang chạy (detect từ codebase)
```bash
workflow-ai --target ~/projects/existing-app
```

### Update sau khi stack thay đổi
```bash
workflow-ai --target ~/projects/my-app --update
```

### Xem sẽ làm gì trước khi chạy
```bash
workflow-ai --target ~/projects/my-app --dry-run
```

## Sau khi install

Install tạo 3 thứ trong dự án của bạn:

```
your-project/
├── CLAUDE.md              ← phân công Claude Code vs Antigravity theo stack
├── .env.example           ← template API key
└── docs/
    └── modules/
        └── README.md      ← hướng dẫn viết design.md
```

### Quy trình làm việc

```
[ ] 1. claude (terminal) → "Thiết kế module [tên]. Ghi docs/modules/[tên]/design.md"
[ ] 2. Antigravity        → "Đọc design.md và implement toàn bộ module"
[ ] 3. claude (terminal) → "Review security + logic trong src/[tên]/"
[ ] 4. Antigravity        → sửa theo feedback
[ ] 5. claude (terminal) → git commit + push
```

## Tối ưu chi phí Claude Code

```bash
# 80% task hàng ngày — Sonnet đủ dùng
claude --model claude-sonnet-4-6

# Thiết kế kiến trúc, security review — dùng Opus
claude --model claude-opus-4-6
```

## Setup API key

```bash
cp ~/projects/my-app/.env.example ~/projects/my-app/.env
# Điền ANTHROPIC_API_KEY vào .env
```

Dùng proxy:
```env
ANTHROPIC_BASE_URL=https://your-proxy.example.com
```

## Security

- Analysis chạy **100% local** — không gửi source code ra ngoài
- Chỉ gửi **ProjectProfile JSON** (~500 tokens) lên Claude API để sinh CLAUDE.md
- Không cần Gemini API riêng — Antigravity đã có Gemini built-in

## Stack được detect

| Language | Frameworks | Database | Infra |
|----------|-----------|----------|-------|
| TypeScript/JavaScript | React, Next.js, Vue, Angular, Svelte | PostgreSQL, MySQL, MongoDB, Redis | Docker, GitHub Actions |
| Python | FastAPI, Flask, Django, PyTorch | SQLAlchemy, Prisma | GitLab CI, Kubernetes |
| Ruby | Rails, Sinatra | ActiveRecord | Helm, Terraform |
| Go | Gin, Echo, Fiber, Chi | GORM | |
| Java/Kotlin | Spring Boot | | |
