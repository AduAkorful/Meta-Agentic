import sqlite3
from pathlib import Path
from pydantic import BaseModel

DB_FILE = Path("/root/meta_agentic_agents.db")

class Agent(BaseModel):
    id: int
    name: str
    purpose: str
    model: str = "default"

def init_db():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            purpose TEXT NOT NULL,
            model TEXT DEFAULT 'default'
        )
        """)
        conn.commit()

def insert_agent(agent: Agent):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO agents (id, name, purpose, model) VALUES (?, ?, ?, ?)",
            (agent.id, agent.name, agent.purpose, agent.model)
        )
        conn.commit()

def get_agent(agent_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("SELECT id, name, purpose, model FROM agents WHERE id = ?", (agent_id,))
        row = cur.fetchone()
        if row:
            return Agent(id=row[0], name=row[1], purpose=row[2], model=row[3])
        return None

def update_agent(agent: Agent):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "UPDATE agents SET name = ?, purpose = ?, model = ? WHERE id = ?",
            (agent.name, agent.purpose, agent.model, agent.id)
        )
        conn.commit()

def delete_agent(agent_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        conn.commit()

def list_agents():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("SELECT id, name, purpose, model FROM agents")
        rows = cur.fetchall()
        return [Agent(id=row[0], name=row[1], purpose=row[2], model=row[3]) for row in rows]
