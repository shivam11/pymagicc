# Pymagicc

| [![Build Status](https://travis-ci.org/openclimatedata/pymagicc.svg?branch=master)](https://travis-ci.org/openclimatedata/pymagicc) | [![AppVeyor](https://img.shields.io/appveyor/ci/openclimatedata/pymagicc/master.svg)](https://ci.appveyor.com/project/openclimatedata/pymagicc) |
| :--- | :--- |
| [![Codecov](https://img.shields.io/codecov/c/github/openclimatedata/pymagicc.svg)](https://codecov.io/gh/openclimatedata/pymagicc) | [![Launch Binder](https://img.shields.io/badge/launch-binder-e66581.svg)](https://mybinder.org/v2/gh/openclimatedata/pymagicc/master?filepath=notebooks/Example.ipynb) |
| [![PyPI](https://img.shields.io/pypi/pyversions/pymagicc.svg)](https://pypi.org/project/pymagicc/) | [![PyPI](https://img.shields.io/pypi/v/pymagicc.svg)](https://pypi.org/project/pymagicc/) |
| [![status](https://joss.theoj.org/papers/85eb9a9401fe968073bb429ea361924e/status.svg)](https://joss.theoj.org/papers/85eb9a9401fe968073bb429ea361924e) | [![Zenodo](https://zenodo.org/badge/DOI/10.5281/zenodo.1111815.svg)](https://zenodo.org/record/1111815) |

Pymagicc is a Python wrapper around the reduced complexity climate model
[MAGICC6](http://magicc.org/). It wraps the CC-BY-NC-SA licensed
[MAGICC6 binary](http://www.magicc.org/download6). Pymagicc itself is AGPL licensed.

MAGICC (Model for the Assessment of Greenhouse Gas Induced Climate Change)
is widely used in the assessment of future emissions pathways in climate policy analyses,
e.g. in the Fifth Assessment Report of the
Intergovernmental Panel on Climate Change or to model the physical aspects of climate change in Integrated Assessment Models (IAMs).

Pymagicc makes the MAGICC model easily installable and usable from Python and allows for the easy modification of all MAGICC model parameters and emissions scenarios directly from Python.
In climate research it can, for example, be used in the analysis of mitigation scenarios, in Integrated Assessment Models, complex climate model emulation, and uncertainty analyses, as well as in climate science education and communication.

See [www.magicc.org](http://www.magicc.org/) and [Meinshausen et al. 2011](https://doi.org/10.5194/acp-11-1417-2011) for further information.

## Basic Usage

```python
import pymagicc
from pymagicc import scenarios
import matplotlib.pyplot as plt

for name, scen in scenarios.items():
    results, params = pymagicc.run(scen, return_config=True)
    temp = (results["SURFACE_TEMP"].GLOBAL.loc[1850:] -
            results["SURFACE_TEMP"].GLOBAL.loc[1850:1900].mean())
    temp.plot(label=name)
plt.legend()
plt.title("Global Mean Temperature Projection")
plt.ylabel(u"°C over pre-industrial (1850-1900 mean)")
# Run `plt.show()` to display the plot when running this example
# interactively or add `%matplotlib inline` on top when in a Jupyter Notebook.
```

![](scripts/example-plot.png)

For more example usage see this [Jupyter Notebook](https://github.com/openclimatedata/pymagicc/blob/master/notebooks/Example.ipynb).
Thanks to the [Binder project](https://mybinder.org) the [Notebook](https://mybinder.org/v2/gh/openclimatedata/pymagicc/master?filepath=notebooks/Example.ipynb) can be run and modified without installing anything locally. A small interactive [demo app](https://mybinder.org/v2/gh/openclimatedata/pymagicc/master?urlpath=apps/notebooks/Demo.ipynb) using Jupyter Notebook's [appmode extension](https://github.com/oschuett/appmode/)
is also available.

## Installation

    pip install pymagicc

On Linux and OS X the original compiled Windows binary available on
http://www.magicc.org/ and included in Pymagicc
can run using [Wine](https://www.winehq.org/).

On modern 64-bit systems one needs to use the 32-bit version of Wine

    sudo dpkg --add-architecture i386
    sudo apt-get install wine32

On 32-bit systems Debian/Ubuntu-based systems `wine` can be installed with

    sudo apt-get install wine

On OS X `wine` is available in the Homebrew package manager:

    brew install wine

It should also be available in other package managers, as well as directly from the [Wine project](https://wiki.winehq.org/Download).

Note that after the first install the first run of Pymagicc might be slow due
to setting up of the `wine` configuration and be accompanied by pop-ups or
debug output.

To run an example session using Jupyter Notebook and Python 3 you can run the
following commands to create a virtual environment `venv` and install an
editable version for local development:

    git clone https://github.com/openclimatedata/pymagicc.git

    cd pymagicc
    make venv
    ./venv/bin/pip install --editable .
    ./venv/bin/jupyter-notebook notebooks/Example.ipynb


## Development

For local development, install dependencies and an editable version of Pymagicc from a clone or download of the Pymagicc repository with

    make venv
    ./venv/bin/pip install --editable .

To run the tests run

    ./venv/bin/pytest tests --verbose

To skip tests which run MAGICC and take longer use

    ./venv/bin/pytest tests --skip-slow

To get a test coverage report, run

    ./venv/bin/pytest --cov

To unify coding style [black](https://github.com/ambv/black) is used.

To format the files in `pymagicc` and `tests` as well as `setup.py` run

```shell
make black
```

## More Usage Examples

### Use an included scenario

```python
from pymagicc import rcp26

rcp26["WORLD"].head()
```

### Read a MAGICC scenario file

```python
from pymagicc import read_scen_file

scenario = read_scen_file("PATHWAY.SCEN")
```

### Create a new scenario

Pymagicc uses Pandas DataFrames to represent scenarios. Dictionaries are
used for scenarios with multiple regions.

```python
import pandas as pd

scenario = pd.DataFrame({
    "FossilCO2": [8, 10, 9],
    "OtherCO2": [1.2, 1.1, 1.2],
    "CH4": [300, 250, 200]},
    index=[2010, 2020, 2030]
)

```

### Run MAGICC for a scenario

```python
output = pymagicc.run(scenario)

# Projected temperature adjusted to pre-industrial mean
temp = (output["SURFACE_TEMP"].GLOBAL -
        output["SURFACE_TEMP"].loc[1850:2100].GLOBAL.mean())
```

### Using a different MAGICC version

A custom version of MAGICC may be used with `pymagicc` using the
`MAGICC_EXECUTABLE_6` and `MAGICC_EXECUTABLE_7` environment variables for MAGICC6
 and MAGICC7 respectively. These environment variables should be set to the
 location of the magicc executable (either `magicc` for linux/mac or
 `magicc.exe` for Windows).
For example, a custom MAGICC7 folder located at `/tmp/magicc` can be used on
 under Linux by setting `MAGICC_EXECUTABLE_7` to `/tmp/magicc/run/magicc`.

Example usage in Bash:
```bash
MAGICC_EXECUTABLE_7=/tmp/magicc/run/magicc.exe python run_tests.py
```

Or in a script:
```bash
#!/bin/bash
export MAGICC_EXECUTABLE_7=tmp/magicc/run/magicc.exe
python run_tests.py
python generate_plots.py
```


## Contributing

Please report issues or discuss feature requests on Pymagicc's
[issue tracker](https://github.com/openclimatedata/pymagicc/issues).

You can also contact the `pymagicc` authors via email
<robert.gieseke@pik-potsdam.de>.


## License

The [compiled MAGICC binary](http://www.magicc.org/download6) by Tom Wigley,
Sarah Raper, and Malte Meinshausen included in this package is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License](https://creativecommons.org/licenses/by-nc-sa/3.0/).

The `pymagicc` wrapper is free software under the GNU Affero General Public
License v3, see [LICENSE](./LICENSE).

If you make any use of MAGICC, please cite:

> M. Meinshausen, S. C. B. Raper and T. M. L. Wigley (2011). "Emulating coupled
atmosphere-ocean and carbon cycle models with a simpler model, MAGICC6: Part I
"Model Description and Calibration." Atmospheric Chemistry and Physics 11: 1417-1456.
[doi:10.5194/acp-11-1417-2011](https://dx.doi.org/10.5194/acp-11-1417-2011)

See also the [MAGICC website](http://magicc.org/) and
[Wiki](http://wiki.magicc.org/index.php?title=Main_Page)
for further information.
