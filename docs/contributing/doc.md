# Contributing to the documentation

Don't hesitate to raise an issue on GitHub 
[:octicons-link-external-16:](https://github.com/AntaresSimulatorTeam/antares_craft/issues) ! 
You might feel that there are some documentation not up to date or other problems.

## Writing documentation

This documentation is built using [MkDocs](https://www.mkdocs.org) a static site generator from Markdown pages.
The API reference is generated automatically with the docstrings of the python code.

### Editing on GitHub

To modify the documentation on GitHub in the user interface. First, you can click on the :material-file-edit-outline:
icon at the top right of the page you want to edit. It will open GitHub to edit the source page associated.
Then, you follow the instructions to fork the repo inside the interface. 

Note that you can also check the source code by a clicking on the :material-file-eye-outline: icon.

!!! Tip

    You can find some more precise instruction on how to use GitHub for editing files here [:octicons-link-external-16:](https://docs.github.com/en/repositories/working-with-files/managing-files/editing-files).

### Editing locally

After cloning the repository on your machine, you can install the documentation 
requirements by running in your terminal:

```
pip install -r requirements-dev.txt
```
And now you are ready to edit pages !

1. To preview the docs on your local machine run `mkdocs serve`. 
    You will be able to open a preview of the doc in your browser. 
    It will reload automatically when you change and save a file.
2. To build the static site for publishing for example on [Read the Docs](https://readthedocs.io) use `mkdocs build`.
3. To flesh out the documentation see [mkdocs guides](https://www.mkdocs.org/user-guide/).