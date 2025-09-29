# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.1] - 2025-09-29

### Added

- **BREAKING**: Run simulations in a dedicated folder and refactor file saving (`55cfa24`)
  - The new behavior now is to create a sub folder with the same `name` of the simulation
  - All simulation input/output files are now placed in the subfolder rather than in the current working directory
  - This might break postprocessing workflows with hardcoded paths where to read simulation output, like `pl.readdump("positions.txt")`
- Check for LAMMPS executable presence before attempting to run (`899c35e`)
- New tests for README example (`57c87dc`)

### Changed

- **MAJOR**: Replaced p/wexpect usage with `subprocess.run()` for LAMMPS execution (`5000c08`, `f94cbe7`)
  - User interface (`simulation.execute()`) remains the same
  - It doesn't require installing OS-dependent package dependencies
  - This required rewriting functionalities requiring to inspect the simulation output
- Code formatting, import sorting, and import hygiene across the codebase (`a5bd468`, `4117860`, `17641f6`)

### Fixed

- Linting and test fixes (various small commits; see git log for details) (`a625ba9`)

## [0.6.0] - 2025-09-29

### Added

- **New test**: Added `tests/test_simpleexample.py`, corresponding to the example in the README
- **Modern Python packaging**: Introduced `pyproject.toml` for modern Python package configuration

### Changed

- **BREAKING: Build system modernization**:
  - Migrated from legacy `setup.py` to `pyproject.toml`
  - Updated to use `setuptools>=69` with proper build backend
- **BREAKING: Project structure reorganization**:
  - Moved all source code from `pylion/` to `src/pylion/` directory structure
  - This follows modern Python packaging best practices
- **Documentation improvements**: Updated `readme.md` with installation instructions for LAMMPS and the package
- **Updated .gitignore**: Based on Github's [Python .gitignore](https://github.com/github/gitignore/blob/main/Python.gitignore)
- **Code formatting**: Applied formatting using `ruff` across all project source files
- **Package metadata**: Improved project description, dependencies, and development requirements

### Removed

- **Legacy configuration files**:
  - Removed `setup.py` (replaced by `pyproject.toml`)
  - Removed `setup.cfg` (functionality moved to `pyproject.toml`)
- **Deprecated scripts**: Removed `run.py` which was no longer needed

## Previous Versions

For changes in versions prior to 0.6.0, please refer to the git history:

```bash
git log --oneline 099022e^
```

---

## Migration Guide

### Upgrading from 0.5.x to 0.6.0

This release includes breaking changes in the build system and project structure. Follow these steps to upgrade:

#### For Users

**Installation changes:**

```bash
# Old installation method (no longer supported)
python setup.py install

# New installation method
pip install .

# For development installation
pip install -e .
```

**Import statements remain unchanged:**

```python
import pylion
# All existing code continues to work
```

#### For Developers

**Project structure changes:**

- Source code moved from `pylion/` to `src/pylion/`
- Build configuration moved from `setup.py` to `pyproject.toml`

**Development setup:**

```bash
# Clone and setup development environment
git clone <repository-url>
cd pylion
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with development dependencies
pip install -e .[dev]

# Run tests
pytest

# Code formatting and linting
ruff format .
ruff check .
```

**Development tools now included:**

- `pytest` for testing
- `ruff` for formatting and linting
- `bump-my-version` for version management

---

## Development

### Testing

Run the test suite:

```bash
pytest
```

Run specific tests:

```bash
pytest tests/test_simpleexample.py
```

### Code Formatting

This project uses `ruff` for code formatting and linting:

```bash
# Format code
ruff format .

# Check for linting issues
ruff check .
```

### Version Management

Use bumpversion to update package versions:

```bash
# Bump patch version (0.5.3 -> 0.5.4)
bump-my-version patch

# Bump minor version (0.5.3 -> 0.6.0) 
bump-my-version minor

# Bump major version (0.5.3 -> 1.0.0)
bump-my-version major
```

---

## Links

- [Repository](https://github.com/carmelom/pylion)
- [Issues](https://github.com/carmelom/pylion/issues)
- [LAMMPS Documentation](https://docs.lammps.org/)
