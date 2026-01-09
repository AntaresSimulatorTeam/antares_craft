v0.9.1 (2026-01-09)
-------------------

### Bug fixes
* **local, thematic-trimming**: allow unknown fields [323](https://github.com/AntaresSimulatorTeam/antares_craft/pull/323)

v0.9.1 (2026-01-08)
-------------------

### Bug fixes
* **api, binding constraints**: allow offset to be null inside terms [320](https://github.com/AntaresSimulatorTeam/antares_craft/pull/320)

v0.9.0 (2026-01-05)
-------------------

### Features
* **build**: support Python 3.14 [315](https://github.com/AntaresSimulatorTeam/antares_craft/pull/315)

### Bug fixes
* **local, hydro**: write allocation values to ini file [317](https://github.com/AntaresSimulatorTeam/antares_craft/pull/317)

### Others
* **deps**: use numpy v2 instead of v1 [316](https://github.com/AntaresSimulatorTeam/antares_craft/pull/316)


v0.8.0 (2025-12-18)
-------------------

## Compatibility
* The method `study.delete_binding_constraint` has been replaced by `study.delete_binding_constraints` where you can now
give a list of constraints to delete at the same time [308](https://github.com/AntaresSimulatorTeam/antares_craft/pull/308)

### Features
* **local, area**: implement area deletion [196](https://github.com/AntaresSimulatorTeam/antares_craft/pull/196)

### Bug fixes

* **local, settings**: allow exportmps `both-optims` value [311](https://github.com/AntaresSimulatorTeam/antares_craft/pull/311)
* **local, settings**: allow reading with unwanted fields in the generaldata.ini [312](https://github.com/AntaresSimulatorTeam/antares_craft/pull/312)
* **local, renewable**: consider free groups before v9.3 are `other res 1` [313](https://github.com/AntaresSimulatorTeam/antares_craft/pull/313)
* **local, sc-builder**: clean the file when deleting objects [307](https://github.com/AntaresSimulatorTeam/antares_craft/pull/307)
* **local, sc-builder**: clean it when changing bc group [309](https://github.com/AntaresSimulatorTeam/antares_craft/pull/309)

### Perfs
* **local, output**: faster aggregation for clusters [305](https://github.com/AntaresSimulatorTeam/antares_craft/pull/305)

### Others
* **tests**: use 8.8.19 inside integration tests [310](https://github.com/AntaresSimulatorTeam/antares_craft/pull/310)


v0.7.0 (2025-12-12)
-------------------

## Compatibility
* This version is compatible with AntaresWeb v2.27.0. So does the 0.6.0.

### Bug fixes
* **local, thermal**: consider free groups before 9.3 are `other 1` [`292`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/292)
* **local, st-storage**: make groups case-insensitive [`293`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/293)
* **local, bc**: check matrices coherence at constraint creation [`298`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/298)
* **local, bc**: modify matrices when updating constraint `time_step` or `operator` [`301`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/301)

### Perfs
* **local, output**: use polars inside output aggregation [`302`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/302)
* **local, matrix**: use polars to read and write input matrices [`303`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/303)

### Others
* **ci**: use the right desktop name [`291`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/291)
* **doc**: more docstrings [`144`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/144)
* **tests**: use AntaresWeb 2.27 inside integration tests [`300`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/300)


v0.6.0 (2025-11-07)
-------------------

## Compatibility
* This version is compatible with AntaresWeb v2.26.0. The previous is not.
* The following methods concerning binding constraint terms were removed due to this [`279`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/279):
    * `add_terms`, `delete_term` and `update_term` were replaced by `set_terms` that takes the given terms and replace existing ones.

### Features
* **hydro**: support reading and editing allocation [`285`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/285)

### Bug fixes
* **dependencies**: fix issue with optional fields and pydantic 2.12 [`281`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/281)
* **clusters**: stop writing cluster names in lowercase inside API [`288`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/288)

### Perfs
* **binding-constraints**: clean code and improve perfs for local [`280`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/280)
* **api**: use new endpoint inside `read_study_api` [`271`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/271)

### Others
* **tests**: remove useless API UTs [`283`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/283)
* **tests**: add integration API test inside the CI [`282`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/282)
* **tests**: launch API integration test with new AWeb API[`284`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/284)
* **docs**: change package presentation message on pypi [`286`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/286)
* **tests**: add daily integration test with latest AntaresWeb code [`287`](https://github.com/AntaresSimulatorTeam/antares_craft/pull/287)


v0.5.0 (2025-10-13)
-------------------

### Compatiblity
* This version fully supports the Simulator v9.3 [251](https://github.com/AntaresSimulatorTeam/antares_craft/pull/251), [277](https://github.com/AntaresSimulatorTeam/antares_craft/pull/277)
* This version is compatible with AntaresWeb v2.25.0. The previous is not.

### Bug fixes
* **ts-gen**: bump the `timeseries generation` package to fix an issue [263](https://github.com/AntaresSimulatorTeam/antares_craft/pull/263)
* **local**: allow clusters with numeric names [268](https://github.com/AntaresSimulatorTeam/antares_craft/pull/268)
* **api**: fix issue inside area properties reading and mass update [272](https://github.com/AntaresSimulatorTeam/antares_craft/pull/272)
* **output**: raise when links are given in the wrong order [274](https://github.com/AntaresSimulatorTeam/antares_craft/pull/274)
* **deps**: add pyarrow inside pyproject.toml [276](https://github.com/AntaresSimulatorTeam/antares_craft/pull/276)
* **scenario-builder**: only use `hydro final level` for v9.2+ studies [275](https://github.com/AntaresSimulatorTeam/antares_craft/pull/275)

### Perfs
* **aggregation**: use parquet instead of csv inside output aggregation [273](https://github.com/AntaresSimulatorTeam/antares_craft/pull/273)

### Others
* **deps**: relax dependencies requirements in pyproject.toml [266](https://github.com/AntaresSimulatorTeam/antares_craft/pull/266)
* **lint** fix linting [269](https://github.com/AntaresSimulatorTeam/antares_craft/pull/269)

## New Contributors
* @RobbieKiwi made their first contribution in [268](https://github.com/AntaresSimulatorTeam/antares_craft/pull/268)


v0.4.0 (2025-09-16)
-------------------

### Compatiblity
* This version fully supports the Simulator v9.2

### Features
* **thematic-trimming**: add `BC. MARG. COST` [244](https://github.com/AntaresSimulatorTeam/antares_craft/pull/244)
* **st-storages**: add attributes coherence check [245](https://github.com/AntaresSimulatorTeam/antares_craft/pull/245)
* **st-storages**: support additional constraints [246](https://github.com/AntaresSimulatorTeam/antares_craft/pull/246)
* **local**: support 9.2 launcher [249](https://github.com/AntaresSimulatorTeam/antares_craft/pull/249)

### Bug fixes
* **local**: support optional matrices [248](https://github.com/AntaresSimulatorTeam/antares_craft/pull/248)
* **local**: delete matrices when deleting an object [250](https://github.com/AntaresSimulatorTeam/antares_craft/pull/250)
* **api**: encode binding constraint term ID inside API call + use the right solver inside simulation [256](https://github.com/AntaresSimulatorTeam/antares_craft/pull/256)

### Others
* **output**: remove columns renaming inside local aggregation [243](https://github.com/AntaresSimulatorTeam/antares_craft/pull/243)
* **tests**: fix desktop tests [261](https://github.com/AntaresSimulatorTeam/antares_craft/pull/261)

### Perfs
* **xpansion**: remove one API call [247](https://github.com/AntaresSimulatorTeam/antares_craft/pull/247)
* **settings**: remove some API calls when updating study settings [253](https://github.com/AntaresSimulatorTeam/antares_craft/pull/253)

v0.3.0 (2025-07-24)
-------------------

### Features
* **xpansion**: implement matrices reading [231](https://github.com/AntaresSimulatorTeam/antares_craft/pull/231)
* **xpansion**: implement inputs editing  [232](https://github.com/AntaresSimulatorTeam/antares_craft/pull/232), [233](https://github.com/AntaresSimulatorTeam/antares_craft/pull/233), [234](https://github.com/AntaresSimulatorTeam/antares_craft/pull/234), [235](https://github.com/AntaresSimulatorTeam/antares_craft/pull/235), [236](https://github.com/AntaresSimulatorTeam/antares_craft/pull/236), [237](https://github.com/AntaresSimulatorTeam/antares_craft/pull/237), [238](https://github.com/AntaresSimulatorTeam/antares_craft/pull/238), [239](https://github.com/AntaresSimulatorTeam/antares_craft/pull/239), [240](https://github.com/AntaresSimulatorTeam/antares_craft/pull/240), [241](https://github.com/AntaresSimulatorTeam/antares_craft/pull/241)
* **xpansion**: implement outputs reading [206](https://github.com/AntaresSimulatorTeam/antares_craft/pull/206)

v0.2.10 (2025-07-16)
-------------------

### Features
* **xpansion**: implement inputs reading [227](https://github.com/AntaresSimulatorTeam/antares_craft/pull/227)

### Bug fixes
* **api**: change thematic-trimming `to_model` method [229](https://github.com/AntaresSimulatorTeam/antares_craft/pull/229)

v0.2.9 (2025-07-09)
-------------------

### Compatiblity
* This version is compatible with AntaresWeb v2.22.1. The previous is not.
* This version is compatible with Simulator v9.2 except for the short-term storage additional constraints.

### Features
* **api**: support AntaresWeb 2.22.1 [220](https://github.com/AntaresSimulatorTeam/antares_craft/pull/220)
* **version**:  handle Simulator v9.2 [179](https://github.com/AntaresSimulatorTeam/antares_craft/pull/179)

### Breaking changes
* **clusters**: forbid creation with matrices for thermal and renewable clusters [219](https://github.com/AntaresSimulatorTeam/antares_craft/pull/219)
  * Thermal and renewable clusters can no longer be instantiated with matrices (`DataFrame`)
  * Before:
    ```python
    thermal = area_fr.create_thermal_cluster("cluster_nuclear", series=matrix)
    ```
  * After:
    ```python
    thermal = area_fr.create_thermal_cluster("cluster_nuclear")
    thermal.set_series(matrix)
    ```

### Bug fixes
* **local**: remove useless thermal file [212](https://github.com/AntaresSimulatorTeam/antares_craft/pull/212)
* **local**: rename matrix C02Cost in CO2Cost [213](https://github.com/AntaresSimulatorTeam/antares_craft/pull/213)
* **local**: check constraint matrices size at the creation [214](https://github.com/AntaresSimulatorTeam/antares_craft/pull/214)
* **local**: use different thermal prepro matrices [215](https://github.com/AntaresSimulatorTeam/antares_craft/pull/215)
* **local**: perform whole data validation before writing data inside mass update methods [216](https://github.com/AntaresSimulatorTeam/antares_craft/pull/216)
* **api**: allow extra fields from API inside pydantic model [225](https://github.com/AntaresSimulatorTeam/antares_craft/pull/225)

### Miscellaneous
* **chore**: make exception messages a bit clearer [217](https://github.com/AntaresSimulatorTeam/antares_craft/pull/217)

v0.2.8 (2025-07-03)
-------------------

### Compatiblity
This version is compatible with AntaresWeb v2.22. The previous is not.

### Features
* **bcs**: forbid deletion if area/link/cluster is referenced inside a constraint term [195](https://github.com/AntaresSimulatorTeam/antares_craft/pull/195)
* **api** handle AntaresWeb version 2.22 [197](https://github.com/AntaresSimulatorTeam/antares_craft/pull/197)

### Miscellaneous
* **deps**: bump pydantic and move documentation requirements [198](https://github.com/AntaresSimulatorTeam/antares_craft/pull/198)
* **sonar**: fix little sonar issues [199](https://github.com/AntaresSimulatorTeam/antares_craft/pull/199)
* **output**: add aggregation enums inside `__all__` [200](https://github.com/AntaresSimulatorTeam/antares_craft/pull/200)
* **tests**: adapt code to custom desktop version [210](https://github.com/AntaresSimulatorTeam/antares_craft/pull/210)


v0.2.7 (2025-06-13)
-------------------

### Breaking changes
This version is only compatible with AntaresWeb v2.21.0 and higher due to [188](https://github.com/AntaresSimulatorTeam/antares_craft/pull/188)

We also changed the user output interaction due to [186](https://github.com/AntaresSimulatorTeam/antares_craft/pull/186)  
**Example:**  
Previously: 
```res = output.aggregate_areas_mc_all(query_file="details", frequency="hourly")```   
Now:
```res = output.aggregate_mc_all_areas(data_type="details", frequency="hourly")```


### Features
* **version** handle explicitely only `v8.8` studies [181](https://github.com/AntaresSimulatorTeam/antares_craft/pull/181)
* **local** implement local output service [185](https://github.com/AntaresSimulatorTeam/antares_craft/pull/185)
* **local** use `getpass.getuser()` when creating a local study [189](https://github.com/AntaresSimulatorTeam/antares_craft/pull/189)
* **local** add clusters reading inside `read_study_local` [191](https://github.com/AntaresSimulatorTeam/antares_craft/pull/191)

### Bug fixes
* **local**: allow study reading when there's no `output` folder [175](https://github.com/AntaresSimulatorTeam/antares_craft/pull/175)
* **local**: `read_areas` method relies on study path [176](https://github.com/AntaresSimulatorTeam/antares_craft/pull/176)
* **local**: support several values for `accuracy_on_correlation` field [177](https://github.com/AntaresSimulatorTeam/antares_craft/pull/177)
* **local**: allow area names inside hydro.ini file [178](https://github.com/AntaresSimulatorTeam/antares_craft/pull/178)
* **local**: fix several issues on cluster group parsing [192](https://github.com/AntaresSimulatorTeam/antares_craft/pull/192)
* **settings**: allow reading legacy values [193](https://github.com/AntaresSimulatorTeam/antares_craft/pull/193)

### Miscellaneous
* **build**: restore Windows CI [172](https://github.com/AntaresSimulatorTeam/antares_craft/pull/172)
* **build**: bump `ruff` and `mypy` [173](https://github.com/AntaresSimulatorTeam/antares_craft/pull/173)
* **local**: use `antares-study-version` package to simplify the code [180](https://github.com/AntaresSimulatorTeam/antares_craft/pull/180)
* **build**: bump tox [182](https://github.com/AntaresSimulatorTeam/antares_craft/pull/182)
* **chore**: use mypy inside tests [190](https://github.com/AntaresSimulatorTeam/antares_craft/pull/190)

v0.2.6 (2025-04-14)
-------------------

### Bug fixes
- **local**: support `None` value for include-export-mps [169](https://github.com/AntaresSimulatorTeam/antares_craft/pull/169)
- **local**: allow empty field for `accuracy-on-correlation` inside generaldata.ini [170](https://github.com/AntaresSimulatorTeam/antares_craft/pull/170)

v0.2.5 (2025-04-09)
-------------------

### Features
- **build**: support Python3.13 [164](https://github.com/AntaresSimulatorTeam/antares_craft/pull/164)

### Bug fixes
- **local**: avoid reading useless fields inside `read_settings` method [165](https://github.com/AntaresSimulatorTeam/antares_craft/pull/165)
- **local**: use the default value when reading an empty string [166](https://github.com/AntaresSimulatorTeam/antares_craft/pull/166)

v0.2.4 (2025-04-04)
-------------------

### Features
- **renewable**: add `update_renewable_clusters` method [149](https://github.com/AntaresSimulatorTeam/antares_craft/pull/149)
- **st-storage**: add `update_st_storages` method [150](https://github.com/AntaresSimulatorTeam/antares_craft/pull/150)
- **local** support playlist reading and writing [159](https://github.com/AntaresSimulatorTeam/antares_craft/pull/159)
- **local** support thematic trimming reading and writing [160](https://github.com/AntaresSimulatorTeam/antares_craft/pull/160)
- **scenariobuilder**: support scenario builder reading and writing [161](https://github.com/AntaresSimulatorTeam/antares_craft/pull/161), [162](https://github.com/AntaresSimulatorTeam/antares_craft/pull/162)

### Bug fixes
- **local** fix several issues inside properties update [152](https://github.com/AntaresSimulatorTeam/antares_craft/pull/152) [154](https://github.com/AntaresSimulatorTeam/antares_craft/pull/154), [155](https://github.com/AntaresSimulatorTeam/antares_craft/pull/155), [156](https://github.com/AntaresSimulatorTeam/antares_craft/pull/156), [157](https://github.com/AntaresSimulatorTeam/antares_craft/pull/157), [158](https://github.com/AntaresSimulatorTeam/antares_craft/pull/158)

### Miscellaneous
- **local** use `ini_reader` instead of `ConfigParser` to prepare future work [151](https://github.com/AntaresSimulatorTeam/antares_craft/pull/151)
- **local** avoid unecessary i/o operations inside area properties update [153](https://github.com/AntaresSimulatorTeam/antares_craft/pull/153)

v0.2.3 (2025-03-20)
-------------------

### Breaking changes
* We dropped the support of Python3.9. The supported versions of Python are the 3.10, 3.11 and 3.12
* Every `update_multiple_...` method has been renamed in `update_...s` [145](https://github.com/AntaresSimulatorTeam/antares_craft/pull/145)

### Features
* **hydro**: handle inflow-structure [137](https://github.com/AntaresSimulatorTeam/antares_craft/pull/137)
* **adequacy-patch**: change default values for 2 fields [141](https://github.com/AntaresSimulatorTeam/antares_craft/pull/141)

### Bug fixes
* **local**: use right st-storage matrices names [140](https://github.com/AntaresSimulatorTeam/antares_craft/pull/140)
* **local**: several bugs made antares simulation fail [147](https://github.com/AntaresSimulatorTeam/antares_craft/pull/147)

### Perfs
* **local**: avoid multiple i/o operations on the same files inside reading methods [134](https://github.com/AntaresSimulatorTeam/antares_craft/pull/134)
* **local**: speed-up `study.update_thermals` methods [142](https://github.com/AntaresSimulatorTeam/antares_craft/pull/142)

### Miscellaneous
* **chore** remove useless read methods [135](https://github.com/AntaresSimulatorTeam/antares_craft/pull/135)
* **chore** simplify read methods [136](https://github.com/AntaresSimulatorTeam/antares_craft/pull/136)
* **chore**: clean link code [143](https://github.com/AntaresSimulatorTeam/antares_craft/pull/143)


v0.2.2 (2025-03-17)
-------------------

### Bug fixes
- **api**: parse horizon inside study settings even when it's an integer

### Perfs
- **api**: use AntaresWeb table-mode endpoints to reduce amount of API calls inside reading methods

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