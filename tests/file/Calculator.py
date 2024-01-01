class Calculator:
    """A simple class that performs basic arithmetic operations."""

    def add(self, a, b):
        """Adds two numbers together and returns the result."""
        return a + b

    def subtract(self, a, b):
        """Subtracts two numbers and returns the result."""
        return a - b

    def multiply(self, a, b):
        """Multiplies two numbers together and returns the result."""
        return a * b

    def divide(self, a, b):
        """Divides two numbers and returns the result. Raises a ValueError if the divisor is zero."""
        if b == 0:
            raise ValueError('Cannot divide by zero')
        return a / b

    def example_function_Calculator(self):
        calculator = Calculator()
        result = calculator.add(1, 2)
        print(result)  # Prints 3