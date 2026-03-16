# Building and Publishing to PyPI

## Prerequisites

1. Create an account on [PyPI](https://pypi.org)
2. Install build tools:
   ```bash
   pip install build twine
   ```

3. Create a `~/.pypirc` file with your PyPI credentials:
   ```ini
   [distutils]
   index-servers =
       pypi
       testpypi

   [pypi]
   repository: https://upload.pypi.org/legacy/
   username: __token__
   password: pypi-AgEIcHlwaS5vcmc...

   [testpypi]
   repository: https://test.pypi.org/legacy/
   username: __token__
   password: pypi-AgEIcHlwdGVzdC5vcmc...
   ```

## Build the Package

```bash
# From the project root directory
python -m build
```

This creates:
- `dist/chrysalis-0.1.0.tar.gz` (source distribution)
- `dist/chrysalis-0.1.0-py3-none-any.whl` (wheel)

## Test Upload to TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

## Upload to PyPI

```bash
python -m twine upload dist/*
```

## Verify Installation

```bash
# After a few minutes, install from PyPI
pip install chrysalis
```

## Before Publishing

- [ ] Update version number in `pyproject.toml`
- [ ] Update `CHANGELOG.md` with changes
- [ ] Ensure all tests pass: `pytest`
- [ ] Run type checking: `mypy chrysalis`
- [ ] Run code formatting: `black chrysalis`
- [ ] Check code quality: `pylint chrysalis` (optional)

## Package Structure

The project is configured for publication to PyPI with:
- `pyproject.toml`: Modern Python packaging configuration
- `MANIFEST.in`: Specifies additional files to include
- `chrysalis/py.typed`: Indicates the package supports type hints
- `README.md`: Used as the package description on PyPI
- `LICENSE`: CC0 1.0 Universal (Public Domain)
- `CHANGELOG.md`: Track version changes

## Notes

- The package has zero runtime dependencies
- Python 3.8+ is supported
- Full type hints are included (`py.typed` marker present)
- Licensed under CC0 1.0 (Public Domain)
