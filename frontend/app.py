import gradio as gr
import requests

API_URL = "https://jeffquaye36--meta-agentic-backend-app-entry.modal.run"  # replace with your actual backend URL

def create_agent(id, name, purpose):
    data = {"id": id, "name": name, "purpose": purpose}
    response = requests.post(f"{API_URL}/agents/", json=data)
    if response.status_code == 200:
        return f"✅ Agent created: {response.json()}"
    else:
        return f"❌ Failed to create agent: {response.text}"

def get_agent(agent_id):
    response = requests.get(f"{API_URL}/agents/{agent_id}")
    if response.status_code == 200:
        agent = response.json()
        return f"Agent ID: {agent['id']}\nName: {agent['name']}\nPurpose: {agent['purpose']}"
    else:
        return f"❌ Agent not found: {response.text}"

def update_agent(agent_id, name, purpose):
    data = {"id": agent_id, "name": name, "purpose": purpose}
    response = requests.put(f"{API_URL}/agents/{agent_id}", json=data)
    if response.status_code == 200:
        return f"✅ Agent updated: {response.json()}"
    else:
        return f"❌ Failed to update agent: {response.text}"

def delete_agent(agent_id):
    response = requests.delete(f"{API_URL}/agents/{agent_id}")
    if response.status_code == 200:
        return f"✅ Agent deleted."
    else:
        return f"❌ Failed to delete agent: {response.text}"

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 Meta-Agentic Framework Interface")
    gr.Markdown("Create and manage modular AI agents connected to toolchains.")

    with gr.Tab("Create Agent"):
        agent_id = gr.Number(label="Agent ID", precision=0)
        name = gr.Textbox(label="Agent Name")
        purpose = gr.Textbox(label="Purpose / Goal")
        create_button = gr.Button("Create Agent")
        create_output = gr.Textbox(label="Output")
        create_button.click(create_agent, inputs=[agent_id, name, purpose], outputs=create_output)

    with gr.Tab("Get Agent"):
        get_id = gr.Number(label="Agent ID", precision=0)
        get_button = gr.Button("Get Agent")
        get_output = gr.Textbox(label="Agent Info")
        get_button.click(get_agent, inputs=get_id, outputs=get_output)

    with gr.Tab("Update Agent"):
        update_id = gr.Number(label="Agent ID", precision=0)
        update_name = gr.Textbox(label="Agent Name")
        update_purpose = gr.Textbox(label="Purpose / Goal")
        update_button = gr.Button("Update Agent")
        update_output = gr.Textbox(label="Output")
        update_button.click(update_agent, inputs=[update_id, update_name, update_purpose], outputs=update_output)

    with gr.Tab("Delete Agent"):
        delete_id = gr.Number(label="Agent ID", precision=0)
        delete_button = gr.Button("Delete Agent")
        delete_output = gr.Textbox(label="Output")
        delete_button.click(delete_agent, inputs=delete_id, outputs=delete_output)

    gr.Markdown("🚧 More coming soon: agent editing, chat interface, toolchain customization...")

demo.launch()
