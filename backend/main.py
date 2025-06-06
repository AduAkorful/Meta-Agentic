import os
import sqlite3
import pathlib
import modal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

# Modal app and image setup
app = modal.App(
    name="meta-agentic-backend",
    image=modal.Image.debian_slim().pip_install_from_requirements("requirements.txt"),
)

fastapi_app = FastAPI()

# SQLite DB file path inside container
AGENT_DB_FILE = "/root/meta_agentic_agents.db"

# Agent model
class Agent(BaseModel):
    id: int
    name: str
    purpose: str
    model: str = "default"

# Initialize SQLite DB and create table if not exists
def init_db():
    db_path = pathlib.Path(AGENT_DB_FILE)
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(AGENT_DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            purpose TEXT NOT NULL,
            model TEXT DEFAULT 'default'
        )
        """)
        conn.commit()

# Insert agent into DB
def insert_agent(agent: Agent):
    with sqlite3.connect(AGENT_DB_FILE) as conn:
        conn.execute(
            "INSERT INTO agents (id, name, purpose, model) VALUES (?, ?, ?, ?)",
            (agent.id, agent.name, agent.purpose, agent.model)
        )
        conn.commit()

# Get agent from DB by id
def get_agent(agent_id: int):
    with sqlite3.connect(AGENT_DB_FILE) as conn:
        cur = conn.execute("SELECT id, name, purpose, model FROM agents WHERE id = ?", (agent_id,))
        row = cur.fetchone()
        if row:
            return Agent(id=row[0], name=row[1], purpose=row[2], model=row[3])
        return None

# Get all agents
def list_agents():
    with sqlite3.connect(AGENT_DB_FILE) as conn:
        cur = conn.execute("SELECT id, name, purpose, model FROM agents")
        rows = cur.fetchall()
        return [Agent(id=row[0], name=row[1], purpose=row[2], model=row[3]) for row in rows]

# Update existing agent
def update_agent(agent: Agent):
    with sqlite3.connect(AGENT_DB_FILE) as conn:
        conn.execute(
            "UPDATE agents SET name = ?, purpose = ?, model = ? WHERE id = ?",
            (agent.name, agent.purpose, agent.model, agent.id)
        )
        conn.commit()

# Delete agent by id
def delete_agent(agent_id: int):
    with sqlite3.connect(AGENT_DB_FILE) as conn:
        conn.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        conn.commit()

# Nebius API helpers
def get_nebius_headers(api_key: str):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

async def call_nebius_model(api_key: str, model_name: str, prompt: str):
    url = f"https://api.nebius.com/v1/models/{model_name}/completions"
    payload = {
        "prompt": prompt,
        "max_tokens": 150
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=get_nebius_headers(api_key), json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("choices", [{}])[0].get("text", "")

# FastAPI routes
@fastapi_app.get("/")
def root():
    return {"message": "Welcome to Meta-Agentic Backend"}

@fastapi_app.post("/agents/")
def create_agent(agent: Agent):
    if get_agent(agent.id) is not None:
        raise HTTPException(status_code=400, detail="Agent already exists")
    insert_agent(agent)
    return agent

@fastapi_app.get("/agents/")
def get_agents():
    agents = list_agents()
    return agents

@fastapi_app.get("/agents/{agent_id}")
def read_agent(agent_id: int):
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@fastapi_app.put("/agents/{agent_id}")
def modify_agent(agent_id: int, agent: Agent):
    existing_agent = get_agent(agent_id)
    if not existing_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    update_agent(agent)
    return agent

@fastapi_app.delete("/agents/{agent_id}")
def remove_agent(agent_id: int):
    if not get_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    delete_agent(agent_id)
    return {"detail": "Agent deleted"}

class PromptRequest(BaseModel):
    prompt: str

@fastapi_app.post("/agents/{agent_id}/generate")
async def generate_with_agent(agent_id: int, prompt_req: PromptRequest):
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    nebius_api_key = os.getenv("NEBIUS_API_KEY")
    if not nebius_api_key:
        raise HTTPException(status_code=500, detail="Nebius API key not found")

    model_name = agent.model if agent.model else "default"

    try:
        output_text = await call_nebius_model(nebius_api_key, model_name, prompt_req.prompt)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Nebius API error: {e.response.text}")

    return {
        "agent_id": agent_id,
        "model": model_name,
        "input_prompt": prompt_req.prompt,
        "output": output_text
    }

# Modal app entrypoint without volume (data is ephemeral)
@app.function(
    secrets=[modal.Secret.from_name("nebius-api-key")]
)
@modal.asgi_app()
def app_entry():
    init_db()  # initialize DB on startup
    return fastapi_app
