from typing import Optional
import threading
from typing import Type, Callable, Dict, Tuple

class DependencyNotRegisteredError(KeyError):
    """Exception raised when a dependency is not registered."""
    pass

class DependencyContainer:
    _instance: Optional['DependencyContainer'] = None
    _lock = threading.Lock()


    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DependencyContainer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_is_initialized') or not self._is_initialized:
            self.dependencies: Dict[Type, Tuple[Callable, bool]] = {}
            self._is_initialized = True

    def register(self, interface, implementation, singleton=True):
        self.dependencies[interface] = (implementation, singleton)

    def resolve(self, interface, *args, **kwargs):      
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




    def example_1(self):
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

