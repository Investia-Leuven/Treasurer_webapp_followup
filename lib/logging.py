import json

def log_event(level, message, **context):
    """
    Logs events in a structured JSON format with a given level and message.
    Additional context can be provided as keyword arguments.
    """
    log = {"level": level, "message": message}
    log.update(context)
    print(json.dumps(log))
