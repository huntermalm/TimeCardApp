def update_user_data(settings, project_data, user_data_dir):
    import os
    import pickle

    if settings["version"] in "1.1.0 1.0.2 1.0.1 1.0.0".split():
        settings["check_for_updates"] = True
        settings["version"] = "1.2.0"

    if settings["version"] in "1.2.1 1.2.0".split():
        if os.path.isfile(user_data_dir + "projects"):
            with open(user_data_dir + "projects", "rb") as f:
                old_project_data = pickle.load(f)

            project_data.extend(old_project_data)
            os.remove(user_data_dir + "projects")
            settings["version"] = "1.2.2"
