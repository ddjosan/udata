import logging

log = logging.getLogger(__name__)

_providers = {}


def register_provider(name, func):
    """Register a notification provder"""
    _providers[name] = func


def list_providers():
    """List registere notifcation provider"""
    return _providers.keys()


def notifier(name):
    """A decorator registering a function as provider"""

    def wrapper(func):
        register_provider(name, func)
        return func

    return wrapper


def get_notifications(user):
    """List notification for a given user"""
    notifications = []
    dismissed_until = user.notifications_dismissed_until

    for name, func in _providers.items():
        for dt, details in func(user):
            if dismissed_until and dt <= dismissed_until:
                continue
            notifications.append({"type": name, "created_on": dt, "details": details})

    return notifications
