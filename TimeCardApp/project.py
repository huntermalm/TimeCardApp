class Project:

    def __init__(self, project_name):
        self.name = project_name
        self.hotkey = None
        self.times = []

    def add_time(self, start_time, end_time):
        self.times.append((start_time, end_time))

    def type(self):
        return "project"


class Folder:

    def __init__(self, folder_name):
        self.name = folder_name
        self.collapsed = True
        self.files = []

    def type(self):
        return "folder"
