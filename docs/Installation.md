# Installation

## From a GitHub Release (recommended)

Install the wheel directly from the Release page:

```bash
pip install "pkg-dynamic-field[all] @ https://github.com/fritill-team/pkg_dynamic_field/releases/download/pkg_dynamic_field-vX.Y.Z/pkg_dynamic_field-X.Y.Z-py3-none-any.whl"
```

Replace `X.Y.Z` with the version (e.g. `0.2.0`).

### In `requirements.txt`

```
pkg-dynamic-field[all] @ https://github.com/fritill-team/pkg_dynamic_field/releases/download/pkg_dynamic_field-v0.2.0/pkg_dynamic_field-0.2.0-py3-none-any.whl
```

## From a Git Tag

```bash
pip install "pkg-dynamic-field @ git+https://github.com/fritill-team/pkg_dynamic_field.git@pkg_dynamic_field-v0.2.0"
```

## Optional Dependencies

The package has optional extras for framework integrations:

| Extra | What it adds |
|-------|-------------|
| `sqlalchemy` | SQLAlchemy >= 2.0 |
| `fastapi` | FastAPI >= 0.100, Pydantic >= 2.0 |
| `all` | Both of the above |

```bash
# Core only (entities, validation, use cases)
pip install "pkg-dynamic-field @ git+https://..."

# With SQLAlchemy
pip install "pkg-dynamic-field[sqlalchemy] @ git+https://..."

# With FastAPI
pip install "pkg-dynamic-field[fastapi] @ git+https://..."

# Everything
pip install "pkg-dynamic-field[all] @ git+https://..."
```

## Local Development

```bash
git clone git@github.com:fritill-team/pkg_dynamic_field.git
cd pkg_dynamic_field
pip install -e ".[all]"
```
