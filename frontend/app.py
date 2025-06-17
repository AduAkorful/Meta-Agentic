import gradio as gr
import requests
import json
import os
from typing import Dict, Any

# Use environment variable or default API URL
API_URL = os.getenv("BACKEND_API_URL", "https://jeffquaye36--meta-agentic-backend-app-entry.modal.run")

def create_agent(id, name, purpose, model, configuration_str):
    try:
        # Parse configuration if provided
        configuration = {}
        if configuration_str.strip():
            configuration = json.loads(configuration_str)
            
        data = {
            "id": int(id), 
            "name": name, 
            "purpose": purpose, 
            "model": model if model else "default",
            "configuration": configuration
        }
        
        response = requests.post(f"{API_URL}/agents/", json=data, timeout=10)
        response.raise_for_status()
        
        return f"✅ Agent created successfully:\n{json.dumps(response.json(), indent=2)}"
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            return f"❌ Error: {e.response.status_code} - {e.response.text}"
        return f"❌ Connection error: {str(e)}"
    except json.JSONDecodeError:
        return f"❌ Invalid JSON in configuration field"

def get_agent(agent_id):
    try:
        response = requests.get(f"{API_URL}/agents/{agent_id}", timeout=10)
        response.raise_for_status()
        
        agent = response.json()
        return f"""## Agent Details
- **ID**: {agent['id']}
- **Name**: {agent['name']}
- **Purpose**: {agent['purpose']}
- **Model**: {agent['model']}

### Configuration
```json
{json.dumps(agent.get('configuration', {}), indent=2)}
