import os
from typing import List, Dict, Tuple, Optional

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.chat_history import InMemoryChatMessageHistory, BaseChatMessageHistory
from langchain_core.messages import trim_messages
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from constants import Comm


class MultiRoleChat:
    """
    Orchestrates multi-role conversations with:
      - one shared memory
      - role-specific prompts that force a 'Role: ' prefix
      - message trimming or summarization to respect a token budget
      - communication logic (sequential or random)

    Usage:
        chat = MultiRoleChat(roles=["Ezreal"], temperature=1.0)
        chat.add_role("Lux") # add Lux to the scene
        chat.create_roles()  # builds agents for all roles
        transcript = chat.communicate(
            init_prompt="You are at Summoner's Rift. You meet each other in the same team.",
            max_turns=4,
            comm_method=Comm.SEQ
        )
        for speaker, text in transcript:
            print(f"{speaker}: {text}")
    """

    def __init__(
        self, roles: Optional[List[str]] = None, *, temperature: float = 1.0,
        model_name: str = "gemini-2.5-flash",
        token_limit_history: int = 500,
        session_id: str = "shared",
        model_provider: str = "google_genai",
        api_key_env: str = "GEMINI_API_KEY",
    ) -> None:
        
        load_dotenv(dotenv_path=find_dotenv())

        self.roles: List[str] = roles or []
        self.temperature = temperature
        self.model_name = model_name
        self.model_provider = model_provider
        self.token_limit = token_limit_history
        self.session_id = session_id

        api_key = os.getenv(api_key_env)
        if not api_key:
            raise RuntimeError(
                f"{api_key_env} not set. Ensure your .env contains {api_key_env}=..."
            )

        # Single model instance is fine for both token counting and inference.
        self.model = init_chat_model(
            model=self.model_name,
            api_key=api_key,
            model_provider=self.model_provider,
            temperature=self.temperature,
        )

        # Shared memory for all roles
        self._shared_history = InMemoryChatMessageHistory()

        def _get_session_history(_: str) -> BaseChatMessageHistory:
            return self._shared_history

        self._get_session_history = _get_session_history

        # Trimmer uses the model’s tokenizer for counting
        self.trimmer = trim_messages(
            max_tokens=self.token_limit,
            strategy="last",
            token_counter=self.model,
            include_system=True,
            allow_partial=False,
        )

        # Built agents live here
        self.agents: Dict[str, RunnableWithMessageHistory] = {}

    # ---------- Public API ----------

    def add_role(self, new_role: str) -> None:
        """Add more roles to the scene that can be later created as an agent"""
        self.roles.append(new_role)

    def create_role(self, role_name: str) -> None:
        """Create and store a RunnableWithMessageHistory for a single role."""
        self.agents[role_name] = self._build_role_agent(role_name)
        if role_name not in self.roles:
            self.roles.append(role_name)

    def create_roles(self, roles: Optional[List[str]] = None) -> None:
        """Create agents for all given roles (or for self.roles if None)."""
        target_roles = roles or self.roles
        for r in target_roles:
            self.create_role(r)

    def communicate(
        self,
        *,
        init_prompt: str,
        max_turns: int = 4,
        comm_method: Comm = Comm.SEQ,
        echo_print: bool = False,
    ) -> List[Tuple[str, str]]:
        """
        Run a conversation and return the transcript as [(role, reply_text), ...].

        - Comm.SEQ: Each turn, roles speak one after another using the previous
          message as context. All share a single session_id memory.
        """
        if not self.roles:
            raise ValueError("No roles defined. Call create_role(s) first.")
        missing_agents = [r for r in self.roles if r not in self.agents]
        if missing_agents:
            raise ValueError(f"Agents not built for roles: {missing_agents}. Call create_role(s) first.")

        shared_cfg = {"configurable": {"session_id": self.session_id}}
        transcript: List[Tuple[str, str]] = []

        if comm_method != Comm.SEQ:
            # implement more communication method later...
            raise NotImplementedError("Only Comm.SEQ is implemented in this wrapper.")

        turn = 0
        last_msg = init_prompt

        while turn < max_turns:
            for idx, role in enumerate(self.roles):
                if turn == 0 and idx == 0:
                    prompt_input = f"Given '{init_prompt}', what would you say given who you are?"
                elif idx == 0:
                    prompt_input = f"{self.roles[-1]} said: {last_msg}\nGiven your role, what is your response?"
                else:
                    prompt_input = f"{self.roles[idx - 1]} said: {last_msg}\nGiven your role, what is your response?"

                reply: str = self.agents[role].invoke(
                    {"input": prompt_input, "speaker": role},
                    config=shared_cfg,
                )

                # Enforce the "Role: " prefix contract downstream just in case
                if not reply.startswith(f"{role}: "):
                    reply = f"{role}: {reply}"

                if echo_print:
                    print(reply, "\n")
                else:
                    if idx == len(self.roles) - 1:
                        print(f"Progress: {int(turn + 1)} turn passed\n")

                transcript.append((role, reply))
                last_msg = reply
            turn += 1

        return transcript
    
    def build_story(
            self, 
            *, 
            init_prompt: str,
            max_turns: int = 4,
            comm_method: Comm = Comm.SEQ,
            verbose_conversation: bool = False,
            temperature: float = 1.0, 
            model_name: str = "gemini-2.5-flash", 
            model_provider: str = "google_genai", 
            api_key_env: str = "GEMINI_API_KEY",
            story_prompt: str = "You are a story teller", 
            instruction: Optional[str] = None) -> None:
        """
        Initiate the communication between the roles and 
        create a story from another model based on the conversation.
        """
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise RuntimeError(
                f"{api_key_env} not set. Ensure your .env contains {api_key_env}=..."
            )
        story_teller = init_chat_model(model=model_name, 
                                       model_provider=model_provider, 
                                       api_key=api_key, 
                                       temperature=temperature)
        transcript = self.communicate(init_prompt=init_prompt, 
                         max_turns=max_turns, 
                         comm_method=comm_method, 
                         echo_print=verbose_conversation)
        conversation_text = "\n".join(f"{role}: {msg}" for role, msg in transcript)
        
        if instruction is not None:
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"{story_prompt}"),
                ("human",
                "Here is the conversation:\n\n{conversation}\n\n"
                "Please create a story from the entire conversation.\n"
                "Additional instruction: {instruction}")
            ])
            chain = prompt | story_teller | StrOutputParser()
            story = chain.invoke({
                "conversation": conversation_text,
                "instruction": instruction
            })
        else:
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"{story_prompt}"),
                ("human",
                "Here is the conversation:\n\n{conversation}\n\n"
                "Please create a story from the entire conversation.")
            ])
            chain = prompt | story_teller | StrOutputParser()
            story = chain.invoke({
                "conversation": conversation_text,
                "instruction": instruction
            })
        print(story)
        return story

    def _build_role_agent(self, role_name: str) -> RunnableWithMessageHistory:
        prompt = self._role_prompt(role_name)
        chain = prompt | self.trimmer | self.model | StrOutputParser()
        return RunnableWithMessageHistory(
            runnable=chain,
            get_session_history=self._get_session_history,
            input_messages_key="input",
            history_messages_key="history",
        )

    @staticmethod
    def _role_prompt(role_name: str) -> ChatPromptTemplate:
        system_msg = (
            f"You are '{role_name}'. Stay strictly in character as {role_name}. "
            f"Never speak as the other role. "
            f"Always begin your reply with exactly '{role_name}: ' (role name, colon, space)."
        )
        return ChatPromptTemplate.from_messages(
            [
                ("system", system_msg),
                MessagesPlaceholder("history"),
                ("human", "[{speaker}] {input}"),
            ]
        )


# -------- Example script usage --------
if __name__ == "__main__":
    roles = ["Ezreal", "Lux"]
    chat = MultiRoleChat(roles=roles, temperature=1.0, token_limit_history=500)
    chat.create_roles()  # builds agents for Ezreal and Lux
    convo = chat.build_story(
        init_prompt="You are at Summoner's Rift. You meet each other in the same team.",
        max_turns=4,
        comm_method=Comm.SEQ,
        verbose_conversation=False,  # set False to suppress printing
    )