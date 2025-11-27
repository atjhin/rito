from langchain_core.messages import BaseMessage
from typing import List, Any
import pandas as pd
import json
import io
import os
import boto3
from dotenv import load_dotenv
from app.utils.data_models.agent_logger_item import AgentLoggerItem


def _content_to_text(content: Any) -> str:
    """
    Normalize various LLM content formats to a plain string.

    Handles:
    - None -> ""
    - str -> as-is
    - list of dict/str/etc -> join text parts
    - dict with 'text'/'content' keys -> that value
    - anything else -> str(content)
    """
    if content is None:
        return ""

    # Simple string
    if isinstance(content, str):
        return content

    # List of parts (common for tool-calls / multi-part responses)
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                # Common patterns: {"type": "text", "text": "..."}
                if "text" in part and isinstance(part["text"], str):
                    parts.append(part["text"])
                elif "content" in part and isinstance(part["content"], str):
                    parts.append(part["content"])
                else:
                    parts.append(str(part))
            else:
                parts.append(str(part))
        return "\n".join(parts)

    # Dict content (rare, but be defensive)
    if isinstance(content, dict):
        if "text" in content and isinstance(content["text"], str):
            return content["text"]
        if "content" in content and isinstance(content["content"], str):
            return content["content"]
        # fall back to JSON-ish representation
        try:
            return json.dumps(content, ensure_ascii=False)
        except TypeError:
            return str(content)

    # Fallback: just stringify
    return str(content)


class Logger:
    def __init__(self):
        self.logs = []
        self.client = None  # Placeholder for any client you might want to add later

    def log_llm_invocation(self, item: AgentLoggerItem):
        role_name = item.agent_role_name
        model_name = item.model_name
        messages: List[BaseMessage] = item.messages
        output_message: BaseMessage = item.output_message

        # Safely extract system message (usually first)
        if messages:
            system_raw = getattr(messages[0], "content", None)
            system_message = _content_to_text(system_raw).strip()
        else:
            system_message = ""

        # Safely extract "human" message (usually last)
        if len(messages) > 1:
            human_raw = getattr(messages[-1], "content", None)
            human_message = _content_to_text(human_raw).strip()
        else:
            human_message = ""

        # Middle messages as "input_message" context
        input_messages = []
        if len(messages) > 2:
            for msg in messages[1:-1]:
                raw = getattr(msg, "content", None)
                text = _content_to_text(raw).strip()
                if text:
                    input_messages.append(text)

        # Output message
        output_raw = getattr(output_message, "content", None)
        output_text = _content_to_text(output_raw).strip()

        log_entry = {
            "role": role_name,
            "model": model_name,
            "system_message": system_message,
            "human_message": human_message,
            "input_message": input_messages,
            "output_message": output_text,
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
            meta=[
                'model', 
                'role', 
                'system_message',
                'human_message',
                'input_message',
                'output_message'
            ],
        )
        print("Formatted log DataFrame:\n", df.head())

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
        os.makedirs(log_folder, exist_ok=True)  # ensure folder exists
        with open(f"{log_folder}/story_teller.log", 'w') as f:
            json.dump(self.logs, f, indent=4)

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
        s3.put_object(
            Bucket=bucket,
            Key=f"story_teller_logs/story_teller_{dt_now}.parquet",
            Body=parquet_buffer.getvalue()
        )
