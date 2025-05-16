# Antares Craft

[![CI](https://github.com/AntaresSimulatorTeam/antares_craft/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AntaresSimulatorTeam/antares_craft/actions?query=workflow%3ACI)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=AntaresSimulatorTeam_antares_craft&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=AntaresSimulatorTeam_antares_craft)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=AntaresSimulatorTeam_antares_craft&metric=coverage)](https://sonarcloud.io/summary/new_code?id=AntaresSimulatorTeam_antares_craft)
[![License](https://img.shields.io/github/license/AntaresSimulatorTeam/antares_craft)](https://mozilla.org/MPL/2.0/)
[![PyPI Latest Release](https://img.shields.io/pypi/v/antares_craft.svg)](https://pypi.org/project/antares_craft/)

## What is it ?

Antares Craft is a python library to read and
edit [antares-simulator](https://github.com/AntaresSimulatorTeam/Antares_Simulator) studies, stored either on you local
filesystem or on an [antares-web](https://github.com/AntaresSimulatorTeam/AntaREST) server. It also allows you to
trigger
simulations and retrieve the corresponding result.

## Main features

- Read and edit antares-simulator studies programmatically
- Work seamlessly on filesystem or antares-web studies
- Support for variant studies on antares-web
- Launch simulations, be it on you computer or on antares-web server
- Retrieve and inspect simulation outputs
- Generate availability timeseries, be it on you computer or on antares-web server

## Installation

Antares Craft can simply be installed from PyPI repository, typically using pip:

```shell
pip install antares_craft
```

## Documentation

You may find further information and documentation on [readthedocs](https://antares-craft.readthedocs.io/en/stable/).

## Example

Below as an example, a code snippet where we create a small study with only one area where 100 MW of load are fed with a
cluster of 5 power plants of 30 MW each. We then run the simulation and print some results.

For more information and examples please refer to the documentation.

```python
conf = APIconf(api_host="https://antares-web.mydomain",
               token="my-token")

# create a study named "my-study" on the antares-web server
study = create_study_api(study_name="my-study", version="8.8", api_config=conf)

# create an area with 100 MW of load for every hour of the year, and 3000 euros/h for unsupplied energy cost
area = study.create_area(area_name="my-country", properties=AreaProperties(energy_cost_unsupplied=3000))
area.set_load(pd.DataFrame(data=100 * np.ones((8760, 1))))

# create a cluster with 5 nuclear units of 30 MW each, and a generation cost of 30 MW/h
cluster = area.create_thermal_cluster("nuclear",
                                      ThermalClusterProperties(unit_count=5,
                                                               nominal_capacity=30,
                                                               marginal_cost=10,
                                                               market_bid_cost=10,
                                                               group=ThermalClusterGroup.NUCLEAR))
cluster.set_series(pd.DataFrame(data=150 * np.ones((8760, 1))))

# launch a simulation on the server and wait for the result
job = study.run_antares_simulation()
study.wait_job_completion(job)
output = study.get_output(job.output_id)

# read some output data as a pandas dataframe:
res = output.aggregate_mc_all_areas(data_type="details", frequency="hourly")
print(res)
```

should print the following output, which shows that at every hour the created cluster has generated 100 MW as expected
to feed the load, and had to start 4 units (NODU column).

```shell
            area  cluster  timeId  production  NP Cost  NODU  Profit - Euro
0     my-country  nuclear       1       100.0      0.0   4.0            0.0
1     my-country  nuclear       2       100.0      0.0   4.0            0.0
2     my-country  nuclear       3       100.0      0.0   4.0            0.0
3     my-country  nuclear       4       100.0      0.0   4.0            0.0
4     my-country  nuclear       5       100.0      0.0   4.0            0.0
...          ...      ...     ...         ...      ...   ...            ...
8731  my-country  nuclear    8732       100.0      0.0   4.0            0.0
8732  my-country  nuclear    8733       100.0      0.0   4.0            0.0
8733  my-country  nuclear    8734       100.0      0.0   4.0            0.0
8734  my-country  nuclear    8735       100.0      0.0   4.0            0.0
8735  my-country  nuclear    8736       100.0      0.0   4.0            0.0

[8736 rows x 7 columns]
```
