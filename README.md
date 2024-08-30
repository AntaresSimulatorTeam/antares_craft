Antares Craft python library is currently under construction. When completed it will allow to create, update and read antares studies.

This project only supports antares studies with a version v8.8 or higher.

To reformat your code, use this command line : `ruff check src/ tests/ --fix && ruff format src/ tests/`

To launch integration tests you'll need an AntaresWebDesktop instance on your local env (at least the v.2.17.3, **currently running in 2.17.5**).  
To install it, download it from the last [Antares Web release](https://github.com/AntaresSimulatorTeam/AntaREST/releases) (inside the assets list).  
Then, unzip it at the root of this repository and rename the folder `AntaresWebDesktop`.  
*NB*: The expected folder structure is the following: `antares_craft/AntaresWebDesktop/config.yaml`
