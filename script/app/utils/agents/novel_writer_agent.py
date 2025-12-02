from typing import List
from app.utils.constants.roles import Role
from app.utils.agents.agent import Agent
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from app.utils.data_models.agent_state import AgentState


class NovelWriterAgent(Agent):
    def __init__(self, role_name: Role, min_words: int, max_words: int):
        self.min_words = min_words
        self.max_words = max_words
        super().__init__(role_name)

    def _init_system_message(self) -> SystemMessage:
        """
        Returns the system prompt defining the persona and strict writing guidelines.
        """
        prompt = """
            You are a bestselling fiction author and ruthless literary editor. Your task is to transform a raw, script-like outline (AI message outputs) into a high-quality, immersive novel chapter.

            **Your Objective:**
            Synthesize the fragmented input into a seamless narrative. Do not just "stitch" the lines together; Reimagine them.

            **Critical Writing Guidelines:**
            1.  **Show, Don't Tell:** Do not summarize emotions (e.g., "She felt sad"). Instead, describe the physical sensations, the atmosphere, and the body language that convey that emotion.
            2.  **Deep Point of View:** Ground the narrative in the characters' immediate experience. Include their internal thoughts, sensory perceptions (smell, sound, touch), and visceral reactions.
            3.  **Prose Quality (NO PURPLE PROSE):**
                - Avoid "Thesaurus stuffing." Do not use complex words (e.g., "rapacious," "abscond," "cacophony") when simple, impactful words will do.
                - Prioritize clarity and flow over flowery descriptions.
                - Vary sentence length. Mix short, punchy sentences with longer, flowing ones to control pacing.
            4.  **Narrative Flow:**
                - Bridge gaps between dialogue with action or introspection.
                - Ensure a clear beginning, rising action, and resolution.

            **Formatting Rules:**
            - Output **only** the story text.
            - No "AI:" or "Human:" tags.
            - No bullet points or lists.
            - Use standard novel formatting (double quotes for dialogue).
        """
        return SystemMessage(content=prompt)

    def _init_human_message(self) -> HumanMessage:
        """
        Returns the human message with length constraints.
        """
        prompt = """
            Based on the script provided above, write a compelling novel chapter.
            
            Target Length: Approximately {min_words} to {max_words} words.
            Focus: Maintain high readability and distinct character voices.
        """
        return HumanMessage(
            content=prompt.format(min_words=self.min_words, max_words=self.max_words)
        )

    def __call__(self, state: AgentState) -> AgentState:
        print("\n Novel Writer called \n")
        return super().__call__(state, add_to_state=False)