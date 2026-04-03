# Antares Craft by Example

Here are some examples of the use of `antares_craft` to set, launch and retrieve data from a study.
It assumes you are already familiar with connection to the API (see [Getting Started](getting-started/first-steps.md)).

!!! note "Local study"

    In the following, the examples given are assumed for an API study.
    However, they generally work for both local and API studies apart specific method/function. 
    For example, use `create_study_local` instead of `create_study_api`.
    Note that the arguments may differ.


## Add areas

Let's add for example 3 areas `fr`, `de` and `be` with various positions on the map. 
You can also decide deterministically the node position on the map.

``` py 
fr_properties = craft.AreaProperties(energy_cost_unsupplied=3000, spread_spilled_energy_cost=43.2)
ui_fr = craft.AreaUi(x=10, y=-30, color_rgb=[11, 0, 255])
area_fr = study.create_area("FR", properties=fr_properties, ui=ui_fr)

other_properties = craft.AreaProperties(energy_cost_unsupplied=3000, filter_by_year={craft.FilterOption.ANNUAL}, filter_synthesis={craft.FilterOption.HOURLY})
generator = np.random.default_rng(1000)
for area_name in ["be", "de"]:
    x = generator.integers(-100, 100)
    y = generator.integers(-100, 100)
    color= generator.integers(0, 255)
    ui = craft.AreaUi(x=x, y=y, color_rgb=[color, color // 2, color // 3])
    area = study.create_area(area_name, properties=other_properties, ui=ui)
    print(f"Area {area.id} successfully created")
```

## Add links

To create links between areas, you have to set a direct and indirect hourly capacity. 
For example, we can create 3 links to create a network between France, Belgium and Germany.

```py
link_be_fr = study.create_link(area_from='be', area_to="fr")
link_be_fr.set_capacity_direct(pd.DataFrame(8760 * [1000]))
link_be_fr.set_capacity_indirect(pd.DataFrame(8760 * [1000]))

link_be_de = study.create_link(area_from="be", area_to='de')
link_be_de.set_capacity_direct(pd.DataFrame(8760 * [800]))
link_be_de.set_capacity_indirect(pd.DataFrame(8760 * [800]))

link_de_fr = study.create_link(area_from="de", area_to='fr')
link_de_fr.set_capacity_direct(pd.DataFrame(8760 * [500]))
link_de_fr.set_capacity_indirect(pd.DataFrame(8760 * [500]))
```

## Set a load for an area

You can set a load for the `fr` area by loading a file such as a `csv`, `tsv`... by using the `pandas` module.

```py
import pandas as pd

load_fr = pd.read_csv(Path.cwd() / "load_area_fr.csv", sep=",", index_col=0)
area_fr.set_load(load_fr)
```

You can fill also other areas with some random load:

```py
for area_name in ["be", "de"]:
    random_matrix = pd.DataFrame(generator.integers(low=1000, high=2000, size=(8760, 5)))
    study.get_areas()[area_name].set_load(random_matrix)
    print(f"Load series generated (random values) for area {area_name}")
```

## Add clusters

Let's say that in our study, we want to add clusters to each area:
- A nuclear cluster inside area France with 8 units of 1400 MW nominal capacity and some custom time-series.
- A lignite power plant in Germany with 4 units of 500 MW of capacity that emit 0,846 tCO2/MWh.
- Some gas units in Belgium with 3 units of 200 MW of capacity and emit 0,354 tCO2/MWh.

```py
# France
area = study.get_areas()["fr"]
nuclear_properties = craft.ThermalClusterProperties(
    group="nuclear",
    nominal_capacity=1200,
    unit_count=6,
    gen_ts=craft.LocalTSGenerationBehavior.FORCE_NO_GENERATION)
new_cluster = area.create_thermal_cluster("Nuclear facility", nuclear_properties)
nuclear_ts = pd.read_csv(Path.cwd() / "nuclear_production_ts.csv", sep=",", index_col=0)
new_cluster.set_series(nuclear_ts)
print(f"Cluster {new_cluster.id} successfully created in area {area.id}")

# Germany
area = study.get_areas()["de"]
cluster_properties = craft.ThermalClusterProperties(
    group="lignite",
    co2=0.846,
    nominal_capacity=500,
    unit_count=4)
new_cluster = area.create_thermal_cluster("Lignite power plant", cluster_properties)
print(f"Cluster {new_cluster.id} successfully created in area {area.id}")

# Belgium
area = study.get_areas()["be"]
cluster_properties = craft.ThermalClusterProperties(
    group="CCGT New",
    co2=0.354,
    nominal_capacity=200,
    unit_count=3)
new_cluster = area.create_thermal_cluster("CCGT New", cluster_properties)
print(f"Cluster {new_cluster.id} successfully created in area {area.id}")
```

