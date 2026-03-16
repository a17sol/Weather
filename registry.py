providers = {}

def register_provider(name):
    def decorator(func):
        providers[name] = func
        return func
    return decorator
