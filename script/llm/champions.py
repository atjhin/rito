from typing import Optional, Set, List

from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage

from .agent import Agent, AgentState
from .constants import Role

class ChampionBot(Agent):
    def __init__(self, role_name: Role, traits: Optional[Set[str]] = None):
        self.traits = traits if traits is not None else set()
        super().__init__(role_name)

    def _init_system_message(self) -> SystemMessage:
        """
        Returns the system prompt defining the champion's personality,
        speaking style, and lore context. This stays consistent for this agent.
        """
        prompt = """
            Imagine you are a script writer pretending to be {champion}, a champion from League of Legends. Your job 
            is to roleplay as {champion} and continue the script as you interact with different champions in the 
            League of Legend universe based on a particular scenario. Below is your lore enclosed with triple backticks.
            ```
            {lore}
            ```

            """
        lore = get_lore(self.role_name) # To be defined
        return SystemMessage(content=prompt.format(champion=self.role_name, lore=lore))

    def _init_human_message(self) -> HumanMessage:
        """
        Returns the human message representing the current turn of dialogue
        or event trigger for the champion.
        """
        prompt = """
        Continue the following script by answering the dialogue and/or acting. FOLLOW THE RULES BELOW
            - Always prefix your response with {champion}: <answer>. 
            - Never remain silent.
            - All act should be enclosed with brackets.
            - If you are unsure, improvise.
            - Follow the script's latest event and improvise.
        """
        return HumanMessage(content=prompt.format(champion=self.role_name))


    def __call__(self, state: AgentState) -> AgentState:
        """
        Invoke call from base agent class 
        """
        # Reuse the base Agent call, to be deleted if no additional change is required.
        return super().__call__(state)


class RoleAssignerBot(Agent):
    def __init__(self, role_name: Role, champions_ls: List[str] = None):
        self.champions_ls = champions_ls
        super().__init__(role_name)

    def _init_system_message(self) -> SystemMessage:
        """
        Returns the system prompt defining ...
        """
        prompt = """
            Imagine you are a **script director** for a League of Legends roleplay.  
            Your sole responsibility is to decide **which champion should speak next OR when to trigger a new event**.  

            Output options: ({champions}), Event)

            Rules:
            - Only output one of the following: a champion's name () or `Event`.  
            - If the **current event is still unfolding**, continue passing turns between champions so they can react.
            - If the current event has been played out by the actors, output `Event` to signal the next event.
            - If the conversation stalls, output `Event` to signal the next event.  
            - Always encourage natural turn-taking between champions.  
            - Never output dialogue, only the next speaker or `Event`.  
            
            ### Example
            Script:
            Event: A sudden storm causes a huge boulder to fall and forces the duel to pause.
            Zed: "Tch. Even the heavens try to interrupt me."
            Shen: "We shall continue this next time Zed. Until then be warned."

            Director output → Event   (because event is complete)
            """
        return SystemMessage(content=prompt.format(champions=', '.join(self.champions_ls)))

    def _init_human_message(self) -> HumanMessage:
        """
        Returns the human message ...
        """
        prompt = """
        Continue the following script by answering the dialogue and/or acting. FOLLOW THE RULES BELOW
            - Always prefix your response with {champion}: <answer>. 
            - Never remain silent.
            - All act should be enclosed with brackets.
            - If you are unsure, improvise.
            - Follow the script's latest event and improvise.
        """
        return HumanMessage(content=prompt.format(champion=self.role_name))


    def __call__(self, state: AgentState) -> AgentState:
        """
        Invoke call from base agent class
        """
        # Reuse the base Agent call, to be deleted if no additional change is required.
        return super().__call__(state, add_to_state=False)


