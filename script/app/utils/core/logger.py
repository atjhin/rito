from langchain_core.messages import BaseMessage
from typing import List
import pandas as pd
import json
import io
import os
import boto3
from dotenv import load_dotenv
from app.utils.data_models.agent_logger_item import AgentLoggerItem


class Logger:
    def __init__(self):
        self.logs = []
        self.client = None # Placeholder for any client you might want to add later

    def log_llm_invocation(self, item: AgentLoggerItem):
        role_name = item.agent_role_name
        model_name = item.model_name
        messages = item.messages
        output_message = item.output_message

        log_entry = {
            "role": role_name,
            "model": model_name,
            "system_message": messages[0].content.strip() if messages and messages[0].content else "",
            'human_message': messages[-1].content.strip() if len(messages) > 1 and messages[-1].content else "",
            "input_message": [msg.content.strip() for msg in messages[1:-1] if msg.content],
            "output_message": output_message.content.strip() if output_message.content else "",
        }
        self.logs.append(log_entry)
        self.save_logs_to_file()

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
        print ("Formatted log DataFrame:\n", df.head())
        
        final_columns = [
            'model',
            'role',
            'system_message',
            'human_message',
            'input_message',
            'output_message'
        ]
        return df[final_columns]


    def save_logs_to_file(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_folder = os.path.abspath(os.path.join(base_dir, "..", "..", "..", "logs"))
        with open(f"{log_folder}/story_teller.log", 'w') as f:
            json.dump(self.logs, f, indent=4)

        # log_df = self.format_logs_to_dataframe()

        # parquet_buffer = io.BytesIO()
        # log_df.to_parquet(parquet_buffer, index=False)
        # parquet_buffer.seek(0)

    def save_logs_to_S3(self):

        log_df = self.format_logs_to_dataframe()

        parquet_buffer = io.BytesIO()
        log_df.to_parquet(parquet_buffer, index=False)
        parquet_buffer.seek(0)

        basedir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(basedir, '.env')
        load_dotenv(env_path)

        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
            region_name=os.getenv("S3_REGION")
        )

        bucket = os.getenv("S3_BUCKET")
        dt_now = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        s3.put_object(Bucket=bucket, Key=f"story_teller_logs/story_teller_{dt_now}.parquet", Body=parquet_buffer.getvalue())