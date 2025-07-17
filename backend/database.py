import sqlite3
from pathlib import Path
from pydantic import BaseModel
import os
import json

# Use environment variable or default path
DB_FILE = Path(os.getenv("AGENT_DB_FILE", "/data/meta_agentic_agents.db"))

class Agent(BaseModel):
    id: int
    name: str
    purpose: str
    model: str = "default"
    configuration: dict = {}  # Added to store agent-specific configuration

def init_db():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            purpose TEXT NOT NULL,
            model TEXT DEFAULT 'default',
            configuration TEXT DEFAULT '{}'
        )
        """)
        conn.commit()

def insert_agent(agent: Agent):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO agents (id, name, purpose, model, configuration) VALUES (?, ?, ?, ?, ?)",
            (agent.id, agent.name, agent.purpose, agent.model, json.dumps(agent.configuration))
        )
        conn.commit()

def get_agent(agent_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("SELECT id, name, purpose, model, configuration FROM agents WHERE id = ?", (agent_id,))
        row = cur.fetchone()
        if row:
            config = {}
            try:
                if row[4]:
                    config = json.loads(row[4])
            except json.JSONDecodeError:
                pass
            return Agent(id=row[0], name=row[1], purpose=row[2], model=row[3], configuration=config)
        return None

def update_agent(agent: Agent):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "UPDATE agents SET name = ?, purpose = ?, model = ?, configuration = ? WHERE id = ?",
            (agent.name, agent.purpose, agent.model, json.dumps(agent.configuration), agent.id)
        )
        conn.commit()

def delete_agent(agent_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        conn.commit()

def list_agents():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("SELECT id, name, purpose, model, configuration FROM agents")
        rows = cur.fetchall()
        agents = []
        for row in rows:
            config = {}
            try:
                if row[4]:
                    config = json.loads(row[4])
            except json.JSONDecodeError:
                pass
            agents.append(Agent(
                id=row[0], 
                name=row[1], 
                purpose=row[2], 
                model=row[3], 
                configuration=config
            ))
        return agents
