class Project:

    def __init__(self, project_name):
        self.name = project_name
        self.times = []

    def add_time(self, start_time, end_time):
        self.times.append((start_time, end_time))
