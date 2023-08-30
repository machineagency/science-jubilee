class ToolStateError(Exception):
    """Raise this error if the tool is in the wrong state to perform such a command."""
    pass

class ToolConfigurationError(Exception):
    """Raise this error if there is something wrong with how the tool is configured"""
    pass

class Tool:
    def __init__(self, machine, index, name, **kwargs):
        self._machine = machine
        self.index = index
        self.name = name
        self.is_active_tool = False
        for k,v in kwargs.items():
            setattr(self, k, v )
    