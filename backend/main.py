import os
import modal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import json
from typing import Dict, Any, Optional

# Import from database module
from database import Agent, init_db, insert_agent, get_agent, list_agents, update_agent, delete_agent

# Modal app and image setup
app = modal.App(
    name="meta-agentic-backend",
    image=modal.Image.debian_slim().pip_install_from_requirements("requirements.txt"),
)

fastapi_app = FastAPI()

# Enhanced Agent model for requests
class AgentRequest(BaseModel):
    id: int
    name: str
    purpose: str
    model: str = "default"
    configuration: Dict[str, Any] = {}

# Response model
class AgentResponse(Agent):
    pass

# Enhanced prompt request model
class PromptRequest(BaseModel):
    prompt: str
    parameters: Optional[Dict[str, Any]] = None

# Nebius API helpers
def get_nebius_headers(api_key: str):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

async def call_nebius_model(api_key: str, model_name: str, prompt: str, parameters: Dict[str, Any] = None):
    url = f"https://api.nebius.com/v1/models/{model_name}/completions"
    payload = {
        "prompt": prompt,
        "max_tokens": parameters.get("max_tokens", 150) if parameters else 150,
        "temperature": parameters.get("temperature", 0.7) if parameters else 0.7
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=get_nebius_headers(api_key), json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("choices", [{}])[0].get("text", "")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
            raise HTTPException(status_code=e.response.status_code, detail=f"Nebius API error: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")

# FastAPI routes
@fastapi_app.get("/")
def root():
    return {"message": "Welcome to Meta-Agentic Backend", "status": "operational"}

@fastapi_app.post("/agents/", response_model=AgentResponse)
def create_agent(agent_request: AgentRequest):
    if get_agent(agent_request.id) is not None:
        raise HTTPException(status_code=400, detail="Agent already exists with this ID")
    
    # Convert request to Agent model
    agent = Agent(
        id=agent_request.id,
        name=agent_request.name,
        purpose=agent_request.purpose,
        model=agent_request.model,
        configuration=agent_request.configuration
    )
    
    insert_agent(agent)
    return agent

@fastapi_app.get("/agents/", response_model=list[AgentResponse])
def get_agents():
    agents = list_agents()
    return agents

@fastapi_app.get("/agents/{agent_id}", response_model=AgentResponse)
def read_agent(agent_id: int):
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@fastapi_app.put("/agents/{agent_id}", response_model=AgentResponse)
def modify_agent(agent_id: int, agent_request: AgentRequest):
    existing_agent = get_agent(agent_id)
    if not existing_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Update agent with request data
    agent = Agent(
        id=agent_id,
        name=agent_request.name,
        purpose=agent_request.purpose,
        model=agent_request.model,
        configuration=agent_request.configuration
    )
    
    update_agent(agent)
    return agent

@fastapi_app.delete("/agents/{agent_id}")
def remove_agent(agent_id: int):
    if not get_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    delete_agent(agent_id)
    return {"detail": "Agent deleted"}

@fastapi_app.post("/agents/{agent_id}/generate")
async def generate_with_agent(agent_id: int, prompt_req: PromptRequest):
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    nebius_api_key = os.getenv("NEBIUS_API_KEY")
    if not nebius_api_key:
        raise HTTPException(status_code=500, detail="Nebius API key not found in environment")

    model_name = agent.model if agent.model != "default" else "nebius-text-medium"
    
    # Merge agent configuration with request parameters
    parameters = agent.configuration.copy()
    if prompt_req.parameters:
        parameters.update(prompt_req.parameters)

    output_text = await call_nebius_model(
        nebius_api_key, 
        model_name, 
        prompt_req.prompt,
        parameters
    )
    
    return {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "model": model_name,
        "input_prompt": prompt_req.prompt,
        "output": output_text
    }

# Health check endpoint
@fastapi_app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "1.1.0",
        "database": "connected"
    }

# Modal app entrypoint
@app.function(
    secrets=[modal.Secret.from_name("nebius-api-key")],
    # Add persistent volume for the database
    volumes={
        "/root": modal.Volume.persisted("meta-agentic-db-vol")
    }
)
@modal.asgi_app()
def app_entry():
    init_db()  # initialize DB on startup
    return fastapi_app
