import os
import psycopg
import json
from dotenv import load_dotenv

load_dotenv(".env")

postgres_url = os.getenv("POSTGRES_URL")

try:
    conn = psycopg.connect(postgres_url)
    cursor = conn.cursor()
    
    # Get all checkpoints for thread 2 (or 1)
    cursor.execute("SELECT thread_id, checkpoint FROM checkpoints ORDER BY thread_id, checkpoint_id DESC LIMIT 5;")
    rows = cursor.fetchall()
    
    print("--- LAST 5 CHECKPOINTS ---")
    for row in rows:
        thread_id, checkpoint = row[0], row[1]
        print(f"\n[Thread {thread_id}]")
        try:
            # Checkpoint might be binary or json depending on the saver
            # LangGraph postgres saver usually stores pickle or json in checkpoint column
            if isinstance(checkpoint, bytes):
                import pickle
                data = pickle.loads(checkpoint)
            elif isinstance(checkpoint, str):
                data = json.loads(checkpoint)
            else:
                data = checkpoint
                
            messages = data.get("channel_values", {}).get("messages", [])
            for msg in messages:
                # If msg is a tuple or dict
                if hasattr(msg, "content"):
                    print(f"[{msg.__class__.__name__}] {msg.content}")
                else:
                    print(f"Message: {msg}")
        except Exception as e:
            print(f"Could not parse checkpoint: {e}")
            
    conn.close()
except Exception as e:
    print(f"Failed: {e}")
