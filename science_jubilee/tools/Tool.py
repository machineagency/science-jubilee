class ToolStateError(Exception):
    """Raise this error if the tool is in the wrong state to perform such a command."""
    pass


class ToolConfigurationError(Exception):
    """Raise this error if there is something wrong with how the tool is configured"""
    pass


class Tool:
    #TODO: Is this init supposed to take a machine? 
    def __init__(self, index, name, **kwargs):
        self._machine = None
        if not isinstance(index, int) or not isinstance(name, str):
            raise ToolConfigurationError("Incorrect usage: load_tool(<tool_number>, <name>, **kwargs)")
        self.index = index
        self.name = name
        for k,v in kwargs.items():
            setattr(self, k, v )

    def post_load(self):
        """Run any code after tool has been associated with the machine."""
        pass

    #TODO:
    #add a park tool method that every tool config can define to do things that need to be done pre or post parking
    #ex: make sure pipette has dropped tips before parking

    