class EventCreatorBot(Agent):
    def __init__(self, role_name: Role, champion_dict: List[str], scenario: str):
        self.champion_dict = champion_dict
        self.scenario = scenario
        super().__init__(role_name)

    def _init_system_message(self) -> SystemMessage:
        """
        Returns the system prompt defining ...
        """
        prompt = """
            Imagine you are an event creator working as a script writer for a League of Legends roleplay. Below
            is a list of dictionary where the name and the personalities for each league of legend champion is provided.
            Champions
            {champion_desc}

            Your job is to expand the starting plot into a **complete storyline** by generating a sequence of engaging events.  
            Each event should naturally follow the previous one, encourage interactions, and stay consistent with the champions'
            personalities and the world of League of Legends.

            Rules:
            - Write the output as a **numbered list of events** (e.g., "Event 1: ...", "Event 2: ...").  
            - Each event should be **1-2 sentences**, around 20-40 words.  
            - Always prefix with "Event X: <description>".  
            - Keep events action-oriented and dynamic (conflict, alliance, discovery, danger, resolution).  
            - Ensure the events form a coherent **beginning → middle → climax → resolution** plot arc.  
            - Never output nothing. If unsure, improvise while staying consistent with the champions and their traits.  
            - Make sure to use information from the scenario provided below.

            Example format:
            Event 1: A sudden storm forces the group into an uneasy alliance.  
            Event 2: Zed suggests a dangerous shortcut, testing Shen's cautious nature.  
            """
        return SystemMessage(content=prompt.format(champion_desc="\n".join(f"{c['champion_name']}: {c['personality']}," for c in self.champion_dict)))

    def _init_human_message(self) -> HumanMessage:
        """
        Returns the human message ...
        """
        prompt = """
        Given the scenario below, use it as a basis to create the list of events. If the scenario is incomplete or missing, complete it with creativity.

        Scenario: 
        {scenario}
        """
        return HumanMessage(content=prompt.format(champion=self.role_name, scenario=self.scenario))


    def __call__(self, state: AgentState) -> AgentState:
        """
        Invoke call from base agent class
        """
        # Reuse the base Agent call, to be deleted if no additional change is required.
        return super().__call__(state, add_to_state=False)


class NovelWriterBot(Agent):
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
        return HumanMessage(content=prompt.format(min_words=self.min_words, max_words=self.max_words))

    def __call__(self, state: AgentState) -> AgentState:
        """
        Invoke call from base agent class
        """
        # Reuse the base Agent call, to be deleted if no additional change is required.
        return super().__call__(state, add_to_state=False)




class SummarizerBot(Agent):
    """
    Summarizes earlier conversation and rewrites state['messages'] as:
      [System(running memory)] + last_k_messages

    Notes:
    - Uses the currently active model registered on this Agent (via register_model / set_active_model).
    - Does NOT append its own AI message to the transcript; instead it compresses and replaces history.
    """

    def __init__(
        self,
        role_name: Role,
        k_keep: int = 8,
    ):
        self.k_keep = max(0, int(k_keep))
        super().__init__(role_name)

    def _init_system_message(self) -> SystemMessage:
        """
        Returns the system prompt defining the memory compression task.
        """
        prompt = """
        You are a memory compressor for a multi-character roleplay. Produce a concise running memory preserving: (1) key plot facts, (2) each speaker's intentions, (3) unresolved threads, and (4) world-state changes and commitments. Keep names consistent. Do not invent new facts. Aim ~120–200 words.
        """
        return SystemMessage(content=prompt)
    
    def _init_human_message(self) -> HumanMessage:
        """
        Returns the human message defining the summarization input format.
        """
        prompt = """
       Given the earlier conversation above, produce a summary with the following Output format:
        1) Short paragraph summary (3–6 sentences).
        2) Bulleted 'open threads' checklist, if any (<=5 bullets).
        """
        return HumanMessage(content=prompt)


    def __call__(self, state: AgentState) -> AgentState:
        """
        Compress older history into a single SystemMessage + keep last k messages.
        Rewrites state['messages'] and returns updated state.
        """
        messages: List[BaseMessage] = state.get("messages", [])  
        if not messages or len(messages) <= self.k_keep:
            # Nothing to compress; pass through unchanged
            return super().__call__(state, add_to_state=False)

        head = messages[:-self.k_keep]
        tail = messages[-self.k_keep:]

        # Get active LLM from the Agent's registry
        if self._active_model_key is None:
            raise RuntimeError("SummarizerBot: no active model set. Call register_model() and set_active_model().")
        llm = self._models[self._active_model_key].get_llm()  

        summary = llm.invoke([self._system_message, *head, self._human_message])

        new_state: AgentState = {**state, "messages": summary + tail}
        return new_state
        