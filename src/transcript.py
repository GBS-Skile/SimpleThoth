import json
import sys


class ParseError(Exception):
    def __init__(self, message):
        self.message = message
    
    def __str__(self):
        return self.message


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


def transcript(file):
    scenario = []
    state = None
    state_manager = StateManager()

    for line in file:
        tokens = line.strip().split()
        if len(tokens) == 0:
            continue

        command = tokens[0]
        args = tokens[1:]

        if command == '#':
            pass    # comment
        elif command == 'STATE':
            name = ''

            if len(args) > 1:
                raise ParseError('Wrong command: STATE [STATE_NAME]')
            elif len(args) == 1:
                name = args[0]
            else:
                name = state_manager.get_valid_state_name()

            old_state = state
            state = state_manager.get_state(name)
            scenario.append(state)

            if old_state and 'next_state' not in old_state:
                old_state['next_state'] = name
        elif command == 'STATE?':
            state = state_manager.get_state(None)
            scenario.append(state)
        elif command == '>':
            if state is None:
                raise ParseError('Wrong command: STATE not defined.')

            state.setdefault('message', []).append(' '.join(args))
        elif command == 'GOTO':
            if len(args) > 1:
                raise ParseError('Wrong command: GOTO <STATE_NAME>')

            if state is None:
                raise ParseError('Wrong command: STATE not defined.')

            if 'next_state' in state.keys():
                raise ParseError('Wrong command: GOTO duplicated.')

            state['next_state'] = args[0]
        elif command == '<':
            state.setdefault('platform', {}) \
                .setdefault('quick_replies', []) \
                .append(' '.join(args))
        else:
            raise ParseError(f'Command {command} does not exist.')
    
    print(json.dumps(scenario, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python transcript.py <FILE_PATH>')
    else:
        with open(sys.argv[1], encoding='utf-8') as f:
            transcript(f)
