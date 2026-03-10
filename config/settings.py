"""
⚙️ Settings & Constants
"""

# ── File filtering ──────────────────────────────────────────────
INCLUDE_EXTENSIONS = {
    # Code
    '.py', '.js', '.ts', '.jsx', '.tsx',
    '.java', '.cpp', '.c', '.go', '.rs',
    '.rb', '.php', '.cs', '.swift', '.kt',
    # Config & infra
    '.yml', '.yaml', '.toml', '.ini', '.cfg',
    '.env', '.env.example', '.sh', '.bash',
    '.xml', '.json', '.jsonc',
    # Docs
    '.md', '.txt', '.rst',
    # Web
    '.html', '.css', '.scss',
    # SQL
    '.sql',
}

# Exact filenames with no extension
INCLUDE_EXACT_NAMES = {
    'Dockerfile', 'Makefile', 'Procfile',
    '.gitignore', '.dockerignore', '.env',
    'docker-compose', 'nginx.conf',
}

# Always skip these folders
EXCLUDE_FOLDERS = {
    'node_modules', '.git', '__pycache__',
    'venv', 'env', '.venv',
    '.next', '.nuxt',
    'coverage', '.pytest_cache',
    '.mypy_cache', '.ruff_cache',
}

# Skip only if they contain compiled/minified artifacts
SOFT_EXCLUDE_FOLDERS = {
    'dist', 'build',
}

# ── Chunking ────────────────────────────────────────────────────
CHUNK_SIZE        = 1000
CHUNK_OVERLAP     = 150
MAX_FILE_SIZE     = 200_000   # bytes — skip files larger than this

# ── Embeddings ──────────────────────────────────────────────────
EMBEDDING_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DEVICE  = "cpu"

# ── LLM ─────────────────────────────────────────────────────────
LLM_MODEL         = "gemini-2.5-flash"
LLM_TEMPERATURE   = 0.3
RETRIEVER_K       = 5          # how many chunks to retrieve per query