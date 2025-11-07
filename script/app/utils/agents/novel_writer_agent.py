from typing import List
from app.utils.constants.constants import Role
from app.utils.agents.agent import Agent
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from app.utils.data_models.agent_state import AgentState


class NovelWriterAgent(Agent):
    def __init__(self, role_name: Role, min_words: int, max_words: int):
        self.min_words = min_words
        self.max_words = max_words
        super().__init__(role_name)

    def _init_system_message(self) -> SystemMessage:
        # Possible improvement is to include writer type. e.g. Copy the style of a particular writer
        """
        Returns the system prompt defining ...
        """
        prompt = """
            Imagine you are a novelist and literary editor working to transform a screenplay-like script into a polished, immersive novel.
            The script is provided in the form of AI message outputs, representing snippets of dialogue, narration, stage directions, and current event.

            Your job is to weave these fragmented AI message outputs into a cohesive and compelling novel chapter that reads naturally, with strong prose, pacing, and emotional resonance.

            Rules:
            - Treat the AI message outputs as your source script — they contain the intended content, tone, and structure.
            - Expand, merge, and refine the messages into complete paragraphs of novel-quality writing.
            - Preserve all core events, emotions, and dialogues, but rewrite them in elegant literary prose.
            - Use vivid descriptions, natural dialogue, and smooth transitions between scenes.
            - Maintain consistent point of view, tense, and narrative voice throughout.
            - Create a clear beginning → buildup → climax → resolution flow.
            - If context is missing between messages, infer or creatively bridge scenes while staying consistent with prior tone and logic.
            - Do not include message tags like "AI:" or "Human:".
            - Output only the final novel text, formatted in full paragraphs — no bullet points, lists, or event markers.
            - Never output nothing. If unsure, write a plausible and coherent continuation that feels authentic to the story.
            """
        return SystemMessage(content=prompt)

    def _init_human_message(self) -> HumanMessage:
        """
        Returns the human message ...
        """
        prompt = """
            Given the script above, output a novel in about {min_words} to {max_words} words
        """
        return HumanMessage(
            content=prompt.format(min_words=self.min_words, max_words=self.max_words)
        )

    def __call__(self, state: AgentState) -> AgentState:
        """
        Invoke call from base agent class
        """
        # Reuse the base Agent call, to be deleted if no additional change is required.
        print("\n Novel Writer called \n")
        return super().__call__(state, add_to_state=False)
