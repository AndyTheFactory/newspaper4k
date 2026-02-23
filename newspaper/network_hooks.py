import inspect
import sys
import threading
from collections import defaultdict
from contextlib import contextmanager

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """Fallback for Python < 3.11"""

        pass


from functools import wraps
from typing import Any, Literal, Protocol

_lock = threading.RLock()
_hooks = defaultdict(list)  # keys: 'before_request','after_response','on_error'


class HookableEvent(StrEnum):
    """Enumeration of hookable network events used by the hooks system.

    Values:
        BEFORE_REQUEST: Emitted before a request is made.
        AFTER_RESPONSE: Emitted after a successful response.
        ON_ERROR: Emitted when an exception occurs during the request.
    """

    BEFORE_REQUEST = "before_request"
    AFTER_RESPONSE = "after_response"
    ON_ERROR = "on_error"


HookableEventType = Literal["before_request", "after_response", "on_error"]


class HookCallable(Protocol):
    """Protocol for hook callables used by network hooks.

    A hook is invoked with the same signature as request functions: url,
    a configuration object, an optional HTTP method, optional request data,
    and any additional args/kwargs. BEFORE_REQUEST hooks may return a boolean
    value to indicate whether the request should continue.
    """

    def __call__(
        self,
        url: str,
        config: Any,
        method: str = "get",
        data: str | None = None,
        *args,
        **kwargs,
    ) -> bool | None | Any:
        """Invoke the hook with request parameters.

        Args:
            url: The target URL.
            config: Opaque request configuration object.
            method: HTTP method (default 'get').
            data: Optional request body.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Any: Hook-specific return value; BEFORE_REQUEST hooks may return
            a truthy value (False to halt the request, any other value to continue).
        """
        ...


def add_hook(event: HookableEventType, fn: HookCallable) -> None:
    """Register a hook function for a named event.

    Args:
        event: The event name (e.g. 'before_request', 'after_response', 'on_error').
        fn: A callable to be invoked for the given event.

    The callable must be callable and either declare parameters named 'url' and 'config'
    or accept arbitrary positional args (i.e. have *args).
    """

    if not callable(fn):
        raise TypeError("hook must be callable")

    sig = inspect.signature(fn)
    params = sig.parameters
    has_var_positional = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params.values())
    if not (has_var_positional or {"url", "config"}.issubset(params.keys())):
        raise TypeError("hook must declare parameters named 'url' and 'config', or accept *args")

    with _lock:
        _hooks[event].append(fn)


def remove_hook(event: HookableEventType, fn: HookCallable) -> None:
    """Unregister a previously registered hook function for an event.

    If the function is not registered for the event this is a no-op.

    Args:
        event: The event name to remove the hook from. (e.g. 'before_request', 'after_response', 'on_error').
        fn: The callable to remove.
    """
    with _lock:
        try:
            _hooks[event].remove(fn)
        except ValueError:
            # ignore if fn is not present
            pass


def clear_hooks(event: HookableEventType | None = None) -> None:
    """Clear hooks for a specific event or all events.

    Args:
        event: The event name to clear hooks for. (e.g. 'before_request', 'after_response', 'on_error').
            If None, clears all hooks.
    """
    with _lock:
        if event is None:
            _hooks.clear()
        else:
            _hooks[event].clear()


def get_hooks(event: HookableEventType) -> list[HookCallable]:
    """Return a shallow copy of the hook list for the given event.

    Args:
        event: The event name whose hooks to retrieve.

    Returns:
        A list of callables registered for the event.
    """
    with _lock:
        return list(_hooks.get(event, []))


@contextmanager
def local_hook(event: HookableEventType, fn: HookCallable):
    """Temporarily register a hook for the given event for the lifetime of the context.

    The provided callable `fn` is added before entering the context and removed when
    the context exits (even if an exception is raised).

    Args:
        event: The event name to attach the hook to.
        fn: The callable to register as a hook.

    Yields:
        None
    """
    add_hook(event, fn)
    try:
        yield
    finally:
        remove_hook(event, fn)

    return None


def hookable_func(func):
    """
    Decorator to wrap a request function so registered hooks are called
    with the same signature (*args, **kwargs) as the wrapped function.
    Events called: 'before_request' (before), 'on_error' (if exception),
    'after_response' (after success).
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        continue_request = True
        for hook in get_hooks(HookableEvent.BEFORE_REQUEST):
            continue_request = hook(*args, **kwargs) and continue_request

        if not continue_request:
            # If any before_request hook returns False, we skip the request and return None.
            return None

        try:
            result = func(*args, **kwargs)
        except Exception:
            for hook in get_hooks(HookableEvent.ON_ERROR):
                hook(*args, **kwargs)
            raise

        for hook in get_hooks(HookableEvent.AFTER_RESPONSE):
            hook(*args, **kwargs)

        return result

    return wrapper
