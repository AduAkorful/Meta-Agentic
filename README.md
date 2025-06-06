# Meta-Agentic: AI That Builds AI Agents for You

**Meta-Agentic** is a framework that dynamically creates AI agents based on user-defined goals and intents. These agents are configured to interact with various models and tools for automated reasoning, generation, or execution of tasks.

This project was built for the Hugging Face MCP Hackathon and integrates:

- **FastAPI backend** (deployed via Modal)
- **Gradio-based frontend** (hosted on Hugging Face Spaces)
- **SQLite database** to store agent data
- **Nebius AI API** for text generation
- **Agent creation, storage, and execution**

## 🔧 Tech Stack

- Python 3.10
- FastAPI
- Modal Labs (serverless infra)
- SQLite
- Pydantic
- httpx
- Gradio (frontend)
- Nebius LLM API


## 🚀 How to Run

### Backend
Deployed with Modal. To deploy:

```bash
cd backend
modal deploy main.py
