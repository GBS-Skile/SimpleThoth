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
    for key, value in obj.items():
        if type(value) == dict:
            map_all_value(value, fn)
        else:
            obj[key] = fn(value)
    
    return obj


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


class Scenario:
    def __init__(self, path, encoding="utf-8"):
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

        format_message = lambda m: req_context.format_message(m, msg=message)
        
        return {
            'msg': [
                format_message(m)
                for m in state_node.get('message', [])
            ],
            'platform': state_node.get('platform'),
            'context': map_all_value(state_node.get('context'), format_message),
        }
