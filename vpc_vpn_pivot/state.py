import os
import json

STATE_FILE = os.path.expanduser('~/.vpc_vpn_pivot/state')
STATE_PATH = os.path.expanduser('~/.vpc_vpn_pivot')


class State(object):
    def __init__(self):
        os.makedirs(STATE_PATH, exist_ok=True)

    def get(self):
        try:
            json.loads(open(STATE_FILE).read())
        except FileNotFoundError:
            return {}

    def set(self, state):
        state = json.dumps(state, indent=4, sort_keys=True)
        open(STATE_FILE, 'w').write(state)

    def append(self, key, value):
        state = self.get()
        state[key] = value
        self.set(state)
