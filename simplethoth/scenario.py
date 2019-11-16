from json import load


def flatten_dictionary(d):
    result = {}
    for key, value in d.items():
        if type(value) == dict:
            result.update({
                f'{key}_{inner_key}': inner_value
                for inner_key, inner_value
                in flatten_dictionary(value).items()
            })
        else:
            result[key] = value
    return result


def map_all_value(obj, fn):
    return {
        key: map_all_value(value, fn)
            if type(value) == dict else fn(value)
        for key, value in obj.items()
    }


class ContextManager:
    def __init__(self, context: dict = {}):
        self._context = context
    
    def get(self, key, fallback = None):
        result = self._context
        
        for token in key.split('.'):
            if token in result.keys():
                result = result.get(token)
            else:
                return fallback
        
        return result
    
    def format_message(self, message, **kwargs):
        kwargs.update(flatten_dictionary(self._context))
        return message.format(**kwargs)
    
    def check(self, condition, **kwargs):
        kwargs.update(flatten_dictionary(self._context))
        for key, query in condition.items():
            value = kwargs.get(key, None)
            for operator, operand in query.items():
                if operator == 'is':
                    return value == operand
                elif operator == 'exists':
                    return bool(value) == operand
                else:
                    raise NotImplementedError(f'Unknown operator: `{operator}`')
        
        return True


class Scenario:
    def __init__(self, path, encoding='utf-8'):
        with open(path, encoding=encoding) as fp:
            self._data = load(fp)
            self.state_nodes = {
                node['state']: node
                for node in self._data
            }
            self.fallback_state = self.state_nodes.get(None, {})

    def action(self, context: dict, message: str):
        """
        """
        req_context = ContextManager(context)
        state = req_context.get('Dialog.state')
        state_node = self.state_nodes.get(state, self.fallback_state)

        current_node = state_node
        format_message = lambda m: (req_context.format_message(m, msg=message) if isinstance(m, str) else m)

        for branch in state_node.get('branch', []):
            if req_context.check(branch.get('condition', {}), msg=message):
                current_node = branch.get('then', {})
        
        return {
            'msg': [
                format_message(m)
                for m in current_node.get('message', [])
            ],
            'platform': map_all_value(current_node.get('platform', {}), format_message),
            'context': map_all_value(current_node.get('context', {}), format_message),
        }
