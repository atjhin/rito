from app.utils.core.agent_factory import AgentFactory
from app.utils.data_models.agent_creation_item import (
    ChampionAgentConfig,
    EventCreatorAgentConfig,
    NovelWriterAgentConfig,
    RoleAssignerAgentConfig,
    SummarizerAgentConfig,
)
from langgraph.graph import StateGraph, END
from app.utils.constants.roles import Role
from app.utils.constants.models import ModelChoices
from app.utils.constants.path_config import Config
from app.utils.data_models.agent_state import AgentState
from langchain_core.messages import AIMessage
from app.utils.data_models.story_teller_item import StoryTellerItem
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
import pprint 
import sqlite3
import os
from collections import defaultdict

class RequestCounter(BaseCallbackHandler):
    def __init__(self):
        # Master storage for active run contexts
        self._run_context = {} 
        self._seen_run_ids = set()
        
        # Stat Buckets
        self.stats = {
            "total": {"req": 0, "in": 0, "out": 0, "sum": 0},
            "by_model": defaultdict(lambda: {"req": 0, "in": 0, "out": 0, "sum": 0}),
            "by_role": defaultdict(lambda: {"req": 0, "in": 0, "out": 0, "sum": 0}),
            "by_provider": defaultdict(lambda: {"req": 0, "in": 0, "out": 0, "sum": 0}),
        }

    def _get_provider(self, model_name: str) -> str:
        model_name = model_name.lower()
        if "gemini" in model_name: return "Google"
        if "gpt" in model_name or "o1-" in model_name: return "OpenAI"
        if "grok" in model_name: return "XAI"
        return "Other"

    def on_chat_model_start(self, serialized, messages, *, run_id, metadata=None, **kwargs):
        if run_id in self._seen_run_ids: return
        self._seen_run_ids.add(run_id)

        # 1. Identify Model
        model = "unknown_model"
        if kwargs.get('invocation_params') and 'model' in kwargs['invocation_params']:
             model = kwargs['invocation_params']['model'] # Common for OpenAI/Gemini
        elif serialized and 'kwargs' in serialized and 'model_name' in serialized['kwargs']:
             model = serialized['kwargs']['model_name']
        
        # 2. Identify Role (Node Name)
        # LangGraph injects the node name into metadata
        role = metadata.get("langgraph_node", "Unknown_Node") if metadata else "Unknown_Node"

        # 3. Store Context for when the End event fires
        self._run_context[run_id] = {
            "model": model,
            "role": role,
            "provider": self._get_provider(model)
        }

    def on_llm_start(self, serialized, prompts, *, run_id, metadata=None, **kwargs):
        # Fallback for non-chat models
        self.on_chat_model_start(serialized, [], run_id=run_id, metadata=metadata, **kwargs)

    def on_chat_model_end(self, outputs: LLMResult, *, run_id, **kwargs):
        self._process_end(outputs, run_id)

    def on_llm_end(self, response: LLMResult, *, run_id, **kwargs):
        self._process_end(response, run_id)

    def _process_end(self, outputs: LLMResult, run_id):
        # Retrieve context
        ctx = self._run_context.get(run_id, {"model": "unknown", "role": "unknown", "provider": "unknown"})
        
        # Calculate tokens using the robust strategy
        in_t, out_t, total_t = self._extract_tokens(outputs)

        # Update Statistics
        self._update_bucket(self.stats["total"], 1, in_t, out_t, total_t)
        self._update_bucket(self.stats["by_model"][ctx["model"]], 1, in_t, out_t, total_t)
        self._update_bucket(self.stats["by_role"][ctx["role"]], 1, in_t, out_t, total_t)
        self._update_bucket(self.stats["by_provider"][ctx["provider"]], 1, in_t, out_t, total_t)

    def _update_bucket(self, bucket, req, in_t, out_t, total_t):
        bucket["req"] += req
        bucket["in"] += in_t
        bucket["out"] += out_t
        bucket["sum"] += total_t

    def _extract_tokens(self, outputs: LLMResult):
        """Robust extraction logic returning (input, output, total) tuple"""
        i, o, t = 0, 0, 0
        found_usage = None
        
        # ... (Strategy 1 & 2 logic remains the same) ...
        # Ensure you capture the usage object like before
        if outputs.llm_output and 'token_usage' in outputs.llm_output:
            found_usage = outputs.llm_output['token_usage']
        elif outputs.generations:
            gen = outputs.generations[0][0]
            # ... existing checks ...
            if hasattr(gen, 'message') and getattr(gen.message, 'usage_metadata', None):
                 found_usage = gen.message.usage_metadata

        if found_usage:
            try:
                # 1. Google Object Style
                if hasattr(found_usage, 'prompt_token_count'): 
                    i, o, t = found_usage.prompt_token_count, found_usage.candidates_token_count, found_usage.total_token_count
                
                elif isinstance(found_usage, dict):
                    # 2. OpenAI / Standard Keys (The Fix is adding prompt_tokens/completion_tokens)
                    i = (found_usage.get('promptTokenCount') or 
                         found_usage.get('input_tokens') or 
                         found_usage.get('prompt_token_count') or 
                         found_usage.get('prompt_tokens') or 0) # <--- Added prompt_tokens

                    o = (found_usage.get('candidatesTokenCount') or 
                         found_usage.get('output_tokens') or 
                         found_usage.get('candidates_token_count') or 
                         found_usage.get('completion_tokens') or 0) # <--- Added completion_tokens

                    t = (found_usage.get('totalTokenCount') or 
                         found_usage.get('total_tokens') or 
                         found_usage.get('total_token_count') or 0)
            except:
                pass
        
        return i, o, t

    def __repr__(self):
        def print_table(title, data_dict):
            res = [f"\n--- {title} ---"]
            header = f"{'Name':<25} | {'Reqs':<5} | {'Input':<8} | {'Output':<8} | {'Total':<8}"
            res.append(header)
            res.append("-" * len(header))
            for name, d in data_dict.items():
                res.append(f"{name:<25} | {d['req']:<5} | {d['in']:<8} | {d['out']:<8} | {d['sum']:<8}")
            return "\n".join(res)

        output = []
        output.append("="*60)
        output.append(" TOKEN USAGE REPORT ")
        output.append("="*60)
        output.append(f"TOTAL REQUESTS: {self.stats['total']['req']}")
        output.append(f"TOTAL TOKENS:   {self.stats['total']['sum']} (In: {self.stats['total']['in']}, Out: {self.stats['total']['out']})")
        
        output.append(print_table("BY PROVIDER", self.stats["by_provider"]))
        output.append(print_table("BY MODEL", self.stats["by_model"]))
        output.append(print_table("BY ROLE (Node)", self.stats["by_role"]))
        output.append("\n" + "="*60)
        return "\n".join(output)

