import json
import os
import re
import shutil
import subprocess
import warnings
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import h5py
import jinja2 as j2
from tqdm import tqdm

from . import utils
from ._version import __version__
from .functions import check_particles_in_domain


class SimulationError(Exception):
    """Custom error class for Simulation."""

    pass


class Attributes(dict):
    """Light dict wrapper to serve as a container of attributes."""

    def save(self, filename):
        with h5py.File(filename, "a") as f:
            print(f"Saving attributes to {filename}")
            f.attrs.update({k: json.dumps(v) for k, v in self.items()})

    def load(self, filename):
        with h5py.File(filename, "r") as f:
            return {k: json.loads(v) for k, v in f.attrs.items()}


class Simulation(list):
    def __init__(self, name="pylion"):
        super().__init__()

        # keep track of uids for list function overrides
        self._uids = []

        # slugify 'name' to use for filename
        name = name.replace(" ", "_").lower()

        self.attrs = Attributes()
        self.attrs["gpu"] = None
        self.attrs["executable"] = "lmp"
        self.attrs["thermo"] = 10000
        self.attrs["thermo_styles"] = ["step", "cpu"]
        self.attrs["timestep"] = 1e-6
        self.attrs["nsteps"] = None  # will be set by evolve
        self.attrs["domain"] = [1e-3, 1e-3, 1e-3]  # length, width, height
        self.attrs["name"] = name
        self.attrs["neighbour"] = {"skin": 1, "list": "nsq"}
        self.attrs["coulombcutoff"] = 10
        self.attrs["template"] = "simulation.j2"
        self.attrs["version"] = __version__
        self.attrs["rigid"] = {"exists": False}
        self.attrs["output_files"] = []
        self.attrs["progressbar"] = True

        directory = (Path.cwd() / name).resolve()
        directory.mkdir(exist_ok=True, parents=True)
        self.attrs["directory"] = os.fspath(directory)

        # # initalise the h5 file
        # with h5py.File(self.attrs['name'] + '.h5', 'w') as f:
        #     pass

    def __contains__(self, this):
        """Check if an item exists in the simulation using its ``uid``."""

        try:
            return this["uid"] in self._uids
        except KeyError:
            print("Item does not have a 'uid' key.")

    def append(self, this):
        """Appends the items and checks their attributes.
        Their ``uid`` is logged if they have one.
        """

        # only allow for dicts in the list
        if not isinstance(this, dict):
            raise SimulationError("Only 'dicts' are allowed in Simulation().")

        self._uids.append(this.get("uid"))

        # ions will always be included first so to sort you have
        # to give 1-count 'priority' keys to the rest
        if this.get("type") == "ions":
            this["priority"] = 0
            if this.get("rigid"):
                self.attrs["rigid"]["exists"] = True
                self.attrs["rigid"].setdefault("groups", []).append(this["uid"])

        timestep = this.get("timestep", 1e12)
        if timestep < self.attrs["timestep"]:
            print(f"Reducing timestep to {timestep} sec")
            self.attrs["timestep"] = timestep

        nsteps = this.get("nsteps")
        if nsteps:
            if self.attrs["nsteps"] is None:
                self.attrs["nsteps"] = nsteps
                print(f"Setting number of steps to {nsteps}")
            else:
                raise SimulationError(
                    "Number of steps already set. Cannot set it again."
                )

        super().append(this)

    def extend(self, iterable):
        """Calls ``append`` on an iterable."""

        for item in iterable:
            self.append(item)

    def index(self, this):
        """Returns the index of an item using its ``uid``."""

        return self._uids.index(this["uid"])

    def remove(self, this):
        """Will not remove anything from the simulation but rather from lammps.
        It adds an ``unfix`` command when it's called.
        Use del if you really want to delete something or better yet don't
        add it to the simulation in the first place.
        """

        code = ["\n# Deleting a fix", f"unfix {this['uid']}\n"]
        self.append({"code": code, "type": "command"})

    def sort(self):
        """Sort with 'priority' keys if found otherwise do nothing."""

        try:
            super().sort(key=lambda item: item["priority"])
        except KeyError:
            pass
            # Not all elements have 'priority' keys. Cannot sort list

    def _writeinputfile(self):
        self.sort()  # if 'priority' keys exist

        odict = defaultdict(list)
        # deal the items in odict
        for item in self:
            if item.get("type") == "ions":
                odict["species"].append(item)
            else:
                odict["simulation"].append(item)

        # do a couple of checks
        # check for uids clashing
        uids = [uid for uid in self._uids if uid is not None]
        if len(uids) > len(set(uids)):
            raise SimulationError(
                "There are identical 'uids'. Although this is allowed in some "
                " cases, 'lammps' is probably not going to like it."
            )

        # make sure species will behave
        maxuid = max(odict["species"], key=lambda item: item["uid"])["uid"]
        if maxuid > len(odict["species"]):
            raise SimulationError(
                f"Max 'uid' of species={maxuid} is larger than the number "
                f"of species={len(odict['species'])}. "
                "Calling '@lammps.ions' decorated functions increments the "
                "'uid' count unless it is for the same ion group."
            )

        # check if ions are within the domain
        for ion in odict["species"]:
            if not check_particles_in_domain(ion["positions"], self.attrs["domain"]):
                raise SimulationError(
                    f"Ions are of species={ion['uid']} are placed outside the simulation domain."
                )

        # load jinja2 template
        env = j2.Environment(
            loader=j2.PackageLoader("pylion", "templates"), trim_blocks=True
        )
        template = env.get_template(self.attrs["template"])
        rendered = template.render({**self.attrs, **odict})

        filepath = Path(self.attrs["directory"], self.attrs["name"] + ".lammps")
        with open(filepath, "w") as f:
            f.write(rendered)

        # get a few more attrs now that the lammps file is written
        # - simulation time
        self.attrs["time"] = datetime.now().isoformat()

        # - names of the output files
        fixes = filter(lambda item: item.get("type") == "fix", odict["simulation"])
        self.attrs["output_files"] = [
            line.split()[5]
            for fix in fixes
            for line in fix["code"]
            if line.startswith("dump")
        ]

    def execute(self):
        """Write lammps input file and run the simulation."""

        if getattr(self, "_hasexecuted", False):
            raise SimulationError(
                "Simulation has executed already. Do not run it again."
            )

        executable = shutil.which(self.attrs["executable"])
        if not executable:
            raise SimulationError(
                f"Could not find executable '{self.attrs['executable']}'. "
                "Make sure it is installed and in your PATH."
            )

        self._writeinputfile()

        args = [
            executable,
            "-log",
            self.attrs["name"] + ".lmp.log",
            "-in",
            self.attrs["name"] + ".lammps",
        ]
        cwd = self.attrs["directory"]

        if self.attrs["progressbar"]:
            stdout = self._run_with_progressbar(
                args, cwd, total_steps=self.attrs["nsteps"]
            )
        else:
            stdout = self._run(args, cwd)

        self._process_stdout(stdout)
        self._hasexecuted = True

        # save everything at the end
        # so if the simulation fails the h5file is not even created
        self._save_attributes_and_files()

    def _run(self, args, cwd):
        p = subprocess.run(
            args,
            cwd=cwd,
            stderr=subprocess.STDOUT,  # redirect stderr to stdout
            stdout=subprocess.PIPE,  # capture the output
            text=True,
            check=False,
        )
        return p.stdout

    def _run_with_progressbar(self, args, cwd, total_steps=None):
        """
        Run a command with a live tqdm bar driven by the thermo 'Step' column.
        If total_steps is None, the bar is indeterminate and advances by delta in Step.
        Returns the subprocess.Popen object.
        """

        # Match lines where the first token is an integer step count (LAMMPS thermo rows)
        step_line = re.compile(r"^\s*(\d+)\s+\S")

        p = subprocess.Popen(
            args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        bar = tqdm(
            total=total_steps,
            desc="LAMMPS",
            unit="step" if total_steps else "iter",
            leave=True,
        )
        last_step = 0

        lines = []
        try:
            for raw in p.stdout:
                lines.append(raw)
                m = step_line.match(raw)
                if not m:
                    continue
                step = int(m.group(1))
                if total_steps is None:
                    inc = max(0, step - last_step)
                    if inc:
                        bar.update(inc)
                else:
                    if step > bar.n:
                        bar.n = step
                        bar.refresh()
                last_step = step
        finally:
            p.wait()
            stdout = "".join(lines)
            if total_steps and bar.n < total_steps:
                bar.n = total_steps
                bar.refresh()
            bar.close()

        return stdout

    def _save_attributes_and_files(self):
        self.attrs["output_files"].extend(
            [
                self.attrs["name"] + ".lammps",
                self.attrs["name"] + ".lmp.log",
            ]
        )

        # initalise the h5 file
        h5file = Path(self.attrs["directory"], self.attrs["name"] + ".h5")
        with h5py.File(h5file, "w") as f:  # noqa: F841
            pass

        # save attrs and scripts to h5 file
        self.attrs.save(h5file)
        utils._savecallersource(h5file)

        for filename in self.attrs["output_files"]:
            filepath = str(Path(self.attrs["directory"]) / filename)
            utils._savescriptsource(h5file, filepath)

    def _process_stdout(self, stdout):
        if "ERROR:" in stdout:
            for line in stdout.splitlines():
                if "ERROR:" in line:
                    raise SimulationError(line.strip())

        if "WARNING:" in stdout:
            for line in stdout.splitlines():
                if "WARNING:" in line:
                    warnings.warn(line.strip(), RuntimeWarning)

        atoms = 0
        for line in stdout.splitlines():
            line = line.rstrip("\r\n")
            if line == "Created 1 atoms":
                atoms += 1
                continue
            elif line == "Created 0 atoms":
                raise SimulationError(
                    "lammps created 0 atoms - perhaps you placed ions "
                    "with positions outside the simulation domain?"
                )

            if atoms:
                print(f"Created {atoms} atoms.")
                atoms = False
                continue
