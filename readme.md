
# pylion

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A [LAMMPS](http://lammps.sandia.gov/) wrapper for molecular dynamics simulations of trapped ions.

## Installation

### Install LAMMPS (prebuilt / packages)

The official LAMMPS site provides several prebuilt installation options and platform-specific instructions: <https://docs.lammps.org/Install.html>

After installing a LAMMPS distribution, make sure the chosen executable (for example `lmp-serial`, `lmp`, or `lmp_mpi`) is on your PATH or note its location so you can point tools at it when running simulations.

### Install LAMMPS (from source)

If building from source, make sure the `rigid` and `misc` packages are enabled. For example:

```bash
make yes-rigid
make yes-misc
make serial

# other useful commands
make package   # list available packages and help
make ps        # list package status
```

This produces an `lmp-serial` (or similarly named) executable. On macOS you can also try `make mac`.

### Install pylion

Once LAMMPS is installed, install `pylion` from this repository using your Python packaging tool of choice (this project uses `pyproject.toml`):

Quick (editable / development) install:

```bash
python -m pip install -e .
```

Install the package for normal use:

```bash
python -m pip install .
```

On Windows the package declares a platform-specific runtime dependency (`wexpect`) in `pyproject.toml`; `pip` will select the correct dependency for your platform automatically. For development you may also want to install the test and linters manually:

```bash
python -m pip install pytest ruff sphinx sphinx-rtd-theme
```

`pylion` supports Python 3 only (the project metadata requires >=3.6). It has been tested with Python 3.8 and later, but newer Python versions should work as well.

To build the documentation, install Sphinx and the theme and then run `make html` from the `docs/` folder:

```bash
cd docs
make html
```

## Getting started

Once you're done with the installation you can start simulating clouds of ions within a few lines of code.
The following simulates the trajectories of 100 ions, trapped in a linear Paul trap.

```python
import pylion as pl

s = pl.Simulation('simple')

ions = {'mass': 40, 'charge': 1}
s.append(pl.createioncloud(ions, 1e-3, 100))

trap = {'radius': 3.75e-3, 'length': 2.75e-3, 'kappa': 0.244,
        'frequency': 3.85e6, 'voltage': 500, 'endcapvoltage': 15}
s.append(pl.linearpaultrap(trap))

s.append(pl.langevinbath(0, 1e-5))

s.append(pl.dump('positions.txt', variables=['x', 'y', 'z'], steps=10))

s.append(pl.evolve(1e4))
s.execute()
```

Look into the `examples` and `tests` folders for more ideas.

## Tests

Run the test suite with `pytest`. Many of the tests run full simulations and can take a while. To skip longer tests use the marker:

```bash
pytest -m "not slow"
```

There are a few fast unit-like tests (for internal implementation) which are convenient during development; the remaining tests exercise physics and are intentionally slower.

## Documentation

You will need `sphinx` and the `sphinx_rtd_theme` to build the documentation.
Both can be installed with:

```bash
pip install sphinx # or conda install sphinx
pip install sphinx_rtd_theme
```

If you're using Anaconda you probably have `sphinx` already.
Go to the `docs` folder and run `make html` or whatever format you prefer.

## Features

- Simulate multiple ion species in the same trap.

- Use multiple trap driving frequencies. See [Phys. Rev. A 94, 023609](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.94.023609) for details.

- Define rigid bodies from groups of ions to simulate mesoscopic charged objects.

If you find this software useful in your research please cite:

E. Bentine et al., [Computer Physics Communications, 253, 107187, (2020)](http://www.sciencedirect.com/science/article/pii/S0010465520300369)

D. Trypogeorgos et al., [Phys. Rev. A 94, 023609, (2016)](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.94.023609)

C. Foot et al., [IJMS Volume 430, July 2018, Pages 117-125](https://www.sciencedirect.com/science/article/pii/S1387380618300010)

## File structure

- `pylion`: contains all the main classes for managing the simulation.

- `examples`: example simulations showing different features of `(py)lion`.

- `tests`: a collection of scripts used to test the correct implementation of `(py)lion`.

- `docs`: documentation folder including user and developer manuals.

Free software: MIT license