class DebugHandler(BaseCallbackHandler):
    def __init__(self):
        self.depth = 0

    def on_chain_start(self, serialized, inputs, *, run_id, **kwargs):
        name = "Unknown Runnable"
        if serialized:
            name = serialized.get("name") or serialized.get("id") or name
        elif kwargs.get("metadata"):
            name = kwargs["metadata"].get("langgraph_node") or name
        print(f"{'  ' * self.depth}-> CHAIN START: {name} ({run_id})")
        self.depth += 1

    def on_chain_end(self, outputs, *, run_id, **kwargs):
        self.depth -= 1
        print(f"{'  ' * self.depth}<- CHAIN END ({run_id})")



class StoryTeller:
    def __init__(self, scenario, champions_json, logger):
        self.graph = StateGraph(AgentState)
        self.scenario = scenario
        self.champions_json = champions_json
        self.logger = logger
        self.agent_factory = AgentFactory()
        self._preprocess_input()
        self.conn = None
        self.app = None
        self.db_path = Config.LANGGRAPH_CHECKPOINTS_DB

    def __init__(self, story_teller_item: StoryTellerItem):
        self.graph = StateGraph(AgentState)
        self.scenario = story_teller_item.scenario
        self.champions_json = story_teller_item.champions
        self.logger = story_teller_item.logger
        self.agent_factory = AgentFactory()
        self._preprocess_input()
        self.conn = None
        self.app = None
        self.debug = DebugHandler()
        self.db_path = Config.LANGGRAPH_CHECKPOINTS_DB

    def _preprocess_input(self):
        self.champion_agents = {}
        for champ in self.champions_json:
            champ_name = champ["name"]
            champ_traits = set(champ["personality"])
            champ_model = ModelChoices[champ["models"]]
            champ_agent_config = ChampionAgentConfig(
                role=Role[champ_name],
                model=champ_model,
                traits=champ_traits,
                story_context=self.scenario,
            )
            self.champion_agents[champ_name] = self.agent_factory.create_champion_agent(
                champ_agent_config
            )
            self.graph.add_node(champ_name, self.champion_agents[champ_name])

    def build_graph(self):
        event_bot = self.agent_factory.create_event_creator_agent(
            EventCreatorAgentConfig(
                role=Role.Event,
                model=ModelChoices.Event,
                input_json=self.champions_json,
                scenario=self.scenario,
            )
        )
        role_bot = self.agent_factory.create_role_assigner_agent(
            RoleAssignerAgentConfig(
                role=Role.RoleAssigner,
                model=ModelChoices.RoleAssigner,
                champions_list=list(self.champion_agents.keys()),
            )
        )
        summarizer_bot = self.agent_factory.create_summarizer_agent(
            SummarizerAgentConfig(role=Role.Summarizer, model=ModelChoices.Summarizer)
        )
        novel_bot = self.agent_factory.create_novel_writer_agent(
            NovelWriterAgentConfig(
                role=Role.Novel,
                model=ModelChoices.Novel,
                min_words=200,
                max_words=500,
            )
        )

        self.graph.add_node("RoleAssignerBot", role_bot)
        self.graph.add_node("EventCreatorBot", event_bot)
        self.graph.add_node("NovelWriterBot", novel_bot)
        self.graph.add_node("SummarizerBot", summarizer_bot)

        self.graph.set_entry_point("EventCreatorBot")
        self.graph.add_edge("EventCreatorBot", "RoleAssignerBot")

        self.graph.add_conditional_edges(
            "RoleAssignerBot",
            role_assigner_node,
            list(self.champion_agents.keys()) + ["NovelWriterBot", "RoleAssignerBot"],
        )
        for champ in self.champion_agents.keys():
            self.graph.add_edge(champ, "SummarizerBot")
            self.graph.add_edge("SummarizerBot", "RoleAssignerBot")
        self.graph.add_edge("NovelWriterBot", END)

        print(f"\n{'='*60}")
        print(f"DB path: {self.db_path}")
        print(f"{'='*60}\n")

        # Use config path
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        memory = SqliteSaver(self.conn)
        self.app = self.graph.compile(checkpointer=memory)

        # Save graph visualization using config path
        try:
            with open(str(Config.GRAPH_VISUALIZATION_PATH), "wb") as f:
                f.write(self.app.get_graph().draw_mermaid_png())
            print(f"Graph visualization saved to {Config.GRAPH_VISUALIZATION_PATH}\n")
        except Exception as e:
            print(f"Warning: Could not save graph visualization: {e}\n")

    def invoke(self):
        stats_collector = RequestCounter()
        
        config = {
            "configurable": {
                "thread_id": thread_id
            },
            "recursion_limit": 100,
            "callbacks": [stats_collector, self.debug]
        }

        self.app.invoke(
            AgentState(
                messages=[], model=None, next_bot=[], event_list=[], ai_response=""
            ),
            config
        )
        
        print(stats_collector) 

        if self.conn:
            self.conn.commit()
            self.conn.close()

        try:
            self.logger.export_and_save_checkpoints_to_s3(self.db_path)
            self.logger._cleanup_database(self.db_path)
        except Exception as e:
            raise

        # serializable_result = {
        #     'ai_response': result.get('ai_response', ''),
        #     'messages': [
        #         {
        #             'role': getattr(msg, 'type', 'unknown'),
        #             'content': msg.content if hasattr(msg, 'content') else str(msg)
        #         }
        #         for msg in result.get('messages', [])
        #     ],
        #     'event_list': list(result.get('event_list', [])),
        #     'next_bot': result.get('next_bot', []),
        #     'model': str(result.get('model', '')) if result.get('model') else None
        # }

        # get the content of ai_response
        # return result["ai_response"].content


def role_assigner_node(state):
    if len(state["next_bot"]) > 0:
        next_bot = state["next_bot"][-1]
        if (next_bot == "Event") and (len(state["event_list"]) == 0):
            return "NovelWriterBot"
        elif next_bot == "Event":
            next_event = state["event_list"].popleft()
            state["messages"].append(AIMessage(content=next_event))
            return "RoleAssignerBot"
        else:
            return next_bot
    else:
        raise Exception("Something wrong")

if __name__ == "__main__":
    from .logger import Logger

    scenario = "Twisted Fate and Zed are computer science students. They are arguing about their group project."
    json_input = [
        {"name": "Zed", "personality": "Happy", "models": "gemini_2_0_flash_lite"},
        {
            "name": "TwistedFate",
            "personality": "Sad",
            "models": "gemini_2_0_flash_lite",
        },
    ]
    logger = Logger()
    story_teller = StoryTeller(
        scenario=scenario, champions_json=json_input, logger=logger
    )
    assert story_teller is not None
    story_teller.build_graph()
    story_teller.invoke()