import os
import json

from vpc_vpn_pivot.constants import STATE_PATH, STATE_FILE


class State(object):
    def __init__(self):
        os.makedirs(STATE_PATH, exist_ok=True)

    def get(self, key):
        try:
            state = json.loads(open(STATE_FILE).read())
        except FileNotFoundError:
            return None
        else:
            return state.get(key, None)

    def append(self, key, value):
        state = self.dump()
        state[key] = value
        self.force(state)

    def dump(self):
        try:
            json.loads(open(STATE_FILE).read())
        except FileNotFoundError:
            return {}

    def force(self, state):
        state = json.dumps(state, indent=4, sort_keys=True)
        open(STATE_FILE, 'w').write(state)
