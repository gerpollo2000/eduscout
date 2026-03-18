# Eduscout - DigitalOcean Gradient AI Agent 🎓

Eduscout is a multi-agent AI system deployed on DigitalOcean using the [DigitalOcean Gradient Agent Development Kit (ADK)](https://docs.digitalocean.com/products/gradient-ai-platform/getting-started/use-adk/). 

This system helps users find, compare, and analyze schools by leveraging a suite of specialized AI agents, interactive tools (WhatsApp, Vapi), and a robust database knowledge base.

## 🏗️ Architecture & Project Structure

Our project follows a modular architecture separating agents, tools, and the webhook interface:

*   **`agents/`**: Contains the core DO ADK Agent definitions.
    *   `school_finder.py`: Agent specialized in querying the database for school recommendations.
    *   `school_comparison.py`: Agent dedicated to comparing metrics between different educational institutions.
    *   `document_analyst.py`: Handles processing and understanding educational documents.
    *   `mystery_shopper.py`: Specialized agent for evaluating school responses/interactions.
    *   `session_manager.py` / `logistics.py`: Orchestrators for user sessions and operational logic.
*   **`tools/`**: Custom ADK Tools bound to our agents.
    *   `database.py`: Tool for agents to query our SQL database.
    *   `maps.py`: Tool for geographic and location-based school queries.
    *   `whatsapp.py`: Integration for sending/receiving WhatsApp messages.
    *   `vapi_caller.py`: Voice AI integration using Vapi.
    *   `preference_extractor.py`: Utility tool to extract user parameters from natural language.
*   **`webhook/`**: The communication layer.
    *   `server.py`: The main server handling incoming requests.
    *   `vapi_webhook_handler.py`: Dedicated endpoints for handling Vapi voice AI webhooks.
*   **`data/`**: The Knowledge Base. Contains SQL schemas (`schema.sql`) and seed data (`seed_schools.sql`).

## 🧠 AI Models & Knowledge Base

### The Models
*(Note to author: Specify here which DO Gradient models you are using, e.g., Meta-Llama-3-70B-Instruct or Mixtral-8x7B)*. 
These models are configured within the `agents/` directory using the `gradient-ai` python package.

### The Knowledge Base
The agent's knowledge base is grounded in a relational database. 
*   **Schema**: Found in `data/schema.sql`.
*   **Seeding**: Initial school data is loaded via `data/seed_schools.sql`.
*   **Migrations**: Managed iteratively (e.g., `migration_day5.sql`).
The agents do not rely solely on LLM training data; they use the `database.py` tool to perform RAG (Retrieval-Augmented Generation) and deterministic lookups against this database to ensure zero hallucinations regarding school data.

## 🚀 Deployment & Setup

This agent is designed to run on a DigitalOcean Droplet.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/gerpollo2000/eduscout.git
   cd eduscout

Install dependencies:
code
Bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Environment Variables:
Create a .env file in the root directory (do not commit this file) and include your keys:
code
Env
DIGITALOCEAN_ACCESS_TOKEN=your_do_token
VAPI_API_KEY=your_vapi_key
DATABASE_URL=your_db_connection_string
Run the Application:
code
Bash
python main.py
# OR for the webhook server
python webhook/server.py
