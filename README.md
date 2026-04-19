# workflow-ai

Cài AI workflow (Claude Code + Gemini) vào bất kỳ dự án nào — tự động detect stack, sinh CLAUDE.md tương thích, không conflict với config hiện có.

## Cài đặt (một lần)

```bash
git clone https://github.com/your-username/workflow-ai ~/workflow-ai
cd ~/workflow-ai
pip install -r requirements.txt
```

Set API keys trong `~/.zshrc`:
```bash
export ANTHROPIC_API_KEY=xxx
export GEMINI_API_KEY=xxx
```

## Dùng

### Dự án mới
```bash
python ~/workflow-ai/install.py --target ~/projects/new-project
```

### Dự án có system design doc
```bash
python ~/workflow-ai/install.py --target ~/projects/my-app --docs ~/docs/system-design.md
```

### Dự án đang chạy (detect từ codebase)
```bash
python ~/workflow-ai/install.py --target ~/projects/existing-app
```

### Update sau khi stack thay đổi
```bash
python ~/workflow-ai/install.py --target ~/projects/my-app --update
```

### Xem sẽ làm gì trước khi chạy
```bash
python ~/workflow-ai/install.py --target ~/projects/my-app --dry-run
```

### Chỉ xem ProjectProfile (không ghi file)
```bash
python ~/workflow-ai/install.py --target ~/projects/my-app --profile-only
```

## Cấu trúc

```
workflow-ai/
├── install.py                  # Entry point
├── analyzers/
│   ├── detect_stack.py         # Detect tech stack (local, không gửi code ra ngoài)
│   ├── detect_conventions.py   # Detect formatter, linter, naming conventions
│   └── detect_conflicts.py     # Kiểm tra conflict với config hiện có
├── generators/
│   └── generate_claude_md.py   # Sinh CLAUDE.md qua Claude API (fallback: template tĩnh)
├── scripts/
│   └── gemini.py               # Script gọi Gemini API (được cài vào dự án)
└── templates/
    └── CLAUDE.md.base          # Template tĩnh fallback
```

## Security

- Analysis chạy **100% local** — không gửi source code ra ngoài
- Chỉ gửi **ProjectProfile JSON** (~500 tokens, không chứa code) lên Claude API để sinh CLAUDE.md
- API keys chỉ đọc từ environment variables, không bao giờ ghi vào file

## Stack được detect

| Language | Frameworks | DB | Infra |
|----------|-----------|-----|-------|
| TypeScript/JavaScript | React, Next.js, Vue, Angular, Svelte | PostgreSQL, MySQL, MongoDB, Redis | Docker, GitHub Actions, Terraform |
| Python | FastAPI, Flask, Django | SQLAlchemy, Prisma | GitLab CI, Jenkins |
| Ruby | Rails, Sinatra | ActiveRecord | Kubernetes, Helm |
| Go | Gin, Echo, Fiber, Chi | GORM | |
| Java/Kotlin | Spring Boot | | |
