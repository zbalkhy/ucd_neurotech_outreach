class filterClass():
    def __init__(self, filter_name: str):
        self.filter_name: str = filter_name
        self.filters: dict = {'filter': [], 'order': [], 'frequency': []}
    def get_filters(self):
        return self.filters
    def add_filters(self, name, value):
        self.filters[name].append(value)
        
        