import pytest
import pylion as pl
from pathlib import Path


@pytest.fixture
def simulation_data():
    ions = {"mass": 40, "charge": 1}
    trap = {
        "radius": 3.75e-3,
        "length": 2.75e-3,
        "kappa": 0.244,
        "frequency": 3.85e6,
        "voltage": 500,
        "endcapvoltage": 15,
    }
    return trap, ions


@pytest.fixture
def cleanup():
    yield
    p = Path("test")
    for filename in p.iterdir():
        filename.unlink()
    p.rmdir()


def test_simpleexample(simulation_data):
    trap, ions = simulation_data
    s = pl.Simulation("test")

    s.append(pl.createioncloud(ions, 1e-3, 100))

    s.append(pl.linearpaultrap(trap))

    s.append(pl.langevinbath(0, 1e-5))

    s.append(pl.dump("positions.txt", variables=["x", "y", "z"], steps=10))

    s.append(pl.evolve(10))
    s.execute()

    assert Path("test/positions.txt").exists()
