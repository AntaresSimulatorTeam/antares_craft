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
area_properties = AreaProperties(energy_cost_unsupplied=10)
study.create_area("fr", area_properties)
```

### How to access study areas

```
area_list = study.read_areas()
```