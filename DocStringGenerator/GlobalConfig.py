from DocStringGenerator.DependencyContainer import DependencyContainer, Scope
dependencies = DependencyContainer()

class GlobalConfig:
    def __init__(self):
        self.mode: str = "cli"

dependencies.register(GlobalConfig, GlobalConfig, Scope.SINGLETON)