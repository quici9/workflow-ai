# workflow-ai

Cài AI workflow (Claude Code + Gemini) vào bất kỳ dự án nào — tự động detect stack, sinh CLAUDE.md tương thích, không conflict với config hiện có.

## Cài đặt (một lần)

```bash
git clone https://github.com/quici9/workflow-ai.git ~/workflow-ai
cd ~/workflow-ai

# Tạo và kích hoạt virtual env
python3 -m venv .venv
source .venv/bin/activate

# Cài dependencies
pip install -r requirements.txt
```

> **Lưu ý:** Mỗi lần mở terminal mới cần kích hoạt lại venv:
> ```bash
> source ~/Projects/workflow-ai/.venv/bin/activate
> ```
> Hoặc thêm alias vào `~/.zshrc` cho tiện:
> ```bash
> alias workflow-ai='source ~/Projects/workflow-ai/.venv/bin/activate && python3 ~/Projects/workflow-ai/install.py'
> ```

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

### Chỉ xem ProjectProfile (không ghi file)
```bash
workflow-ai --target ~/projects/my-app --profile-only
```

> Nếu chưa set alias, thay `workflow-ai` bằng:
> ```bash
> python3 ~/workflow-ai/install.py
> ```

## Setup API keys cho từng dự án

Sau khi chạy install, một file `.env.example` sẽ được tạo trong dự án. Copy và điền key:

```bash
cp ~/projects/my-app/.env.example ~/projects/my-app/.env
# Mở .env và điền giá trị thật
```

Nội dung `.env`:
```env
GEMINI_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_anthropic_key

# Tuỳ chọn: override model mặc định (gemini-2.5-pro)
# GEMINI_MODEL=gemini-2.5-flash
```

`scripts/gemini.py` tự load `.env` khi chạy — không cần `export` thủ công.
`.env` đã được tự động thêm vào `.gitignore`, không lo bị commit nhầm.

## Cấu trúc

```
workflow-ai/
├── install.py                  # Entry point
├── requirements.txt
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

Sau khi install, dự án của bạn chỉ nhận 2 file:
```
your-project/
├── .env.example       ← commit được
├── scripts/
│   └── gemini.py      ← script gọi Gemini
└── CLAUDE.md          ← config cho Claude Code
```

## Security

- Analysis chạy **100% local** — không gửi source code ra ngoài
- Chỉ gửi **ProjectProfile JSON** (~500 tokens, không chứa code) lên Claude API để sinh CLAUDE.md
- API keys đọc từ `.env` per-project, không hardcode, không ghi vào git

## Stack được detect

| Language | Frameworks | Database | Infra |
|----------|-----------|----------|-------|
| TypeScript/JavaScript | React, Next.js, Vue, Angular, Svelte, Astro | PostgreSQL, MySQL, MongoDB, Redis | Docker, GitHub Actions, Terraform |
| Python | FastAPI, Flask, Django, PyTorch, pandas | SQLAlchemy, Prisma, Drizzle | GitLab CI, Jenkins |
| Ruby | Rails, Sinatra | ActiveRecord | Kubernetes, Helm |
| Go | Gin, Echo, Fiber, Chi | GORM | |
| Java/Kotlin | Spring Boot | | |
