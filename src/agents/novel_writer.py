from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.base import Agent
from src.schemas.roles import Role
from src.schemas.state import AgentState


class NovelWriterAgent(Agent):
    """Agent that transforms the script into a polished narrative."""
    
    def __init__(self, role_name: Role, min_words: int, max_words: int):
        self.min_words = min_words
        self.max_words = max_words
        super().__init__(role_name)

    def _init_system_message(self) -> SystemMessage:
        """Universal narrative prompt focused on 'Modern Commercial Fiction' standards."""
        prompt = """
        You are a bestselling author of modern fantasy fiction. Your task is to transform a raw AI script into a gripping, cinematic novel chapter.

        **THE 4 PILLARS OF WRITING (Strict Adherence Required):**

        1. **AUTHENTIC DIALOGUE (The "Human" Test)**
           - Dialogue must sound spoken, not written.
           - Use contractions, interruptions, and fragments.
           - **Crucial:** Characters must sound distinct based on their personality in the script. A monster sounds primal; a trickster sounds sly; a soldier sounds disciplined.
           - *Avoid:* "I am extremely frightened." -> *Use:* "I... I can't do this."
           - Use everyday language more often.

        2. **IMMERSIVE NARRATION (Show, Don't Tell)**
           - Never state an emotion directly (e.g., "He was angry").
           - Describe the physical reaction: the clenched jaw, the rising temperature, the sharp silence.
           - Ground the scene in sensory details: textures, smells, and lighting.

        3. **PROSE HYGIENE (No "Purple Prose")**
           - Do not use a thesaurus. Simple, impactful words are better than complex, obscure ones.
           - Do not overuse the same words.
           - Eliminate adverbs where possible (e.g., instead of "ran quickly", use "sprinted").

        4. **NARRATIVE FLOW**
           - You are the director. Bridge the gaps between script lines with meaningful action or introspection.
           - Ensure the pacing matches the scene (fast sentences for action, slower flow for rest).

        **FORMATTING:**
        - Do not use em dash.
        - Output ONLY the story text.
        - Standard novel formatting (double quotes for dialogue).
        - No markdown tags, no 'AI:' labels.
        """
        return SystemMessage(content=prompt)

    def _init_human_message(self) -> HumanMessage:
        """Simple, length-constrained trigger."""
        prompt = """
        Using the script provided above, write the story chapter.

        **Constraints:**
        - Length: {min_words} to {max_words} words.
        - Tone: Engaging, polished, and character-driven.
        """
        return HumanMessage(
            content=prompt.format(min_words=self.min_words, max_words=self.max_words)
        )

    def __call__(self, state: AgentState) -> AgentState:
        """Invoke the novel writer."""
        print("\n Novel Writer called \n")
        return super().__call__(state, add_to_state=False)

