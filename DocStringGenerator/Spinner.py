import time
import sys
import itertools
from threading import Thread

class Spinner:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Spinner, cls).__new__(cls)  
        return cls._instance
    
    def __init__(self):
        self._line_length = 0
        self.spinner_iterator = self._create_spinner_iterator()
        
    def _create_spinner_iterator(self):
        spinners = ['-', '/', '|', '\\']
        for spinner in itertools.cycle(spinners):
            yield spinner

    def _clear_line(self):
        sys.stdout.write('\x08' * self._line_length)

    def _write(self, text):
        sys.stdout.write(text)
        sys.stdout.flush()
        self._line_length = len(text)

    def start(self, text=''):
        self._write(text + next(self.spinner_iterator))

    def spin(self):
        self._clear_line()  
        spinner = next(self.spinner_iterator) 
        self._write(spinner)

    def stop(self):
        self._clear_line()
        sys.stdout.write('\n')

    def wait_for(self, thread: Thread):
        while thread.is_alive():
            self.spin()  
            time.sleep(0.1)