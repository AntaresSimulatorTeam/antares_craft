# Getting started

On this page you will find information for getting started quickly with `antares_craft`, together with a brief
introduction to main features.

## Installing Antares Craft

You can install `antares_craft` using your usual python package manager:

```shell
pip install antares_craft
```

## Create a new study or reference an existing study

First, you will want to create a `Study` object to interact with, either by creating a new study or by referencing
an existing study.
For those operations, the syntax slightly depends on whether you want to work on studies on you filesystem, or studies
stored in an antares-web application.

!!! warning

    Only study versions above v8.8 are currently supported.

### Antares-Web studies

In order to create a study on your antares-web server, you can use the the [
`create_study_api`][antares.craft.create_study_api] method.
You will need to define the URL of your server, and provide a token generated in the application in
order to authenticate.

```python
from antares.craft import APIconf, create_study_api

api_config = APIconf(api_host="https://antares-web.mydomain",
                     token="my-token")
study = create_study_api(study_name="my-study",
                         version="8.8",
                         api_config=api_config)
```

!!! question "How to generate your personal token?"

    To generate a token, go to :material-cog: **Settings** >  **TOKENS** tab
    and then click on **CREATE**. Copy the token and store it on your own computer. 
    Note that you cannot access again an already generated token. 

If you prefer to refer to an existing study, you may use its sibling method, [
`read_study_api`][antares.craft.read_study_api]:

```python
from antares.craft import APIconf, read_study_api

api_config = APIconf(api_host="https://antares-web.mydomain",
                     token="my-token")
study = read_study_api(api_config=api_config,
                       study_id="my-study-id")
```
!!! question "How to get your study ID?"

    In your folder listing all your study, you can copy the study ID from the copy :material-content-copy: icon
    on the upper right of the study preview. Equivalently, if your study is already open, you can copy the ID by clicking the same icon 
    on the upper right of the window.

### Filesystem studies

In order to create a study on your filesystem, you can use the the [
`create_study_local`][antares.craft.create_study_local] method.

```python
from pathlib import Path
from antares.craft import create_study_local

study = create_study_local(study_name="my-study",
                           version="8.8",
                           parent_directory=Path("/path/to/my/studies/"))
```

If you prefer to refer to an existing study, you may use its sibling method, [
`read_study_local`][antares.craft.read_study_local]:

```python
from antares.craft import read_study_local

study = read_study_local(study_path="/path/to/my/study")
```

## More examples

To see more examples check the page [Antares Craft by Example](../antares-craft-examples.md)