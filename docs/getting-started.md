# Introduction

With antares-craft you can interact with studies using AntaresWeb API or in local mode.
To interact with AntaresWeb you need a token.

## Install antares_craft

You can install `antares_craft` using your usual python package manager:

```shell
pip install antares_craft
```

## Create a new study or reference an existing study

First, you will want to create a `Study` object to interact with, either by creating a new study or by referencing
an existing study.
For those operations, the syntax slightly depends on whether you want to work on studies on you filesystem, or studies
stored in an antares-web application.

### antares-web studies

In order to create a study on your antares-web server, you can use the the `create_study_api` method.

```python
from antares.craft import APIconf, create_study_api

api_config = APIconf(api_host="https://antares-web.mydomain",
                     token="my-token")
study = create_study_api(study_name="my-study",
                         version="8.8",
                         api_config=api_config)
```

If you prefer to refer to an existing study, you may use its sibling method, `read_study_api`:

```python
from antares.craft import APIconf, read_study_api

api_config = APIconf(api_host="https://antares-web.mydomain",
                     token="my-token")
study = read_study_api(api_config=api_config,
                       study_id="my-study-id")
```

## Filesystem studies

In order to create a study on your filesystem, you can use the the `create_study_local` method.

```python
from pathlib import Path
from antares.craft import create_study_local

study = create_study_local(study_name="my-study",
                           version="8.8",
                           parent_directory=Path("/path/to/my/studies/"))
```

If you prefer to refer to an existing study, you may use its sibling method, `read_study_local_`:

```python
from antares.craft import read_study_local

study = read_study_local(study_path="/path/to/my/study")
```

## Read and edit your study

Once you have your `Study` object, all read and edit operations are the same, be it for antares-web studies or
filesystem studies, allowing you to re-use code on both kind of studies.

You can for example read the existing areas:

```python
area_list = study.read_areas()
```

And create new areas.

```python
area_properties = AreaProperties(energy_cost_unsupplied=10)
study.create_area("fr", area_properties)
```

