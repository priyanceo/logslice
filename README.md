# logslice

> A terminal utility to filter, tail, and export structured logs from Docker containers with fuzzy search.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/yourname/logslice.git && cd logslice && pip install .
```

---

## Usage

```bash
# Tail logs from a running container with fuzzy search
logslice tail my-container --fuzzy "error"

# Filter logs by log level and time range
logslice filter my-container --level ERROR --since "2024-01-01T00:00:00"

# Export filtered logs to a file
logslice export my-container --level WARN --output logs.json
```

### Options

| Flag | Description |
|------|-------------|
| `--fuzzy` | Fuzzy search term to match against log messages |
| `--level` | Filter by log level (DEBUG, INFO, WARN, ERROR) |
| `--since` | Show logs after a given ISO timestamp |
| `--output` | Export results to a file (JSON or plain text) |
| `--follow` | Stream logs in real time (like `docker logs -f`) |

---

## Requirements

- Python 3.8+
- Docker daemon running locally
- `docker` Python SDK

---

## License

MIT © 2024 [yourname](https://github.com/yourname)