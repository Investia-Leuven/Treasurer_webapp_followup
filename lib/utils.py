# lib/utils.py

import json

def log_event(level, message, **context):
    log = {"level": level, "message": message}
    log.update(context)
    print(json.dumps(log))