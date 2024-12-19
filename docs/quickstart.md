# Reference

To start using Antares Craft create a study using either the API or local modes, you can then build on the created object to add study elements as you go:

Exemple:

    from antares.craft.model.study import create_study_local

    study = create_study_local("test_study", 880, {"local_path": "test_study", "study_name": "test_study"})
