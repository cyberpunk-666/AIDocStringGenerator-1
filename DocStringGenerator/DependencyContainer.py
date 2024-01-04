from typing import Union, Callable, Generic
from typing import Any, Type, TypeVar, Dict, Optional
from enum import Enum, auto
import threading
from flask import session
from flask.sessions import SessionMixin

T = TypeVar('T')

class Scope(Enum):
    SINGLETON = auto()
    SCOPED = auto()
    TRANSIENT = auto()

class DependencyNotRegisteredError(KeyError):
    pass

class SingletonWrapper(Generic[T]):
    def __init__(self, cls: Callable[..., T]) -> None:
        self.cls: Callable[..., T] = cls
        self._singleton_instance: Optional[T] = None

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        if self._singleton_instance is None:
            self._singleton_instance = self.cls(*args, **kwargs)
        return self._singleton_instance

    
class DependencyContainer:
    _instance: Optional['DependencyContainer'] = None
    _lock: Any = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DependencyContainer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_is_initialized') or not self._is_initialized:
            self.dependencies: Dict[Type[Any], tuple[Callable[..., Any], Scope]] = {}
            self._is_initialized = True


    def register(self, interface: Type[T], implementation: Union[Callable[..., T], SingletonWrapper[T]], scope: Scope = Scope.SINGLETON):
        self.dependencies[interface] = (implementation, scope)


    def resolve(self, interface: Type[T], *args: Any, **kwargs: Any) -> T:
        implementation_info = self.dependencies.get(interface)
        if not implementation_info:
            raise DependencyNotRegisteredError(f"No implementation registered for {interface}")

        implementation, scope = implementation_info
        if scope == Scope.SINGLETON:
            return implementation(*args, **kwargs)
        elif scope == Scope.SCOPED:
            _scoped_instances: Dict[Type[T], T] = session.get('_scoped_instances', [])
            if isinstance(session, SessionMixin) and _scoped_instances is None:
                _scoped_instances = {}
                session['_scoped_instances'] = _scoped_instances

            if _scoped_instances:
                scoped_instances: Dict[Type[T], T] = _scoped_instances
                if interface not in scoped_instances:
                    scoped_instances[interface] = implementation(*args, **kwargs)
                return scoped_instances[interface]
            else:
                return implementation(*args, **kwargs)
        elif scope == Scope.TRANSIENT:
            return implementation(*args, **kwargs)
        else:
            raise ValueError(f"Unknown scope: {scope}")
