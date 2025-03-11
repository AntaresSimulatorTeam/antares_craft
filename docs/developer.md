# Developers documentation

This page aims at providing useful information for contributors of antares-craft library.

## Install dev requirements

Install dev requirements with `pip install -r requirements-dev.txt`

## Linting and formatting

To reformat your code, use this command line: `ruff check src/ tests/ --fix && ruff format src/ tests/`

## Typechecking

To typecheck your code, use this command line: `mypy`

## Integration testing

To launch integration tests you'll need an AntaresWebDesktop instance on your local env (since v0.2.0, use at least the
**v.2.19.0**)  
To install it, download it from the
last [Antares Web release](https://github.com/AntaresSimulatorTeam/AntaREST/releases)
(inside the assets list).  
Then, unzip it at the root of this repository and rename the folder `AntaresWebDesktop`.  
*NB*: The expected folder structure is the following: `antares_craft/AntaresWebDesktop/config.yaml`

### Tox

To use [tox](https://tox.wiki/) to run unit tests in multiple python versions at the same time as linting and formatting
with ruff and typing with mypy:

1) As the dev requirements include [uv](https://docs.astral.sh/uv/) and `tox-uv` there is no need to install python
   versions, `uv` will do this for you.
2) Use `tox -p` to run the environments in parallel to save time, this will create virtual environment with the
   necessary python versions the first time you run tox.

## Documentation

1) To preview the docs on your local machine run `mkdocs serve`.
2) To build the static site for publishing for example on [Read the Docs](https://readthedocs.io) use `mkdocs build`.
3) To flesh out the documentation see [mkdoc guides](https://www.mkdocs.org/user-guide/).
