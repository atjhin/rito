from app import supabase


def create_story(data):
    # print("Creating story with data:", data)
    # story_board = StoryBoard(
    #     character1=data['character1'],
    #     character2=data['character2'],
    #     context=data.get('context', '')
    # )
    # # have to call on the program that generates the story here
    # print(f"Creating story between {story_board.character1} and {story_board.character2} with context: {story_board.context}")
    # return data
    character1 = data.get("character1")
    character2 = data.get("character2")
    context = data.get("context", "")

    response = supabase.table("story_board").insert({
        "character1": character1,
        "character2": character2,
        "context": context
    }).execute()

    return response.data