from typing import List, Tuple, Optional
from app.utils.constants.roles import Role
from app.utils.agents.agent import Agent
from langchain_core.messages import SystemMessage, HumanMessage
from app.utils.data_models.agent_state import AgentState

# ---------- Strict, simple parsers (single-token names only) ----------

def _parse_with_delimiter(text: str) -> Optional[Tuple[str, str]]:
    """
    Preferred parsing: '<Name or Event> || <reason>'.
    """
    if "||" not in text:
        return None
    left, right = text.split("||", 1)
    return left.strip(), right.strip()

def _count_since_last_event(history: List[str]) -> int:
    cnt = 0
    for x in reversed(history):
        if x == "Event":
            break
        cnt += 1
    return cnt

def _choose_alternate(champions: List[str], last_champ: Optional[str]) -> str:
    if not champions:
        return "Event"
    if last_champ and last_champ in champions:
        for c in champions:
            if c != last_champ:
                return c
    return champions[0]

# ---------- Agent ----------

class RoleAssignerAgent(Agent):
    def __init__(self, role_name: Role, champions_list: List[str] = None):
        self.champions_list = champions_list
        super().__init__(role_name)

    def _init_system_message(self) -> SystemMessage:
        """
        Strong Event bias: 4 champion lines max after Event
        Includes strict delimiter enforcement to prevent parsing errors.
        """
        champions = ", ".join(self.champions_list)
        prompt = f"""
        You are directing a cinematic League of Legends scene.

        ### AVAILABLE ROLES (Exact Spelling Required)
        {champions}
        Event

        ### PACING LOGIC
        1. After an 'Event', allow only a few champion lines.
        2. If the previous 'Event' has been resolved -> MUST output 'Event'.
        3. Never output 'Event' twice in a row.
        4. Alternate speakers unless clearly mid-thought or direct reply.
        5. DECISION: If last output was Event -> Do not output Event. When uncertain -> choose Event.

        ### CRITICAL OUTPUT FORMAT
        You must output exactly ONE line containing the double-pipe delimiter "||".
        
        Syntax:
        <Name or Event> || <Reason>

        ### STRICT FORMATTING RULES
        1. The "||" delimiter is MANDATORY. Without it, the system crashes.
        2. Do not use colons (:), hyphens (-), or arrows (->) as separators.
        3. <Name> must be exactly one of the Available Roles.
        4. <Reason> must be one short sentence.
        5. No punctuation before the name. No markdown.
        
        If you are completely unsure what to generate, output:
        Event || Scene transition required.
        """
        return SystemMessage(content=prompt)

    def _init_human_message(self) -> HumanMessage:
        """
        Minimal, strict, with Event-first bias when uncertain.
        Reinforces the delimiter requirement.
        """
        champions = ", ".join(self.champions_list)
        # Create a dynamic example based on the actual list to help the LLM
        example_champ = self.champions_list[0] if self.champions_list else "ChampionName"
        
        prompt = f"""
        Determine the next turn.

        Valid Options: {champions}, Event

        REQUIRED FORMAT:
        [Option] || [Reason]

        Examples:
        {example_champ} || They step forward to answer.
        Event || A loud explosion interrupts the conversation.

        CONSTRAINT:
        You MUST include the "||" characters in your response.
        If choosing the same speaker as the last turn, the reason must include the word "reasonable".

        Output your decision now:
        """
        return HumanMessage(content=prompt)

    def __call__(self, state: AgentState) -> AgentState:
        """
        Parse pick+reason, then enforce fast pacing:
          - No consecutive Events.
        Stores ONLY exact champion tokens from champions_list OR 'Event'.
        Deviation is coerced to 'Event'.
        """
        full_response = super().__call__(state, add_to_state=False)["ai_response"].content.strip()

        # Parse
        parsed = _parse_with_delimiter(full_response)
        if parsed is not None:
            pick, reason = parsed
            pick = pick.strip()
            pick = pick.replace(" ", "")
        else:
            print("delimiter not applied correctly")
            exit(-1)


        history: List[str] = state.get("next_bot", [])
        last = history[-1] if history else None
        since = _count_since_last_event(history)

        # --- Enforce pacing overrides ---

        # 1) No consecutive Events
        if last == "Event" and pick == "Event":
            last_champ = next((x for x in reversed(history) if x != "Event"), None)
            pick = _choose_alternate(self.champions_list, last_champ)
            reason = "Forced Champion's Name"

        # 2) Force Event after 2 champion lines since last Event
        if since >= 4 and pick != "Event":
            pick = "Event"
            reason = "Forced Event"
        
        if last == pick and "reasonable" not in reason and last != "Event":
            pick = _choose_alternate(self.champions_list, last)
            reason = "Forced to Alternate"


        # Store
        state.setdefault("next_bot", []).append(pick)
        state.setdefault("reason_log", []).append(reason)
        print(f"[RoleAssigner] Next: {pick} | Reason: {reason}")

        return state
