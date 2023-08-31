from .Tool import Tool, ToolStateError


class Loop(Tool):
    def __init__(self, index, name, details):
        super().__init__(index, name, details)
