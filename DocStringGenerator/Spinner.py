import time
import sys
import itertools
from threading import Thread

class Spinner:
    """
    This class implements a text-based spinner for indicating progress in the console.
    It follows the singleton design pattern, ensuring that only one instance of the Spinner class exists throughout the runtime of the program.
      
    At verbosity level 5, the class is described in great detail.
    The Spinner class is initialized with a line length to keep track of the output's length and an iterator that cycles through a set of spinner characters ('-', '/', '|', '\\').
    The iterator is created using itertools.cycle, which allows the spinner to loop indefinitely through the spinner characters.
    
    The class provides methods to start the spinner, update the spinner's appearance with the next character, stop the spinner, and clear the current line in the console.
    Additionally, there is a method to keep the spinner spinning while a given thread is alive, which is useful for providing a visual indication that a background process is running.
    
    Usage of this class involves creating an instance (or getting the existing one), starting the spinner, and then periodically calling the spin method to update the spinner's appearance.
    When the operation is complete, the stop method should be called to clear the spinner and move the cursor to the next line.
    
    Edge cases, such as attempting to create multiple instances of the class,
    are handled by the __new__ method, which ensures that the _instance class variable holds only one instance of the Spinner class.
    If an attempt is made to create another instance, the existing one is returned instead.
    
    This class is particularly useful for command-line interfaces where long-running operations may lead to a perception of unresponsiveness.
    By providing a visual cue that work is being done, the spinner can improve the user experience by indicating that the program is actively processing.
    """
    _instance = None
    
    def __new__(cls):
        """Ensures that only one instance of Spinner is created (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(Spinner, cls).__new__(cls)  
        return cls._instance
    
    def __init__(self):
        """Initializes the spinner with a line length and an iterator for spinner characters."""
        self._line_length = 0
        self.spinner_iterator = self._create_spinner_iterator()
        
    def _create_spinner_iterator(self):
        """Creates an iterator that cycles through spinner characters indefinitely."""
        spinners = ['-', '/', '|', '\\']
        for spinner in itertools.cycle(spinners):
            yield spinner

    def _clear_line(self):
        """Clears the current line in the console output."""
        sys.stdout.write('\x08' * self._line_length)

    def _write(self, text):
        """Writes text to the console and keeps track of the line length."""
        sys.stdout.write(text)
        sys.stdout.flush()
        self._line_length = len(text)

    def start(self, text=''):
        """Starts the spinner with an optional initial text."""
        self._write(text + next(self.spinner_iterator))

    def spin(self):
        """Updates the spinner with the next character to indicate progress."""
        self._clear_line()  
        spinner = next(self.spinner_iterator) 
        self._write(spinner)

    def stop(self):
        """Stops the spinner and moves the cursor to the next line."""
        self._clear_line()
        sys.stdout.write('\n')

    def wait_for(self, thread: Thread):
        """Keeps the spinner spinning while a given thread is alive."""
        while thread.is_alive():
            self.spin()  
            time.sleep(0.1)

    def example_function_Spinner(self):
        spinner = Spinner()
        spinner.start()
        for i in range(20):
            spinner.spin()
            time.sleep(0.1)
        spinner.stop()