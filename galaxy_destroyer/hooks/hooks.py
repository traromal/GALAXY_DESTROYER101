"""Hooks package - reusable logic components"""

from typing import Any, Callable, Optional, Dict, List
from dataclasses import dataclass
import time


@dataclass
class Hook:
    name: str
    callback: Callable
    enabled: bool = True


class Hooks:
    """Hook manager for events"""
    
    def __init__(self):
        self._hooks: Dict[str, List[Hook]] = {}
    
    def register(self, name: str, callback: Callable) -> None:
        if name not in self._hooks:
            self._hooks[name] = []
        self._hooks[name].append(Hook(name=name, callback=callback))
    
    def unregister(self, name: str, callback: Callable) -> None:
        if name in self._hooks:
            self._hooks[name] = [h for h in self._hooks[name] if h.callback != callback]
    
    def trigger(self, name: str, *args, **kwargs) -> List[Any]:
        results = []
        if name in self._hooks:
            for hook in self._hooks[name]:
                if hook.enabled:
                    try:
                        result = hook.callback(*args, **kwargs)
                        results.append(result)
                    except Exception as e:
                        pass
        return results
    
    def enable(self, name: str) -> None:
        if name in self._hooks:
            for hook in self._hooks[name]:
                hook.enabled = True
    
    def disable(self, name: str) -> None:
        if name in self._hooks:
            for hook in self._hooks[name]:
                hook.enabled = False
    
    def clear(self, name: str = None) -> None:
        if name:
            self._hooks[name] = []
        else:
            self._hooks.clear()


_hooks = Hooks()


def get_hooks() -> Hooks:
    return _hooks


def register_hook(name: str, callback: Callable) -> None:
    _hooks.register(name, callback)


def trigger_hook(name: str, *args, **kwargs) -> List[Any]:
    return _hooks.trigger(name, *args, **kwargs)


class UseState:
    """Simple state hook"""
    
    def __init__(self, initial: Any = None):
        self._value = initial
    
    def get(self) -> Any:
        return self._value
    
    def set(self, value: Any) -> None:
        self._value = value
    
    def update(self, fn: Callable[[Any], Any]) -> None:
        self._value = fn(self._value)


class UseEffect:
    """Effect hook - runs after render"""
    
    def __init__(self, effect: Callable, deps: List = None):
        self.effect = effect
        self.deps = deps or []
        self._last_run = None
    
    def should_run(self) -> bool:
        if self._last_run is None:
            return True
        if self.deps:
            return False
        return True
    
    def run(self) -> None:
        if self.should_run():
            self.effect()
            self._last_run = time.time()


class UseCallback:
    """Callback hook - memoized function"""
    
    def __init__(self, fn: Callable, deps: List = None):
        self.fn = fn
        self.deps = deps or []
    
    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)


class UseMemo:
    """Memoized value hook"""
    
    def __init__(self, compute: Callable, deps: List = None):
        self.compute = compute
        self.deps = deps or []
        self._value = None
        self._computed = False
    
    def get(self) -> Any:
        if not self._computed:
            self._value = self.compute()
            self._computed = True
        return self._value


class UseInterval:
    """Interval hook"""
    
    def __init__(self, callback: Callable, delay: float):
        self.callback = callback
        self.delay = delay
        self._running = False
    
    def start(self) -> None:
        self._running = True
    
    def stop(self) -> None:
        self._running = False


class UseDebounce:
    """Debounce hook"""
    
    def __init__(self, value: Any, delay: float):
        self.value = value
        self.delay = delay
        self._debounced = value
        self._last_update = time.time()
    
    def get(self) -> Any:
        if time.time() - self._last_update > self.delay:
            self._debounced = self.value
        return self._debounced


class UseThrottle:
    """Throttle hook"""
    
    def __init__(self, callback: Callable, delay: float):
        self.callback = callback
        self.delay = delay
        self._last_call = 0
    
    def call(self, *args, **kwargs) -> None:
        now = time.time()
        if now - self._last_call >= self.delay:
            self.callback(*args, **kwargs)
            self._last_call = now