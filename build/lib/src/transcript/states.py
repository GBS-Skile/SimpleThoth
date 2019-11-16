from .errors import ParseError

class StateManager:
    def __init__(self):
        self.names = set()
    
    def get_valid_state_name(self):
        index = len(self.names)
        while str(index) in self.names:
            index += 1
        
        return str(index)
    
    def get_state(self, name):
        if name in self.names:
            raise ParseError(f'StateManager: STATE {name} duplicated.')

        self.names.add(name)
        return dict(state=name)
