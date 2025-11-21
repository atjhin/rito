from langchain_core.messages import BaseMessage
from typing import List
import pandas as pd
import json
import io
import os
import boto3
from dotenv import load_dotenv
from app.utils.constants.path_config import Config

import sqlite3
import json
import pandas as pd
from datetime import datetime
from langgraph.checkpoint.sqlite import SqliteSaver

class Logger:
    def __init__(self):
        self.log_dir = Config.LOGS_DIR
        pass

    def export_and_save_checkpoints_to_s3(self, db_path):
        """
        Export LangGraph checkpoints to DataFrame, save locally, and upload all formats to S3
        """
        
        # ===== EXPORT FROM DATABASE =====
        conn = sqlite3.connect(db_path)
        checkpointer = SqliteSaver(conn)
        
        all_checkpoints = []
        
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
        threads = cursor.fetchall()
        
        print(f"Found {len(threads)} threads")
        
        for thread_id_tuple in threads:
            thread_id = thread_id_tuple[0]
            config = {"configurable": {"thread_id": thread_id}}
            
            try:
                checkpoints = list(checkpointer.list(config))
                
                for i, checkpoint_tuple in enumerate(checkpoints):
                    checkpoint_data = checkpoint_tuple.checkpoint
                    checkpoint_config = checkpoint_tuple.config
                    
                    # Extract the important information
                    record = {
                        'thread_id': thread_id,
                        'checkpoint_number': i + 1,
                        'checkpoint_id': checkpoint_config.get('configurable', {}).get('checkpoint_id', 'N/A'),
                        'timestamp': datetime.now().isoformat(),
                    }
                    
                    # Extract channel values
                    if hasattr(checkpoint_data, 'channel_values'):
                        channel_values = checkpoint_data.channel_values
                        
                        # Extract messages as separate column
                        if 'messages' in channel_values:
                            messages = channel_values['messages']
                            # Convert AIMessage objects to dicts
                            record['messages'] = [
                                {
                                    'content': msg.content if hasattr(msg, 'content') else str(msg),
                                    'type': type(msg).__name__,
                                    'id': getattr(msg, 'id', None),
                                    'usage_metadata': getattr(msg, 'usage_metadata', None)
                                }
                                for msg in messages
                            ]
                        else:
                            record['messages'] = []
                        
                        # Extract ai_response as separate column
                        if 'ai_response' in channel_values:
                            ai_response = channel_values['ai_response']
                            if ai_response:
                                record['ai_response'] = {
                                    'content': ai_response.content if hasattr(ai_response, 'content') else str(ai_response),
                                    'type': type(ai_response).__name__,
                                    'id': getattr(ai_response, 'id', None),
                                    'usage_metadata': getattr(ai_response, 'usage_metadata', None)
                                }
                            else:
                                record['ai_response'] = None
                        else:
                            record['ai_response'] = None
                        
                        # Store the rest of channel_values (without messages and ai_response)
                        remaining_state = {k: v for k, v in channel_values.items() 
                                        if k not in ['messages', 'ai_response']}
                        record['state'] = remaining_state
                    else:
                        record['state'] = checkpoint_data
                        record['messages'] = []
                        record['ai_response'] = None
                    
                    # Add metadata if available
                    if hasattr(checkpoint_tuple, 'metadata'):
                        record['metadata'] = checkpoint_tuple.metadata
                    
                    all_checkpoints.append(record)
                    
            except Exception as e:
                print(f"Error reading checkpoints for thread {thread_id}: {e}")
                all_checkpoints.append({
                    'thread_id': thread_id,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        conn.close()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_checkpoints)
        print(f"\nDataFrame shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # ===== SAVE LOCALLY =====
        json_file = os.path.join(self.log_dir, f"langgraph_checkpoints_{timestamp}.json")
        df.to_json(json_file, orient='records', indent=2, default_handler=str)
        print(f"✓ Saved to: {json_file}")
        
        pretty_json_file = os.path.join(self.log_dir, f"langgraph_checkpoints_{timestamp}_pretty.json")
        with open(pretty_json_file, 'w', encoding='utf-8') as f:
            json.dump(all_checkpoints, f, indent=2, default=str, ensure_ascii=False)
        print(f"✓ Pretty version saved to: {pretty_json_file}")
        
        pickle_file = os.path.join(self.log_dir, f"langgraph_checkpoints_{timestamp}.pkl")
        df.to_pickle(pickle_file)
        print(f"✓ Pickle saved to: {pickle_file}")
        
        # ===== UPLOAD TO S3 =====
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
        uploaded_keys = []
        
        try:
            # 1. Upload compact JSON
            buffer = io.BytesIO()
            json_str = df.to_json(orient='records', indent=2, default_handler=str)
            buffer.write(json_str.encode('utf-8'))
            buffer.seek(0)
            key = f"langgraph_checkpoints/json/checkpoints_{timestamp}.json"
            s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())
            uploaded_keys.append(key)
            print(f"✓ Uploaded JSON to S3: {key}")
            
            # 2. Upload pretty JSON
            buffer = io.BytesIO()
            pretty_json_str = json.dumps(all_checkpoints, indent=2, default=str, ensure_ascii=False)
            buffer.write(pretty_json_str.encode('utf-8'))
            buffer.seek(0)
            key = f"langgraph_checkpoints/pretty_json/checkpoints_{timestamp}_pretty.json"
            s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())
            uploaded_keys.append(key)
            print(f"✓ Uploaded pretty JSON to S3: {key}")
            
            # 3. Upload pickle
            buffer = io.BytesIO()
            df.to_pickle(buffer)
            buffer.seek(0)
            key = f"langgraph_checkpoints/pickle/checkpoints_{timestamp}.pkl"
            s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())
            uploaded_keys.append(key)
            print(f"✓ Uploaded pickle to S3: {key}")
            
            # 4. Upload CSV (as the df format)
            buffer = io.BytesIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            key = f"langgraph_checkpoints/csv/checkpoints_{timestamp}.csv"
            s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())
            uploaded_keys.append(key)
            print(f"✓ Uploaded CSV to S3: {key}")
            
            print(f"\n✓ All files uploaded successfully to S3")
            return uploaded_keys, json_file, pretty_json_file, pickle_file, df
            
        except Exception as e:
            print(f"✗ Error uploading to S3: {e}")
            print(f"✓ Local backups available at: {self.log_dir}")
            raise

    def _cleanup_database(self,db_path):
        """Delete the SQLite database after uploading to S3"""
        try:
            if os.path.exists(str(db_path)):
                os.remove(str(db_path))
                print(f"✓ Cleaned up database: {db_path}")
        except Exception as e:
            print(f"⚠ Warning: Could not delete database {db_path}: {e}")