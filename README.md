# Nasa hackathon

## Installation
Install uv:
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install dependencies and the package itself
```
uv venv --python=3.12
uv pip install -e .
```

Copy `.env.template file`, name it `.env` and provide required environment variables.

Extracting structured data from articles
```
python scripts/manual_test.py
```

Running ui app:
```
 python -m nasa_hackathon.app
```