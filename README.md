# EduScout — DigitalOcean Gradient ADK Agent

**School discovery + personalized education agent** built with the **Gradient Agent Development Kit (ADK)**.  
Deployed and running on DigitalOcean Gradient with VAPI webhook integration.

## Architecture Overview
- **Entry point**: `main.py` (uses `@entrypoint` decorator — standard ADK)
- **Multi-agent system**: `agents/` (document_analyst, logistics, mystery_shopper, school_finder, school_comparison, session_manager)
- **Tools**: `tools/` (database, maps, preference_extractor, vapi_caller, whatsapp, webhook handler)
- **Webhook server**: `webhook/server.py` (handles VAPI voice sessions)
- **School portal**: `school_portal/index.html` (frontend demo)
- **Data layer**: `data/` (PostgreSQL schema + migrations + seed data)

Matches official ADK structure + advanced templates (see [gradient-adk-templates](https://github.com/digitalocean/gradient-adk-templates)).

## Knowledge Base
EduScout uses a **DO Knowledge base** and a **custom SQL knowledge base**  stored in PostgreSQL:
- `data/schema.sql` → full table structure
- `data/seed_schools.sql` → initial school dataset
- `data/migration_day5.sql` & `migration_day8.sql` → schema evolution
- AI model queries this KB via natural-language-to-SQL in `tools/database.py` + `agents/school_finder.py`.

## DigitalOcean Knowledge Base (RAG)

EduScout uses a **managed DigitalOcean Knowledge Base** for retrieval-augmented generation (not custom SQL).  
All school data, documents, comparisons, and preferences are grounded in this KB.

### KB Details
| Item                  | Value / Description |
|-----------------------|---------------------|
| **Name**             | EduScout Schools KB (or your chosen name) |
| **UUID**             | `DIGITALOCEAN_KB_UUID` (set in `.env`) |
| **Embedding Model**  | [Your model, e.g. text-embedding-3-large or DO default] |
| **Data Sources**     | - Uploaded school PDFs/docs<br>- `seed_schools` data<br>- Web crawl of education sites (if used)<br>- Spaces bucket (optional) |
| **Chunking**         | Hierarchical / Semantic (configured in DO Control Panel) |
| **OpenSearch DB**    | Auto-provisioned (region matching your agent) |

**How to recreate the KB** (in case you need to spin up a new workspace):
1. DigitalOcean Control Panel → **Agent Platform** → **Knowledge Bases** → **Create Knowledge Base**
2. Choose embedding model
3. Add data sources (files / Spaces / web crawler)
4. Create → indexing starts automatically
5. Copy the UUID from the URL and put in `.env`

## Agent Functions
| Agent | Purpose | Key File |
|-------|--------|----------|
| school_finder | Finds & ranks schools by preferences | `agents/school_finder.py` |
| school_comparison | Side-by-side analysis | `agents/school_comparison.py` |
| document_analyst | Analyzes school PDFs/docs | `agents/document_analyst.py` |
| mystery_shopper | Simulated school visits | `agents/mystery_shopper.py` |
| logistics | Session & flow management | `agents/logistics.py` |
| session_manager | State persistence | `agents/session_manager.py` |

All agents use LangGraph-style state passing.

## Tools & Functions
- `tools/database.py` — AI-powered DB queries (IA model integration)
- `tools/preference_extractor.py` — Extracts user prefs using LLM
- `tools/vapi_caller.py` + `webhook/` — Voice interface
- `tools/maps.py` — Location services
- `tools/whatsapp.py` — Messaging

## Database (using IA model)
- **Engine**: PostgreSQL (inferred from SQL files + backup)
- **IA model integration**: `tools/database.py` + `preference_extractor.py` use the Gradient LLM to:
  - Translate natural language → SQL
  - Self-heal failed queries
  - Enrich results with school rankings
- Schema documentation: `data/schema.sql` (run it on your DB)
- Seeded with real school data (`seed_schools.sql`)

## Setup & Deployment (ADK standard)
```bash
# On droplet
pip install -r requirements.txt
cp .env.example .env
gradient agent run          # local test
gradient agent deploy       # production (already done)

# Testing

Webhook: webhook/server.py
Evaluations: evaluation*.csv
Logs: gradient.logs

Built with ❤️ using official Gradient ADK docs.
