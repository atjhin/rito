class StoryBoard:
    def __init__(self, character1: str, character2: str, context: str = ""):
        self.character1 = character1
        self.character2 = character2
        self.context = context

    def get_json(self):
        return {
            "character1": self.character1,
            "character2": self.character2,
            "context": self.context
        }