from langchain_core.messages import BaseMessage
from typing import List, Dict, Any
import pandas as pd
import json
import io

class Logger:
    def __init__(self):
        self.logs = []
        self.client = None # Placeholder for any client you might want to add later

    def log_llm_invocation(self, role_name: str, model_name: str, messages: List[BaseMessage], output_message: BaseMessage):
        
        log_entry = {
            "role": role_name,
            "model": model_name,
            "system_message": messages[0].content.strip() if messages and messages[0].content else "",
            'human_message': messages[-1].content.strip() if len(messages) > 1 and messages[-1].content else "",
            "input_message": [msg.content.strip() for msg in messages[1:-1] if msg.content],
            "output_message": output_message.content.strip() if output_message.content else "",
        }
        self.logs.append(log_entry)

    def get_logs(self):
        return self.logs
    
    def clear_logs(self):
        self.logs = []

    def format_logs_to_dataframe(self) -> pd.DataFrame:
        # Use json_normalize to flatten the data
        df = pd.json_normalize(
            data=self.logs,

            # 1. Specify the metadata columns (the top-level keys you want to keep)
            # We implicitly omit 'input_context_messages' here
            meta=[
                'model', 
                'role', 
                'system_message',
                'human_message',
                'input_message',
                'output_message'
            ],
        
        )
        
        final_columns = [
            'model',
            'role_name',
            'system_message',
            'human_message',
            'input_message',
            'output_message'
        ]
        
        return df[final_columns]




    def save_logs_to_file(self):
        with open("logs/story_teller.log", 'w') as f:
            json.dump(self.logs, f, indent=4)

        log_df = self.format_logs_to_dataframe()

        parquet_buffer = io.BytesIO()
        log_df.to_parquet(parquet_buffer, index=False)
        parquet_buffer.seek(0)
