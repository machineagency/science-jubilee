from science_jubilee.tools.Tool import Tool, ToolStateError


class Loop(Tool):
    def __init__(self, index, name):
        super().__init__(index, name)
