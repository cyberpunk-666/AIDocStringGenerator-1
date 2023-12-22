class Test:
    """Class to contain test functions."""
    def func1(self, x, y):
        """Adds two numbers together."""
        return x + y
        
    def func2(self, x):
        """Checks sign of a number."""
        if x > 0:
            return "positive"
        else: 
            return "negative"

    def func3(self, items):
        """Sums the values in a list."""
        total = 0
        for item in items:
            total += item
        return total
        
test = Test()
print(test.func1(1, 2))
print(test.func2(-5)) 
print(test.func3([1, 2, 3]))