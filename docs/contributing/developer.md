# Developers documentation

This page aims at providing useful information for contributors of antares-craft library.

## Install dev requirements

Install dev requirements with `pip install -r requirements-dev.txt`

## Linting and formatting

To reformat your code, use this command line: `ruff check src/ tests/ --fix && ruff format src/ tests/`

## Typechecking

To typecheck your code, use this command line: `mypy`

## Integration testing

Integrations tests run inside the CI with AntaresWebDesktop instances and if you want to run them on your local env, 
you'll need the newest version to fetch inside this [private repo](https://github.com/AntaresSimulatorTeam/antares_desktop).
Then, unzip it at the root of this repository and rename the folder `AntaresWebDesktop`.  
*NB*: The expected folder structure is the following: `antares_craft/AntaresWebDesktop/config.yaml`

### Tox

To use [tox](https://tox.wiki/) to run unit tests in multiple python versions at the same time as linting and formatting
with ruff and typing with mypy:

1. As the dev requirements include [uv](https://docs.astral.sh/uv/) and `tox-uv` there is no need to install python
   versions, `uv` will do this for you.

2. Use `tox -p` to run the environments in parallel to save time, this will create virtual environment with the
   necessary python versions the first time you run tox.


