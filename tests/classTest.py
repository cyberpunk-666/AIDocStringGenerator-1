class Test:
    def func1(self, x, y):
        return x + y
        
    def func2(self, x):
        if x > 0:
            return "positive"
        else: 
            return "negative"

    def func3(self, items):
        total = 0
        for item in items:
            total += item
        return total
        
test = Test()
print(test.func1(1, 2))
print(test.func2(-5)) 
print(test.func3([1, 2, 3]))