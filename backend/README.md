# AI Development Advisor Backend

An intelligence and advisory system that translates codebases into:
- Technical insights for engineers
- Strategic, decision-oriented guidance for non-technical leaders

## Quick Start

```bash
# Create and activate virtual environment with uv
uv venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
uv sync

# Install dev dependencies
uv sync --extra dev

# Run the Streamlit UI
uv run streamlit run src/advisor/ui/app.py
```

## Project Structure

```
backend/
├── src/advisor/
│   ├── config/      # Environment and settings
│   ├── database/    # Supabase client and models
│   ├── llm/         # OpenRouter orchestration
│   ├── github/      # Repository intake
│   ├── analysis/    # Intelligence generation
│   ├── reports/     # PDF generation
│   └── ui/          # Streamlit application
└── tests/           # Test suite
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Backend-only secret key
- `OPENROUTER_API_KEY_1` through `OPENROUTER_API_KEY_4` - API keys for LLM access

## Running Tests

```bash
uv run pytest tests/ -v --cov=src/advisor
```
