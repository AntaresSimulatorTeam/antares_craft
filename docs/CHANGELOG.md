v0.1.8_RC2 (2025-01-22)
-------------------
- upload renewable thermal matrices method added
- bug fix clusters/{area}/list.ini file was missing
- bug fix for input/thermal/series/{area}/{cluster}/series.txt /data.txt and modulation.txt, wrong path 
  at cluster creation


v0.1.8_RC1 (2025-01-22)
-------------------

- bug fixes for missing files when creating area
- wrong properties corrected (spread-unsupplied-energy-cost and spread-spilled-energy-cost)

v0.1.7 (2025-01-08)
-------------------

- move doc generation from ci.yml to publish.yml

v0.1.6 (2025-01-08)
-------------------

- Fix concatenate CONCATENATED_README.md files for single Readme at pypi.org 

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