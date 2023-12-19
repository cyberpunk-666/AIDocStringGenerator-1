import threading

class ResultThread(threading.Thread):
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
        if self._target is not None:
            self.result = self._target(*self._args, **self._kwargs)