To generate the availability time-series for all units except those with FORCE_NO_GENERATION property

```py
study.generate_thermal_timeseries(5)
```

Here five different years are generated with hourly availability.

## Add a battery

To add a battery you need to use the object `STStorageProperties` for short-term storage. 
You need to set an efficiency and an injection capacity (in MW).

```py
battery_properties = craft.STStorageProperties(
    injection_nominal_capacity=50,
    efficiency=0.89,
    group="battery")
storage = area_fr.create_st_storage("my_battery", battery_properties)
```

## Create a binding constraint between two links

Let's assume that the flow between Belgium -> France should be equal to the flow Belgium -> Germany. 
You can create a binding constraint like this:

``` py
term1 = craft.ConstraintTerm(weight=1, data=craft.LinkData(area1="be", area2="fr"))
term2 = craft.ConstraintTerm(weight=-1, data=craft.LinkData(area1="be", area2="de"))
study.create_binding_constraint(name="bc1", terms=[term1, term2])
```

## Create a variant of a study

!!! note

    You can only create a variant of a study with the API thanks to the data optimization.

When you have a main study and you want to study the variation of ouput made by an isolated change on the input, you can create a variant. 
It applies the difference on the main input only when launching the simulation allowing no unecessary data duplication. 
To create a variant using you `api_configuration` from the initialization of `APIconf`:

```py
variant_study = craft.create_variant_api(api_configuration, "study_id", "variant_1")
```

Then you can apply changes on this variant study. For example, you can edit the unsupplied energy cost for all areas 
apart from France and test a new parameter `new_val`:

```py
areas = variant_study.get_areas()
new_cost = craft.AreaPropertiesUpdate(energy_cost_unsupplied=new_val)
mapping = {area: new_cost for area in areas.values() if area.id != "fr"}
variant_study.update_areas(mapping)
```

Eventually, you can delete the variant if you don't use it:

```py
variant_study.delete()
```

## Preparing to launch

The simulation settings are stored in the `AntaresSimulationParametersAPI` class. To run the simulation with 5 CPU and the [sirius solver](https://github.com/AntaresSimulatorTeam/sirius-solver):

```py
simulation_parameters = craft.AntaresSimulationParametersAPI(
    solver=craft.Solver.SIRIUS,
    output_suffix="sirius_fast",
    nb_cpu=5)
job = study.run_antares_simulation(simulation_parameters)
study.wait_job_completion(job)
```

Then, if you want to run the simulation, you pass the simulation parameters just created:

```py
job = study.run_antares_simulation(simulation_parameters)
study.wait_job_completion(job)
```




## Retrieve data

### Get a summary of thermal cluster

You want to retrieve the data from all thermal cluster in France and display for each cluster in a table:
- The number of units (`unit_count`)
- The nominal capacity (`nominal_capacity`)
- The marginal cost (`marginal_cost`)

```py
area_fr = study.get_areas()["fr"]
mapping = {}
for thermal_name, thermal in area_fr.get_thermals().items():
    props = thermal.properties
    mapping[thermal_name] = {"unit_count": props.unit_count, "nominal_capacity": props.nominal_capacity, "marginal_cost": props.marginal_cost}
df = pd.DataFrame(mapping).transpose()
```

### Displaying load time-series

If you want to load all the time-series for all MC year and for a specific area (for example "fr"), you can simply:

```py
area_fr = study.get_areas()["fr"]
load = area_fr.get_load_matrix()
```

And then, you can apply multiple operations using the classic [`pandas`](https://pandas.pydata.org/docs/) python module. 
For example, you can show the max consumptio for each MC year : `#!python load.max()`.

### Read outputs

Imagine you want to get the average loss of load duration (LOLD) that is to say the duration of shortfalls over all the MC years for each area.
You select your output simulation and create a dataframe with all the LOLD time-series for each area and each MC year.

```py
outputs = study.get_outputs()
output = outputs['my-output-id']
result = output.aggregate_mc_ind_areas(
    data_type=craft.MCIndAreasDataType.VALUES, 
    frequency=craft.Frequency.HOURLY, 
    mc_years=[], 
    areas_ids=[], 
    columns_names=["LOLD"]
    )
nb_mcyears = result["mcYear"].nunique()
final_df = result.groupby("area")['LOLD'].sum() / nb_mcyears
```

Note that here, omitting specify `mc_years` or `areas_id` defaults to selecting all years and areas.

## Delete an API study

Optionally, you can delete a study with:

```py
study.delete()
```



