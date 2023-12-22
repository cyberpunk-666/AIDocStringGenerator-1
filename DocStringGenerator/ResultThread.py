import threading

class ResultThread(threading.Thread):
    """ResultThread is a singleton subclass of threading.Thread that ensures only one instance of the thread is created throughout the lifetime of a program. It overrides the `__new__` method to enforce the singleton pattern, ensuring that any attempt to instantiate ResultThread will always return the same object. The `__init__` method initializes the thread and sets a `result` attribute to `None`, which is intended to store the result of the thread's target function once it has finished executing. The `run` method is overridden to execute the thread's target function and store the result in the `result` attribute.\n\nThis class is extremely detailed, providing in-depth explanations of its methods, including the singleton pattern implementation, thread initialization, and result storage mechanism. It also covers the usage of private attributes like `_initialized` to track whether the instance has been initialized, and the use of a lock (`_instance_lock`) to ensure thread-safe instantiation of the singleton instance.\n\nUsage examples and edge cases are provided to help users understand how to properly utilize this class in a multithreaded environment."""
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super(ResultThread, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, *args, **kwargs):
        super(ResultThread, self).__init__(*args, **kwargs)
        self.result = None

    def run(self):
        """Executes the thread's target function and stores the result."""
        if self._target is not None:
            self.result = self._target(*self._args, **self._kwargs)