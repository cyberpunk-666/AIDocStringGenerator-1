import threading

class ResultThread(threading.Thread):    
    def __init__(self, target=None, *args, **kwargs):
        super(ResultThread, self).__init__(*args, **kwargs)
        self.result = None
        self._custom_target = target
        self._custom_args = args
        self._custom_kwargs = kwargs

    def run(self):
        """Executes the thread's target function and stores the result."""
        if self._custom_target is not None:
            self.result = self._custom_target(*self._custom_args, **self._custom_kwargs)
