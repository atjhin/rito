from ..entities.StoryBoard import StoryBoard

def create_story(data):
    story_board = StoryBoard(
        character1=data['character1'],
        character2=data['character2'],
        context=data.get('context', '')
    )
    # have to call on the program that generates the story here
    print(f"Creating story between {story_board.character1} and {story_board.character2} with context: {story_board.context}")
    return story_board.get_json()