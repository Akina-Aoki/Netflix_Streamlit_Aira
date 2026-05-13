# Netflix Streamlit Project

## 📦 Project Structure

```
NETFLIX_STREAMLIT/
│
├── src/
│   └── netflix/
│       └── __init__.py
│
├── pyproject.toml
├── README.md
├── .python-version
├── .gitignore
```

---

## 🚀 Setup

### 1. Initialize project

```bash
uv init --package netflix --python 3.13
```

---

### 2. Move package into `src` layout

```bash
mkdir src
mv netflix src/
```

---
## How to run locally

```bash
git clone <repository-url>
cd Netflix_Streamlit_Aira
uv sync
uv run streamlit run src/netflix/app.py
```

If you are not using `uv`, install the project with pip and run Streamlit directly:

```bash
python -m pip install -e .
streamlit run src/netflix/app.py
```