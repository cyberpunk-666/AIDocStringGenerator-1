import threading
from typing import Type, Any, Callable, Dict, Tuple

class DependencyNotRegisteredError(KeyError):
    """Exception raised when a dependency is not registered."""
    pass

class DependencyContainer:


    def register(self, interface: Type, implementation: Callable, singleton: bool = True) -> None:
        """Register a dependency.

        Args:
            interface (Type): The interface or key under which to register the implementation.
            implementation (Callable): The implementation to register.
            singleton (bool): Whether to treat the implementation as a singleton.
        """
        self.dependencies[interface] = (implementation, singleton)

    def resolve(self, interface: Type, *args: Any, **kwargs: Any) -> Any:
        """Resolve a dependency.

        Args:
            interface (Type): The interface or key to resolve.

        Returns:
            Any: The resolved implementation.

        Raises:
            DependencyNotRegisteredError: If no implementation is registered for the interface.
        """
        implementation_info = self.dependencies.get(interface)
        if implementation_info:
            implementation, singleton = implementation_info
            if singleton:
                if not hasattr(implementation, "_singleton_instance"):
                    implementation._singleton_instance = implementation(*args, **kwargs)
                return implementation._singleton_instance
            else:
                return implementation(*args, **kwargs)
        else:
            raise DependencyNotRegisteredError(f"No implementation registered for {interface}")


class DependencyContainer:
    """
    A thread-safe singleton class used for dependency injection.

    The DependencyContainer class provides a centralized registry for managing dependencies. 
    It ensures that only one instance of the container is created (singleton pattern), 
    even in a multi-threaded environment. The container allows for registering dependencies 
    under a specific interface and later resolving them. This aids in decoupling the creation 
    and usage of objects, facilitating better testability and adherence to SOLID principles.

    Attributes:
        _instance (DependencyContainer): A private class-level attribute that stores the 
                                        single instance of the class.
        _lock (threading.Lock): A private class-level lock used to synchronize the creation 
                                of the singleton instance across multiple threads.
        dependencies (Dict[Type, Tuple[Callable, bool]]): A dictionary holding the registered 
                                                          dependencies. Each key is an interface or type, 
                                                          and the value is a tuple containing the 
                                                          implementation (Callable) and a boolean 
                                                          indicating if it should be treated as a singleton.

    Methods:
        __new__(cls): Overrides the default object creation mechanism to implement the singleton pattern.
        __init__(): Initializes the instance; called only once during the first instantiation.
        register(interface, implementation, singleton=True): Registers a dependency with the container.
        resolve(interface, *args, **kwargs): Resolves and returns an instance of the registered dependency.

    Raises:
        DependencyNotRegisteredError: If an attempt is made to resolve a dependency that hasn't been registered.
    """
    _instance: 'DependencyContainer' = None
    _lock = threading.Lock()


    def __new__(cls):
        """ 
        Create a new instance of DependencyContainer (singleton).

        This method ensures that only one instance of the DependencyContainer is created. 
        If an instance already exists, it returns that existing instance. Otherwise, 
        it creates a new instance. This method is thread-safe.

        Returns:
            DependencyContainer: The singleton instance of the DependencyContainer.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DependencyContainer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize the DependencyContainer instance.

        This method initializes the dependencies dictionary for the container. It is 
        designed to run only once; subsequent calls after the first instantiation 
        do not reinitialize the container.

        Note: 
            The __init__ method is not the typical constructor as it is only executed 
            once due to the singleton nature of the DependencyContainer.
        """
        if not hasattr(self, '_is_initialized') or not self._is_initialized:
            self.dependencies: Dict[Type, Tuple[Callable, bool]] = {}
            self._is_initialized = True

    def register(self, interface, implementation, singleton=True):
        """
        Register a dependency in the container.

        This method allows registering an implementation under a specific interface. 
        The implementation can be registered as a singleton or as a non-singleton (new 
        instance on each resolution).

        Args:
            interface (Type): The interface or type under which the implementation is to be registered.
            implementation (Callable): The concrete implementation of the interface.
            singleton (bool, optional): Whether the implementation should be treated as a singleton. 
                                        Defaults to True.

        Example:
            container.register(SomeInterface, SomeImplementation)
        """
        self.dependencies[interface] = (implementation, singleton)

    def resolve(self, interface, *args, **kwargs):
        """
        Resolve and return an instance of the registered dependency.

        This method returns an instance of the implementation registered under the provided interface. 
        If the implementation is registered as a singleton, it returns the same instance on each call. 
        If not, a new instance is created for each call. Additional arguments and keyword arguments 
        are passed to the constructor of the implementation.

        Args:
            interface (Type): The interface or type to resolve.
            *args: Variable length argument list passed to the implementation's constructor.
            **kwargs: Arbitrary keyword arguments passed to the implementation's constructor.

        Returns:
            Any: An instance of the registered implementation.

        Raises:
            DependencyNotRegisteredError: If no implementation is registered for the given interface.

        Example:
            instance = container.resolve(SomeInterface)
        """
        # Method implementation ...



    def example_1():
        # Import necessary classes and modules
        # from dependency_container import DependencyContainer, DependencyNotRegisteredError

        # Step 1: Define an Interface and its Implementation
        # ---------------------------------------------------

        # Define a simple interface (or abstract class) for demonstration
        class Communicator:
            def send_message(self, message):
                raise NotImplementedError

        # Define an implementation of the Communicator interface
        class EmailCommunicator(Communicator):
            def send_message(self, message):
                print(f"Sending email: {message}")

        # Step 2: Register the Implementation with DependencyContainer
        # ------------------------------------------------------------

        # Create an instance of the DependencyContainer
        container = DependencyContainer()

        # Register the EmailCommunicator as the implementation for the Communicator interface
        # Here, we specify that EmailCommunicator should be treated as a singleton
        container.register(Communicator, EmailCommunicator)

        # Step 3: Resolve the Dependency and Use It
        # ------------------------------------------

        # Resolve the dependency from the container
        # This will return an instance of EmailCommunicator
        email_communicator = container.resolve(Communicator)

        # Use the resolved communicator instance to send a message
        email_communicator.send_message("Hello World!")

        # Note: The following line will raise an exception if uncommented, 
        # as no implementation is registered for the 'str' type.
        # container.resolve(str)

        # Additional Usage: Registering Non-Singleton Implementations
        # -----------------------------------------------------------

        # Define another implementation of the Communicator interface
        class SMSCommunicator(Communicator):
            def send_message(self, message):
                print(f"Sending SMS: {message}")

        # Register SMSCommunicator as a non-singleton implementation
        container.register(Communicator, SMSCommunicator, singleton=False)

        # Resolving this will give a new instance each time
        sms_communicator = container.resolve(Communicator)
        sms_communicator.send_message("Text Message")


# Example usage:
# container = DependencyContainer()
# container.register(SomeInterface, SomeImplementation)
# instance = container.resolve(SomeInterface)
