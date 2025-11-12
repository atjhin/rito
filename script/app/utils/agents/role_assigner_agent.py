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
        """
        champions = ", ".join(self.champions_list)
        prompt = f"""
        You are directing a cinematic League of Legends scene.

        TASK
        Choose who speaks next OR trigger an Event.

        OUTPUT (exact, single line)
        <Name or Event> || <one short sentence reason>

        NAMES (STRICT, SINGLE-TOKEN)
        Use EXACT tokens from: {champions} OR Event.
        Do not invent variants. If unsure, output Event.

        STYLE
        - No punctuation/quotes before the first token
        - Do not include extra '||' in the reason
        - No colons/semicolons
        - Reason is 1 sentence
        - For Event, write a scene-level reason (do NOT start with He/She/They/<Name>)

        PACE
        - After an Event → allow only few champion lines
        - If previous Event has been resolved → MUST output Event
        - Never output Event twice in a row
        - Alternate speakers unless clearly mid-thought or direct reply

        DECISION ORDER
        1) If last output was Event → Do not output Event
        2) Strongly Favour to alternate speaker.
        3) When uncertain → choose Event.
        """
        return SystemMessage(content=prompt)

    def _init_human_message(self) -> HumanMessage:
        """
        Minimal, strict, with Event-first bias when uncertain.
        """
        champions = ", ".join(self.champions_list)
        prompt = f"""
        Choose the next speaker or Event.

        Format (exact):
        <Name or Event> || <one sentence reason>

        Use EXACT tokens from: {champions} OR Event.
        Do not output variants. If unsure, choose Event.
        If choosing the same speaker as the last spoken inevitably, include the word "reasonable" to reason.

        Examples:
        Zed || He answers the challenge.
        Event || The scene shifts to a tense pause.

        RULES
        No punctuation before the first token. No colons/semicolons. No extra '||'.
        If Event, use a scene-level reason (not He/She/They/<Name>).
        Favor frequent Event beats; keep the cadence tight.
        Avoid choosing the same speaker as the last spoken.
        Every reason should be unique and very different from the past.
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
