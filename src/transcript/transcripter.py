import json
import sys

from .states import StateManager
from .errors import ParseError


def _set_attribute(obj, path, value, *, sep='.', append=False):
    tokens = path.split(sep)
    for idx, token in enumerate(tokens):
        if idx != len(tokens) - 1:
            obj = obj.setdefault(token, {})
        else:
            if append:
                obj.setdefault(token, []).append(value)
            else:
                obj[token] = value


class Transcripter:
    def __init__(self):
        self._commands = {}
        self.state_manager = StateManager()
    
    class Command:
        def __init__(self, transcripter, name, *, require_state=True):
            self.transcripter = transcripter
            self.name = name
            self.require_state = require_state
        
        def __call__(self, fn):
            def __wrapper(*args, **kwargs):
                if self.require_state and not self.transcripter.state:
                    raise ParseError('Wrong command: STATE not defined.')

                return fn(transcripter, *args, **kwargs)

            self.transcripter._commands[self.name] = __wrapper
            return __wrapper
    
    def command(self, name, *args, **kwargs):
        if name in self._commands.keys():
            raise KeyError(f'Command {name} should be unique.')

        return self.Command(self, name, *args, **kwargs)
    
    def invoke_command(self, command, args):
        if command in self._commands.keys():
            return self._commands[command](*args)

        raise ParseError(f'Command {command} does not exist.')
    
    def transcript(self, fp):
        self.scenario = []
        self.state = None

        for line in fp:
            tokens = line.strip().split()
            if len(tokens) == 0:
                continue
            
            self.invoke_command(tokens[0], tokens[1:])
        
        for state_node in self.scenario:
            _set_attribute(state_node, 'context.Dialog.state', state_node['next_state'])
            del state_node['next_state']
        
        return self.scenario


transcripter = Transcripter()

@transcripter.command('#', require_state=False)
def cmd_comment(tr, *args):
    pass


@transcripter.command('<')
def cmd_add_quick_replies(tr, *args):
    _set_attribute(tr.state, 'platform.quick_replies', ' '.join(args), append=True)


@transcripter.command('STATE', require_state=False)
def cmd_set_state(tr, name=None):
    if name is None:
        name = tr.state_manager.get_valid_state_name()

    old_state = tr.state
    tr.state = tr.state_manager.get_state(name)
    tr.scenario.append(tr.state)

    if old_state and 'next_state' not in old_state:
        old_state['next_state'] = name


@transcripter.command('STATE?', require_state=False)
def cmd_set_default_state(tr):
    tr.state = tr.state_manager.get_state(None)
    tr.scenario.append(tr.state)


@transcripter.command('>')
def cmd_add_message(tr, *args):
    _set_attribute(tr.state, 'message', ' '.join(args), append=True)


@transcripter.command('GOTO')
def cmd_add_next_state(tr, state_name):
    if 'next_state' in tr.state.keys():
        raise ParseError('Wrong command: GOTO duplicated.')
    
    tr.state['next_state'] = state_name


@transcripter.command('SET')
def cmd_set_context(tr, path, value):
    _set_attribute(tr.state, 'context_' + path, value, sep='_')
