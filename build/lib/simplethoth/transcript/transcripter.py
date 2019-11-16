import ast
import json
import sys

from .states import StateManager
from .errors import ParseError


def _get_items(obj, *, sep='.'):
    items = {}
    for key, value in obj.items():
        if type(value) is dict:
            items.update({
                f'{key}.{subkey}': subvalue for subkey, subvalue
                in _get_items(value, sep=sep).items()
            })
        else:
            items.update({key: value})
    
    return items


def _get_attribute(obj, path, *, sep='.', fallback=None):
    tokens = path.split(sep)
    for token in tokens[:-1]:
        try:
            obj = obj[token]
        except KeyError:
            return fallback
    
    return obj.get(tokens[-1], fallback)


def _set_attribute(obj, path, value, *,
    sep='.', append=False, safe=False):
    if append and safe:
        raise ValueError("`append`, `safe` option cannot be together.")

    tokens = path.split(sep)
    for idx, token in enumerate(tokens):
        if idx != len(tokens) - 1:
            obj = obj.setdefault(token, {})
        else:
            if append:
                obj.setdefault(token, []).append(value)
            elif not safe:
                obj[token] = value
            else:
                obj.setdefault(token, value)
    
    return value


class Transcripter:
    COMMENT_INDICATOR = '#'

    def __init__(self):
        self._commands = {}
    
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
        if name.startswith(self.COMMENT_INDICATOR):
            raise KeyError(f'The name of command should not start with `{self.COMMENT_INDICATOR}`.')

        if name in self._commands.keys():
            raise KeyError(f'Command {name} should be unique.')

        return self.Command(self, name, *args, **kwargs)
    
    def invoke_command(self, command, args):
        if command in self._commands.keys():
            return self._commands[command](*args)

        raise ParseError(f'Command {command} does not exist.')
    
    def transcript(self, fp):
        self.state_manager = StateManager()
        self.scenario = []
        self.state = None

        for lineno, line in enumerate(fp):
            tokens = line.strip().split()
            if len(tokens) == 0:
                continue

            if tokens[0].startswith(self.COMMENT_INDICATOR):
                continue
            
            try:
                self.invoke_command(tokens[0], tokens[1:])
            except ParseError as e:
                print(f"ParseError on line {lineno}: {str(e)}")
                return
        
        for state_node in self.scenario:
            before = state_node.get('before', None)
            if before:
                del state_node['before']
                nodes = [node for node in self.scenario]
                for node in self.scenario:
                    nodes.extend([branch['then'] for branch in node.get('branch', [])])
                
                for node in nodes:
                    if _get_attribute(node, 'context.Dialog.state') == state_node['state']:
                        for key, value in _get_items(before).items():
                            _set_attribute(node, key, value)
        
        return self.scenario
    
    @property
    def current(self):
        if self.branch is not None:
            return self.branch
        return self.state

    def set_field(self, path, value, **kwargs):
        return _set_attribute(self.current, path, value, **kwargs)


transcripter = Transcripter()


@transcripter.command('IF')
def cmd_set_branch(tr, variable, operator, *args):
    operand = ' '.join(args)
    tr.branch = tr.set_field('branch', {
        'condition': { variable: { operator: ast.literal_eval(operand) } },
        'then': {}
    }, append=True)['then']


@transcripter.command('<')
def cmd_add_quick_replies(tr, *args):
    title = ' '.join(args)

    tr.branch = None
    tr.set_field('before.platform.quick_replies', title, append=True)
    tr.branch = tr.set_field('branch', {
        'condition': { 'msg': { 'is': title } },
        'then': {}
    }, append=True)['then']


@transcripter.command(':')
def cmd_add_quick_replies(tr, *args):
    title = ' '.join(args)

    tr.branch = None
    tr.set_field('before.platform.quick_replies', title, append=True)


@transcripter.command('STATE', require_state=False)
def cmd_set_state(tr, name=None):
    if name is None:
        name = tr.state_manager.get_valid_state_name()

    old_state = tr.state
    tr.state = tr.state_manager.get_state(name)
    tr.branch = None
    tr.scenario.append(tr.state)

    if old_state:
        _set_attribute(old_state, 'context.Dialog.state', name, safe=True)
        for branch in old_state.get('branch', []):
            _set_attribute(branch['then'], 'context.Dialog.state', name, safe=True)


@transcripter.command('STATE?', require_state=False)
def cmd_set_default_state(tr):
    tr.state = tr.state_manager.get_state(None)
    tr.branch = None
    tr.scenario.append(tr.state)


@transcripter.command('>')
def cmd_add_message(tr, *args):
    tr.set_field('message', ' '.join(args), append=True)


@transcripter.command('GOTO')
def cmd_add_next_state(tr, state_name):
    # TODO State name verification
    tr.set_field('context.Dialog.state', state_name)


@transcripter.command('GOTOSELF')
def cmd_add_next_state(tr):
    # TODO State name verification
    tr.set_field('context.Dialog.state', tr.state['state'])


@transcripter.command('SET')
def cmd_set_context(tr, path, *args):
    value = ast.literal_eval(' '.join(args))
    tr.set_field(path, value, sep='_')


@transcripter.command('APPEND')
def cmd_set_context(tr, path, *args):
    value = ast.literal_eval(' '.join(args))
    tr.set_field(path, value, sep='_', append=True)
