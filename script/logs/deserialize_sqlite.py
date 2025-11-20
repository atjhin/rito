import sqlite3
import json
from datetime import datetime
from langgraph.checkpoint.sqlite import SqliteSaver

conn = sqlite3.connect("langgraph_checkpoints.sqlite")
checkpointer = SqliteSaver(conn)

output_file = f"checkpoint_contents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("LANGGRAPH CHECKPOINT CONTENTS\n")
    f.write(f"Generated: {datetime.now()}\n")
    f.write("="*80 + "\n\n")
    
    # List all checkpoints
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
    threads = cursor.fetchall()
    
    for thread_id_tuple in threads:
        thread_id = thread_id_tuple[0]
        f.write(f"\n{'='*80}\n")
        f.write(f"Thread ID: {thread_id}\n")
        f.write(f"{'='*80}\n\n")
        
        # Get checkpoints for this thread
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Get checkpoint history
            checkpoints = list(checkpointer.list(config))
            
            for i, checkpoint_tuple in enumerate(checkpoints):
                f.write(f"\n--- Checkpoint #{i+1} ---\n")
                f.write(f"Checkpoint ID: {checkpoint_tuple.config.get('configurable', {}).get('checkpoint_id', 'N/A')}\n\n")
                
                # The checkpoint data is in checkpoint_tuple.checkpoint
                checkpoint_data = checkpoint_tuple.checkpoint
                
                f.write("CHECKPOINT DATA:\n")
                f.write(json.dumps(checkpoint_data, indent=2, default=str) + "\n\n")
                
                # Try to extract channel values (where the actual state is stored)
                if hasattr(checkpoint_data, 'channel_values'):
                    f.write("STATE VALUES:\n")
                    f.write(json.dumps(checkpoint_data.channel_values, indent=2, default=str) + "\n\n")
                
                f.write("-"*80 + "\n")
                
        except Exception as e:
            f.write(f"Error reading checkpoints: {e}\n\n")

conn.close()
print(f"Checkpoint contents saved to: {output_file}")