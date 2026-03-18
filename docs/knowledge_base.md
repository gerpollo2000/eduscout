# EduScout Knowledge Base (Official DO Managed RAG)

**KB Name**: eduscout-school-docs  
**UUID**: `24caa050-0de5-1ff1-b074-4e013e2ddde4` (see `.env.example`)  
**Workspace**: EduScout

Matches the official `KnowledgeBaseRAG` template structure and ADK best practices.

## Exact Configuration (screenshots from March 2026)

| Setting                  | Value                                      |
|--------------------------|--------------------------------------------|
| **Embeddings Model**    | GTE Large EN v1.5 ($0.09/1M tokens)       |
| **Data Sources**        | 1 source: "eduscout-docs" (SFO3)          |
| **Chunking**            | Section-based                             |
| **Total Size**          | 2.05 MiB                                  |
| **Indexing Schedule**   | Every day at 4:04 AM UTC                  |
| **OpenSearch DB**       | genai-octopus (San Francisco • SFO2 • default-sfo2) |
| **Tags**                | None                                      |
| **Associated Agents**   | None (normal for ADK — we use dynamic SDK retrieval) |
| **Last Indexing**       | ~9 hours ago (no changes, free)           |

## Source Documents (Canonical Files)

These are the **exact files** uploaded to the "eduscout-docs" data source:

- `beacon_handbook.md`
- `ideal_school_handbook.md`
- `ps6_handbook.md`
- `stuyvesant_handbook.md`
- `success_academy_handbook.md`
- `trinity_handbook.md`

**Location in repo**: `knowledge_base/sources/`  
Upload these 6 files when recreating the data source.

## How the Agent Uses the KB (RAG)

All agents (`school_finder.py`, `document_analyst.py`, `preference_extractor.py`, etc.) retrieve context dynamically via the Gradient SDK (no manual attachment needed).

Example (adapt to your exact implementation in `tools/`):

```python
from gradient_sdk import GradientClient
import os

client = GradientClient(api_token=os.getenv("DIGITALOCEAN_API_TOKEN"))
kb_uuid = os.getenv("DIGITALOCEAN_KB_UUID")

response = client.knowledge_bases.retrieve(
    knowledge_base_uuid=kb_uuid,
    query=user_query,
    num_results=5
)

context = "\n\n".join([doc.text for doc in response.results])
