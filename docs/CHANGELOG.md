v0.2.1 (2025-03-13)
-------------------

### Compatiblity
This version is only compatible with AntaresWeb v2.19.1 and higher.
Consequently, the v0.2.0 is only compatible with AntaresWeb v2.19.0 

It also requires a solver in v8.8.14 or higher

### Breaking changes
* **areas**: new user class for AreaUI. It does no longer support multiple layers [96](https://github.com/AntaresSimulatorTeam/antares_craft/pull/96)
* **matrices**: rename matrices update methods. The prefixes `create` or `update` changed to `set` for clarity’s sake [125](https://github.com/AntaresSimulatorTeam/antares_craft/pull/125)
* **user** make `read` methods inside Study or Area private. You shall no longer need to use them [126](https://github.com/AntaresSimulatorTeam/antares_craft/pull/126)

### Features
* **user**: make user classes frozen to avoid careless modifications [99](https://github.com/AntaresSimulatorTeam/antares_craft/pull/99)
* **links**: create `modify_multiple_links` method by [98](https://github.com/AntaresSimulatorTeam/antares_craft/pull/98)
* **local**: handle st storage methods [101](https://github.com/AntaresSimulatorTeam/antares_craft/pull/101)
* **local**: handle thermal methods [102](https://github.com/AntaresSimulatorTeam/antares_craft/pull/102)
* **local**: handle renewable methods [103](https://github.com/AntaresSimulatorTeam/antares_craft/pull/103)
* **links**: use `read_links` inside `read_study_api`[105](https://github.com/AntaresSimulatorTeam/antares_craft/pull/105)
* **constraints**: introduce `update_multiple_constraints` method [108](https://github.com/AntaresSimulatorTeam/antares_craft/pull/108)
* **local**: implement `read_constraints` method [110](https://github.com/AntaresSimulatorTeam/antares_craft/pull/110)
* **local**: implement some `binding_constraints` [111](https://github.com/AntaresSimulatorTeam/antares_craft/pull/111)
* **local**: implement `thermal_ts_generation` [112](https://github.com/AntaresSimulatorTeam/antares_craft/pull/112)
* **local**: return default simulator matrices when they are empty [113](https://github.com/AntaresSimulatorTeam/antares_craft/pull/113)
* **areas**: introduce `update_multiple_areas_properties` method [104](https://github.com/AntaresSimulatorTeam/antares_craft/pull/104)
* **local**: handle local launcher [116](https://github.com/AntaresSimulatorTeam/antares_craft/pull/116)
* **local**: handle delete and read output methods [117](https://github.com/AntaresSimulatorTeam/antares_craft/pull/117)
* **local**: handle clusters deletion methods [118](https://github.com/AntaresSimulatorTeam/antares_craft/pull/118)
* **local**: handle link update ui and deletion [120](https://github.com/AntaresSimulatorTeam/antares_craft/pull/120)
* **local**: implement delete constraint method [123](https://github.com/AntaresSimulatorTeam/antares_craft/pull/123)
* **api**: handle AntaresWeb version 2.19.1 [92](https://github.com/AntaresSimulatorTeam/antares_craft/pull/92)
* **thermals**: introduce `update_multiple_thermal_clusters` method [124](https://github.com/AntaresSimulatorTeam/antares_craft/pull/124)


### Fixes
* **user**: `read_xxx` methods modify objects instead of copying them [100](https://github.com/AntaresSimulatorTeam/antares_craft/pull/100)
* **user**: put new dependencies inside the `pyproject.toml` file [129](https://github.com/AntaresSimulatorTeam/antares_craft/pull/129)
* **local**: `write_timeseries` method improvement [97](https://github.com/AntaresSimulatorTeam/antares_craft/pull/97)
* **local**: actually modify ini files inside update methods [119](https://github.com/AntaresSimulatorTeam/antares_craft/pull/119)


### Miscellaneous
* **doc**: initialize doc deployment to readthedoc [121](https://github.com/AntaresSimulatorTeam/antares_craft/pull/121)
* **chore**: cleaning duplicated code [106](https://github.com/AntaresSimulatorTeam/antares_craft/pull/106)
* **chore**: better handling of filtering values [114](https://github.com/AntaresSimulatorTeam/antares_craft/pull/114)
* **chore**: remove pydantic related field from user classes [115](https://github.com/AntaresSimulatorTeam/antares_craft/pull/115)
* **chore**: put user related classes inside `__init__.py` [127](https://github.com/AntaresSimulatorTeam/antares_craft/pull/127)


**Full Changelog**: https://github.com/AntaresSimulatorTeam/antares_craft/compare/v0.2.0...v0.2.1

v0.2.0 (2025-02-20)
-------------------

### Compatiblity with AntaresWeb
This version is only compatible with AntaresWeb v2.19.0 and higher

### Breaking changes
- It is no longer possible to create a study while giving settings. The user will have to update them afterward.
- All user classes are now dataclasses and not Pydantic model.
- All user class (except for update) have no optional fields meaning it will be clearer for the users to see what they are really sending.
It will also silent typing issues inside user scripts
- New classes have been introduced for update. They are all optional which makes it also clear to understand which fields are updated.
- STStorage methods for updating matrices have been renamed `update_xxx` instead of `upload_xxx`.

Example of an old code:
```python
import AreaProperties

area_properties = AreaProperties()
area_properties.energy_cost_unsupplied = 10
area_properties.energy_cost_spilled = 4
area_fr = study.create_area("fr", area_properties)

new_properties = AreaProperties()
new_properties.energy_cost_unsupplied = 6
area_fr.update_properties(new_properties)
```

Example of a new code:
```python
import AreaProperties, AreaPropertiesUpdate

area_properties = AreaProperties(energy_cost_unsupplied=10, energy_cost_spilled=4)
area_fr = study.create_area("fr", area_properties)

new_properties = AreaPropertiesUpdate(energy_cost_unsupplied=6)
area_fr.update_properties(new_properties)
```

### Features
- API: add `import_study_api` method
- API: add update_thermal_matrices methods
- API: specify number of years to generate for thermal TS-generation

### Fixes
- LOCAL: `get_thermal_matrix` method checked the wrong path
- API: `read_renewables` method doesn't fail when settings are aggregated instead of clusters
- API: `read_settings` doesn't fail when horizon is a year
- API: disable proxy when using the Desktop version to avoid any issue

### Miscellaneous
- enforce strict type checking with mypy
- enforce override with mypy
- Moves all local and api related classes and methods outside the `model` package

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