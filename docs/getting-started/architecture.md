# Package Architecture

## Preliminary notes on understanding `antares_craft`

The Antares Craft package closely relates to Antares-Web interface allowing not to guess how things are named.

The package follows an Object-Oriented Programming (OOP) architecture. Information is grouped by classes 
(named in the `CamelCase` convention) that are composed by:

- attributes to store values, parameter strings, paths to files or even other classes
- methods to perform actions on the class or its attributes

However, there are a handful of standalone functions that can be used by the user: 

- [create_study_api][antares.craft.create_study_api]
- [read_study_api][antares.craft.read_study_api]
- [import_study_api][antares.craft.import_study_api]
- [create_study_local][antares.craft.create_study_local]
- [read_study_local][antares.craft.read_study_local]

When you have in the UI some dropdown menus with multiple choices, there is generally a corresponding class
called an enumeration (`Enum`). You can access either option by using `.` and the name of the option in uppercase 
such as `Enum.OPTION1`.

Generally, to aggregate some parameters, there are some classes `XxxxProperties` and `XxxxPropertiesUpdate`. 
The second one differs only because all parameters field are optional. 
Moreover, all classes are not meant to be modified by the user. As some provides only default parameters. 

## Architecture

To better understand the architecture of the package, in the following diagrams will be presented for visual understanding. All classes and enums imported when using `#!python from antares.craft import *` are represented on these schematics. The arrows only represent a possible requirement. However, these classes may take numerical value attributes, paths, strings...

The legend for all these diagrams:

![](../assets/architecture-legend.drawio)

### Connection and main classes

The entry points of Antares are the configuration classes for either local or API configuration. 
Then you want to create the most import class : a `Study`. 

!!! note
    To create a study, please use the standalone functions and not the built in constructor of the `Study` class. 
    Then, to apply changes on the newly made study you can use `Study`'s methods. 

![starting](../assets/architecture-start.drawio)

### Areas and links

At the base of the modelization of an energy system in Antares are areas 
and links in between.

![areas](../assets/architecture-area.drawio)

![links](../assets/architecture-link.drawio)


### Xpansion

![xpansion](../assets/architecture-xpansion.drawio)

### Settings

The settings are divided roughly into two part. 
The settings for the simulation (simulator executable...): 

![simulation settings](../assets/architecture-simulation-settings.drawio)

And the settings for the study:

![settings](../assets/architecture-settings.drawio)

### Outputs

To analyze outputs from an Antares simulation, you need to use the `get_output`
method of the study you are working on. It will return an `Output` object.

![outputs](../assets/architecture-outputs.drawio)

### Binding constraints

![binding constraints](../assets/architecture-binding-constraints.drawio)