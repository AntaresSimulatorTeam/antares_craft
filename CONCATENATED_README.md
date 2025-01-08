# antares_craft
[![github ci](https://github.com/AntaresSimulatorTeam/antares_craft/actions/workflows/ci.yml/badge.svg)](https://github.com/AntaresSimulatorTeam/antares_craft/actions/workflows/ci.yml)

## about

Antares Craft python library is currently under construction. When completed it will allow to create, update and read 
antares studies.

This project only supports antares studies with a version v8.8 or higher.



# Introduction

With antares-craft you can interact with studies using AntaresWeb API or in local mode.
To interact with AntaresWeb you need a token.

## AntaresWeb

### How to create a study

```
api_config = APIconf(api_host=antares_web.url, token=your_token, verify=False)
study = create_study_api("antares-craft-test", "880", api_config)
```

### How to point to an existing study

Not handled yet

## LOCAL

### How to create a study

    study = create_study_local("your_name", 880, {"local_path": "your_path", "study_name": "your_name"})

### How to point to an existing study

`study = read_study_local(study_path)`

## Apart from that every operation is the same no matter the environment you're targetting.

### How to create an area with given properties:

```
area_properties = AreaProperties()
area_properties.energy_cost_unsupplied = 10  
study.create_area("fr", area_properties)
```

### How to access study areas

```
area_list = study.read_areas()
```

### install dev requirements

Install dev requirements with `pip install -r requirements-dev.txt`

### linting and formatting

To reformat your code, use this command line: `ruff check src/ tests/ --fix && ruff format src/ tests/`

### typechecking

To typecheck your code, use this command line: `mypy`

### integration testing

To launch integration tests you'll need an AntaresWebDesktop instance on your local env (at least the v.2.17.3, 
**currently running in 2.17.5**).  
To install it, download it from the last [Antares Web release](https://github.com/AntaresSimulatorTeam/AntaREST/releases) 
(inside the assets list).  
Then, unzip it at the root of this repository and rename the folder `AntaresWebDesktop`.  
*NB*: The expected folder structure is the following: `antares_craft/AntaresWebDesktop/config.yaml`

### tox
To use [tox](https://tox.wiki/) to run unit tests in multiple python versions at the same time as linting and formatting
with ruff and typing with mypy:  
1) As the dev requirements include [uv](https://docs.astral.sh/uv/) and `tox-uv` there is no need to install python 
versions, `uv` will do this for you.  
2) Use `tox -p` to run the environments in parallel to save time, this will create virtual environment with the 
necessary python versions the first time you run tox.

### mkdocs
Smallest beginning of `mkdocs` included more as proof of concept than anything, theme and logo copied from [Antares 
Simulator](https://github.com/AntaresSimulatorTeam/Antares_Simulator).  
1) To preview the docs on your local machine run `mkdocs serve`.  
2) To build the static site for publishing for example on [Read the Docs](https://readthedocs.io) use `mkdocs build`.
3) To flesh out the documentation see [mkdoc guides](https://www.mkdocs.org/user-guide/).


v0.1.5 (2025-01-08)
-------------------

- Concatenate .md files for single Readme at pypi.org 

v0.1.4 (2025-01-07)
-------------------

- Allow read_areas method to read area parameters and ui
- Add output functionalities (get_matrix, aggregate_values)

v0.1.3 (2024-12-19)
-------------------

- Add project requirements inside `pyproject.toml` to use the package as is
- Add a subfolder "craft" inside src to rename the package `antares.craft` for users
- Add `py.typed` file to avoid mypy issues in projects importing the package

v0.1.2 (2024-12-18)
-------------------

### Features

- Read a study
- Read thermal, renewable clusters and short term storages properties
- Read load matrix
- Read link matrices
- Allow variant creation
- Allow to run simulation

v0.1.1 (2024-11-26)
-------------------

* update token and bump version to publish on PyPi.

v0.1.0 (2024-11-26)
-------------------

* First release of the project.

