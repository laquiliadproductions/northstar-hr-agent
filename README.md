# Northstar HR Agent

Northstar HR Agent is a Retrieval-Augmented Generation (RAG) system for answering questions about fictional Northstar Analytics HR policies. It retrieves relevant policy passages from a local Chroma vector database, injects the passages and citation metadata into a grounded prompt, and generates answers through a configurable OpenAI-compatible language-model provider.
The project currently implements corpus preparation, document ingestion, local embeddings, vector retrieval, grounded generation, verified citations, layered guardrails, MCP tools, and LangGraph agent orchestration.

## Current Project Status
| Stage | Status | Summary |
|---|---|---|
| Stage 1: Data and policy corpus | Complete | Fourteen policy documents and two fictional structured datasets |
| Stage 2: Ingestion and indexing | Complete | Loading, cleaning, chunking, local embeddings, Chroma persistence, and citation metadata |
| Stage 3: Retrieval-Augmented Generation | Complete | Top-k retrieval, metadata filtering, grounded prompts, verified citations, guardrails, tests, and a complex multi-document case |
| Stage 4: Agentic system design | Complete | LangGraph orchestration, multi-step HR workflows, operational traces, graceful failures, policy-aware reasoning, and confirmation-gated mock actions |
| Stage 5: MCP server and tool integration | Complete | Local stdio MCP server, five discoverable tools, RAG-backed policy retrieval, structured HR data access, confirmation-gated mock operations, and agent-to-MCP execution |
| Stage 6: Web application | Complete | Flask chatbot, HTTP endpoints, citations, supporting snippets, agent traces, and conversational employee identification |
| Stage 7: Render deployment | Complete | Free single-service deployment, generated Chroma index, public URL, readiness checks, and cold-start documentation |
| Stage 8: CI/CD | Complete | GitHub Actions checks run on push and pull request; deployment is gated on passing checks |
| Section 9: Agentic RAG evaluation | Complete | 25-case evaluation, answer-quality and agent-behavior metrics, latency, and retrieval ablation |
| Section 10: Design documentation | Complete | Design choices, architecture diagram, safeguards, and two demo workflows documented below |

## Implemented Capabilities

- Load Markdown, PDF, and CSV documents
- Normalize extracted text while retaining useful document structure
- Split Markdown by headings, PDFs by page, and CSV files by row
- Create overlapping token-aware chunks
- Generate free local 384-dimensional embeddings
- Persist embeddings and metadata in ChromaDB
- Run configurable top-k semantic retrieval
- Apply optional Chroma metadata filters
- Build grounded prompts containing retrieved text and source metadata
- Generate answers through a configurable OpenAI-compatible provider
- Resolve model source markers against actual retrieved chunks
- Display document titles, sections, paths, chunk IDs, pages or rows, and supporting snippets
- Reject invented citation numbers
- Refuse clearly out-of-corpus questions before making an LLM request
- Return cautious insufficient-evidence responses for unsupported policy questions
- Distinguish policy facts from non-policy recommendations
- Run a repeatable complex question requiring multiple policy documents
- Route HR requests through deterministic LangGraph workflows
- Retrieve fictional employee and PTO data through MCP tools
- Expose policy evidence retrieval through MCP
- Discover MCP tools and machine-readable input schemas
- Execute confirmation-gated mock PTO operations with no real side effects
- Produce operational traces containing tool selection, arguments, results, and escalation decisions

## Technology Stack

- Python 3.12
- ChromaDB
- LangChain Core and LangChain OpenAI-compatible client
- Groq free-tier inference for the current configuration
- Chroma default local embedding function (`all-MiniLM-L6-v2`)
- LangGraph for agent workflow orchestration
- Model Context Protocol (MCP) 2.2.0 for agent tool integration over stdio
- `tiktoken` for token-aware chunking
- `pypdf` for PDF extraction
- `pytest` for automated unit, workflow, safety, and regression tests

## RAG Architecture

```mermaid
flowchart TD
    A[User question] --> B[Local query embedding]
    B --> C[Chroma top-k retrieval]
    C --> D[Relevance guardrail]
    D -->|Relevant| E[Grounded prompt]
    D -->|Unrelated| F[Out-of-corpus response]
    E --> G[Configured chat model]
    G --> H[Citation validation]
    H --> I[Answer, status, and sources]
```

The model generates answer text, but application code supplies and validates source metadata. This prevents the model from inventing document titles, sections, paths, or chunk identifiers.

## Key Repository Structure

The tree below shows the main application code plus the CI and evaluation directories. Supporting project documentation is described in the submission sections below.

```text
northstar-hr-agent/
|-- .github/workflows/             # CI/CD workflow
|-- data/
|   |-- policies/                  # Fictional HR policy documents
|   `-- structured/                # Synthetic employee and PTO CSV data
|-- evaluation/                    # Cases, scripts, reports, and results
|-- scripts/                       # Index, evaluation, and agent entry points
|-- src/
|   |-- agent/                      # LangGraph workflows and routing
|   |-- ingestion/                  # Loaders, chunking, embeddings, metadata
|   |-- mcp_server/                 # MCP server and stdio client
|   |-- rag/                        # Grounded answers, citations, guardrails
|   |-- retrieval/                  # Chroma retrieval
|   `-- tools/                      # Structured data and mock actions
|-- tests/                         # Automated tests
|-- ai-tooling.md                  # AI tools used and development impact
|-- design-and-evaluation.md       # Architecture and evaluation documentation
|-- deployed.md                    # Public URL, health endpoints, cold starts
|-- requirements.txt
|-- .env.example
`-- README.md
```

## Stage 1: Data and Policy Corpus

The current corpus contains fourteen fictional Northstar Analytics policy documents:

- Ten Markdown documents
- Four page-aware PDF documents

The policies cover topics such as:

- Employee handbook rules
- Paid time off
- Remote and hybrid work
- International remote work
- Information security
- Data classification
- Business expenses
- Business travel
- Benefits enrollment
- Employee onboarding
- Family and medical leave
- Workplace conduct
- Anti-harassment and discrimination
- Performance review and development

Two fictional CSV datasets are stored under `data/structured/`:

- Employee roster
- PTO balances

The structured CSV files support the Stage 4 agent workflows and the Stage 5 MCP employee and PTO tools. They are not added to the policy corpus.

## Stage 2: Ingestion and Vector Indexing

### Loading

`src/ingestion/loaders.py` supports:

- Markdown as one source document
- PDF as one parsed unit per nonempty page
- CSV as one parsed unit per populated row

Each parsed unit carries citation metadata such as title, source path, source type, page, or row.

### Chunking

`src/ingestion/chunkers.py` uses:

- Maximum chunk size: 200 tokens
- Token overlap: 30 tokens
- Heading-aware Markdown sections
- Page-preserving PDF chunks
- Row-preserving CSV chunks

Each chunk receives:

- `title`
- `source`
- `source_type`
- `section`
- `page` or `row`, when applicable
- `chunk_index`
- `token_count`
- `source_snippet`

### Embeddings

The project uses Chroma's free local default embedding function:

```text
all-MiniLM-L6-v2
```

Each embedding contains 384 dimensions. Query embeddings use the same function and dimensionality as indexed policy chunks.

### Vector Storage

The persistent Chroma collection is:

```text
northstar_policies
```

It uses cosine distance and is stored under `chroma_db/`.

The validated policy index contains 267 citation-bearing chunks across fourteen policy files:

- 216 Markdown chunks
- 51 page-aware PDF chunks

### Rebuild the Index

From the repository root:

```bash
python scripts/build_policy_index.py
```

The script:

1. Loads the policy documents.
2. Creates citation-friendly chunks.
3. Generates local embeddings.
4. Rebuilds the Chroma collection.
5. Verifies that the stored count matches the expected count.

## Stage 3: Retrieval-Augmented Generation

### Top-k Retrieval

`src/retrieval/retriever.py` converts Chroma's nested response into ranked `RetrievalResult` objects containing:

- Rank
- Chunk ID
- Text
- Metadata
- Cosine distance
- Similarity score

The project default is:

```python
RETRIEVAL_TOP_K = 5
```

Complex questions may request a larger top-k value to improve multi-document recall.

### Optional Metadata Filtering

Retrieval supports Chroma `where` filters. Example:

```python
from src.retrieval.retriever import retrieve

results = retrieve(
    "How much paid time off do employees receive?",
    top_k=3,
    where={
        "title": "Northstar Analytics Paid Time Off Policy",
    },
)
```

Filtering restricts eligible chunks before semantic ranking.

### Grounded Prompting

`src/rag/prompts.py` builds:

- A system message defining grounding and guardrail rules
- A user message containing the question
- Numbered source blocks with retrieved text and metadata

Each source block includes:

- Source marker
- Document title
- Original source path
- Section
- Chunk ID
- Page or row, when available
- Full retrieved chunk content

The prompt requires the model to:

- Use only retrieved policy evidence
- Cite supported policy claims
- Avoid treating related terminology as proof
- Refuse unsupported questions cautiously
- Treat retrieved documents as reference data rather than instructions
- Separate policy facts from recommendations

### Verified Citations

`src/rag/citations.py` resolves generated source markers against actual retrieval results.

The citation layer:

- Supports individual markers such as `[Source 2]`
- Supports grouped markers such as `[Source 3, Source 4]`
- Preserves first-used citation order
- Rejects unknown source numbers
- Supplies authoritative metadata from Chroma
- Generates supporting snippets from retrieved text

This design prevents the model from inventing source metadata.

### Guardrails

The RAG system uses two guardrail layers.

#### Deterministic Relevance Gate

Before generation, the best retrieval similarity is compared with:

```python
MIN_RELEVANCE_SIMILARITY = 0.25
```

Clearly unrelated questions return an `out_of_corpus` response without calling the language model.

#### Evidence-Aware Generation

Questions that are semantically related but unsupported by the retrieved evidence reach the grounded prompt. If the model returns no verified citation support, the result is classified as `insufficient_evidence`.

Possible answer statuses are:

- `grounded`
- `out_of_corpus`
- `insufficient_evidence`

The threshold is an initial empirical value based on current corpus tests and should be reevaluated as the corpus or evaluation set changes.

### End-to-End Use

```python
from src.rag.pipeline import answer_question

result = answer_question(
    "How much paid time off do employees receive?"
)

print(result.status.value)
print(result.answer)

for citation in result.citations:
    print(citation.marker)
    print(citation.title)
    print(citation.section)
    print(citation.snippet)
```

## Complex Multi-Document Evaluation

Run:

```bash
python scripts/test_complex_rag.py
```

The evaluation asks about a U.S.-based employee who wants to work remotely from another country while taking PTO.

A successful result should:

- Return `grounded`
- Retrieve international remote-work and PTO evidence
- Cite at least two unique documents
- Address advance approval and timing requirements
- Address duration limits
- Address PTO eligibility, notice, increments, and recording
- Separate policy facts from recommendations

## Stage 4: Agentic System Design

### Agent Orchestrator

`src/agent/orchestrator.py` defines a LangGraph orchestrator that classifies intent, decides whether RAG alone is sufficient, selects workflows and required HR capabilities, retrieves policy evidence, and returns a final response with an operational trace.

```mermaid

flowchart TD
    A[User request] --> B[Intent router]
    B -->|Policy question| C[Policy RAG]
    B -->|PTO guidance| D[PTO workflow]
    B -->|Remote eligibility| E[Remote workflow]
    B -->|Ambiguous| F[Clarification]
    C --> G[Response and trace]
    D --> G
    E --> G
    F --> G
```

Routing is deterministic for supported workflows. This makes tool selection predictable and prevents the language model from independently authorizing actions.

### Multi-Step Workflows

The PTO workflow:

1. Looks up the employee through MCP.
2. Retrieves the PTO balance through MCP.
3. Retrieves applicable PTO policies through RAG.
4. Checks requested days against the available balance.
5. Requests missing details when necessary.
6. Requires explicit confirmation before a mock submission.

The remote-work workflow:

1. Looks up the employee through MCP.
2. Uses job, department, work arrangement, office, and country context.
3. Retrieves remote, hybrid, security, and international policies.
4. Provides preliminary eligibility guidance.
5. Identifies required human review.
6. Clearly states that the response is not final approval.

### Operational Trace

Every agent response can include:
- Intent and RAG-sufficiency decision
- Selected tools
- Tool arguments and outputs
- Retrieved policy sources
- Similarity and citation status
- Final answer basis
- Confirmation state
- Escalation decision

The trace contains operational events only and does not expose hidden chain-of-thought.

### Safety and Failure Handling

The agent safely handles missing identifiers, unknown employees, ambiguous requests, unavailable MCP tools, missing action details, insufficient PTO balances, out-of-corpus questions, insufficient policy evidence, and model-service failures.

All HR actions remain mock-only. Even after confirmation, no ticket, message, employee record, or production HR system is changed.

### Run the Agent

Policy question:

```bash
PYTHONPATH=. python scripts/run_agent.py "What expenses require manager approval?"
```

PTO guidance:

```bash
PYTHONPATH=. python scripts/run_agent.py "What is my PTO balance?" --work-email maya.chen@northstaranalytics.com
```

Remote-work guidance:

```bash
PYTHONPATH=. python scripts/run_agent.py "Am I eligible to work remotely?" --work-email maya.chen@northstaranalytics.com
```

Mock PTO request:

```bash
PYTHONPATH=. python scripts/run_agent.py "Submit a PTO request" --work-email maya.chen@northstaranalytics.com --start-date 2026-10-12 --end-date 2026-10-14 --requested-days 3
```

Add `--confirm` to explicitly confirm the mock action. Add `--show-trace` to display the operational trace as JSON.

## Setup

Clone the repository and enter the project directory:
```bash
git clone https://github.com/laquiliadproductions/northstar-hr-agent.git
cd northstar-hr-agent
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Copy the public environment template:

```bash
cp .env.example .env
```

Edit `.env` and add a private provider key:

```dotenv
LLM_PROVIDER=groq
LLM_API_KEY=your_private_key_here
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-120b
```

Never place a real key in `.env.example`, source code, documentation, tests, screenshots, or commits.

## Configuration

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | Informational provider name |
| `LLM_API_KEY` | Private provider credential |
| `LLM_BASE_URL` | OpenAI-compatible API endpoint |
| `LLM_MODEL` | Provider-specific chat-model identifier |
| `PYTHONHASHSEED` | Set before starting Python to make hash randomization repeatable |

Provider details are environment-based. The RAG application code does not hard-code a specific API key or endpoint.

## Run the Web App Locally

From the activated virtual environment, build the local policy index once (and again whenever policy documents change):

```bash
python scripts/build_policy_index.py
```

Set the Python hash seed before starting the process, then start Flask:

Linux or macOS:

```bash
export PYTHONHASHSEED=42
python -m flask --app src.web.app run --host 127.0.0.1 --port 8000
```

Windows PowerShell:

```powershell
$env:PYTHONHASHSEED = "42"
python -m flask --app src.web.app run --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`. The local app reads the provider settings from `.env`; `LLM_API_KEY` must contain a valid key for the configured OpenAI-compatible provider. The first local embedding run may need an internet connection to download the embedding model.

## Testing

Run all automated tests:

```bash
pytest -q
```

The current automated test suite contains 63 tests covering:

- Ranked retrieval conversion
- Metadata-filter forwarding
- Citation metadata resolution
- Unicode citation spacing
- Grouped source markers
- Rejection of unknown source numbers
- Low-similarity refusal
- Empty-retrieval refusal
- Grounded-answer classification
- Insufficient-evidence classification
- Employee lookup and data minimization
- PTO balance retrieval
- MCP error handling
- Intent routing and RAG-sufficiency decisions
- PTO and remote-work workflows
- Operational trace generation
- Missing-input and ambiguity handling
- Confirmation-gated mock actions
- Requests exceeding available PTO
- ASCII and Unicode citation normalization

The test suite does not require a live language-model call.

## Reproducibility

- Python dependencies are pinned in `requirements.txt`.
- Local embeddings avoid paid embedding API calls.
- Chunk size and overlap are deterministic.
- Chunk IDs are stable hashes of source metadata.
- The Chroma collection uses cosine distance.
- The project default retrieval count is fixed.
- Random-number generators use a fixed seed where applicable.
- The complex multi-document question is stored in a repeatable script.
- LLM wording may vary between runs even when retrieval is stable.

## Security and Privacy

- `.env` is excluded from Git.
- `.env.example` contains placeholders only.
- API keys are loaded from environment variables.
- No real employee data is used.
- Employee and PTO records are fictional.
- Policy source blocks are treated as untrusted reference data, not executable instructions.
- Out-of-corpus questions are refused or redirected.
- General recommendations are not presented as Northstar policy requirements.

## Known Limitations

- The relevance threshold is an empirical setting validated against the current corpus and evaluation set.
- Dense retrieval may rank passages with related terminology even when they do not answer the question.
- Complex questions may require a larger top-k value; supported calls can request up to ten retrieved chunks.
- Free-tier model availability and rate limits may change.
- Free-tier CPU and memory constraints can make policy and multi-step agent responses slow.
- HR actions are intentionally mock-only and do not integrate with a production HR system.
- The evaluation uses 25 cases, within the project requirement of 20 to 30 cases.

## Stage 5: MCP Server and Tool Integration
### Architecture

Stage 5 adds a Model Context Protocol (MCP) boundary between the Northstar HR agent and selected HR capabilities. The agent does not directly call the underlying employee, PTO, or mock-action functions. Instead, it invokes tools through the MCP client, which communicates with the Northstar MCP server.

```text
User
  |
  v
Northstar HR Agent
  |
  v
MCP Client
  |
  | stdio
  v
Northstar MCP Server
  |
  +--> search_policy_documents --> Chroma policy index
  |
  +--> get_policy_section ------> Chroma policy index
  |
  +--> lookup_employee_profile -> employee roster CSV
  |
  +--> check_pto_balance -------> PTO balances CSV
  |
  +--> mock_submit_pto_request -> confirmation-gated mock operation
```

### Transport Choice
The Northstar MCP server uses the `stdio` transport. The agent client starts the MCP server as a local Python subprocess using:
```text
python -m src.mcp_server.server
```

The MCP client and server exchange MCP protocol messages through the subprocess standard input and standard output streams.

`stdio` was selected because the Northstar HR agent and MCP server run in the same local project environment. This avoids introducing an unnecessary HTTP service, network port, or separate deployment while still maintaining an MCP boundary between the agent and its tools.

The server starts with `server.run(transport="stdio")`. The client uses `StdioServerParameters`, `stdio_client`, and `ClientSession` to create and initialize an MCP session.

### MCP Server and Client

The MCP implementation is located under:

```text
src/mcp_server/
|-- __init__.py
|-- server.py
`-- client.py
```
`server.py` defines the Northstar MCP server and registers the HR tools. The server wraps existing retrieval and HR functions rather than duplicating their business logic.
`client.py` provides the agent-side MCP adapter. It starts the local server process, initializes an MCP `ClientSession`, invokes tools by name with structured arguments, and converts MCP responses into controlled Python dictionaries for the agent workflows.

### MCP Tool Discovery
MCP clients can discover the server's available capabilities by initializing a session and calling `list_tools()`.

Example:
```python
async with stdio_client(SERVER_PARAMETERS) as streams:
    read_stream, write_stream = streams

    async with ClientSession(read_stream, write_stream) as session:
        await session.initialize()
        result = await session.list_tools()

        for tool in result.tools:
            print(tool.name)
            print(tool.description)
            print(tool.input_schema)
```

The server currently advertises five MCP tools:

```text
search_policy_documents
get_policy_section
lookup_employee_profile
check_pto_balance
mock_submit_pto_request
```

Tool discovery returns each tool's name, description, and machine-readable input schema. The schemas are derived from the registered Python tool signatures and type annotations.

### MCP Tool Schemas

#### `search_policy_documents`

Searches the persistent Chroma policy index for semantically relevant policy evidence.

Inputs:

- `query` - required string containing the policy question or search terms
- `top_k` - optional integer specifying the number of results; defaults to 5 and is limited to 1 through 10

Returns ranked policy chunks containing:

- Rank
- Chunk ID
- Retrieved text
- Document title
- Source path
- Section
- Page or row when available
- Similarity score

This tool satisfies the requirement for an MCP tool that uses the RAG index.

#### `get_policy_section`

Retrieves policy evidence from a specific indexed policy section using Chroma metadata filtering.

Inputs:

- `section` - required section name
- `policy_title` - optional policy title used to further restrict retrieval
- `top_k` - optional result limit; defaults to 5 and is limited to 1 through 10

The tool returns matching policy chunks and citation-related source metadata. If no indexed evidence matches the requested section, it returns a controlled `not_found` response.

#### `lookup_employee_profile`

Looks up one fictional Northstar employee from the structured employee roster.

Inputs:

- `work_email` - optional employee work email
- `full_name` - optional exact employee full name

At least one employee identifier must be supplied. The tool returns only fields required by supported HR workflows rather than the complete roster record.

This tool uses the fictional structured dataset stored at:

```text
data/structured/Northstar_Analytics_Employee_Roster.csv
```

#### `check_pto_balance`

Looks up one fictional employee's PTO balance.

Inputs:

- `employee_id` - optional employee ID
- `work_email` - optional employee work email

At least one identifier must be supplied. The tool returns fields including annual allowance, accrued PTO, used PTO, pending requests, current balance, available balance after pending requests, and the balance date.

This tool uses:

```text
data/structured/Northstar_Analytics_PTO_Balances.csv
```

#### `mock_submit_pto_request`

Previews or simulates a PTO request without modifying a real HR system.

Inputs:

- `employee_id`
- `start_date`
- `end_date`
- `requested_days`
- `confirmed`

When `confirmed` is false, the tool returns `confirmation_required` with a request preview and performs no action.

When `confirmed` is true and the request passes validation, the tool returns `mock_completed` with a synthetic `MOCK-PTO-*` request ID.

The tool always reports:

```text
side_effects: none
```

No real HR system, employee record, or PTO balance is changed.

### Tool Validation and Controlled Results

The MCP tools return structured status values so agent workflows can handle failures and incomplete information without relying on unstructured exception text.

Supported outcomes include:

```text
ok
needs_clarification
invalid_request
not_found
unavailable
confirmation_required
mock_completed
tool_error
tool_unavailable
```

Examples of validation include:

- Policy search `top_k` must be between 1 and 10.
- Employee lookup requires a work email or exact full name.
- PTO lookup requires an employee ID or work email.
- Unknown policy sections return `not_found`.
- PTO request dates must be valid ISO dates.
- PTO request end dates cannot precede start dates.
- Requested PTO days must be greater than zero.
- Mock submissions require explicit confirmation.

### Agent Tool Invocation

The agent invokes MCP-exposed tools through `src/mcp_server/client.py`. It does not directly invoke the underlying employee, PTO, or mock-action functions from its workflows.

For example, the PTO workflow calls:

```python
employee_result = await call_hr_tool(
    "lookup_employee_profile",
    {"work_email": work_email},
)
```

and:

```python
pto_result = await call_hr_tool(
    "check_pto_balance",
    {"work_email": work_email},
)
```

The confirmation-gated PTO action similarly invokes:

```python
output = await call_hr_tool(
    "mock_submit_pto_request",
    arguments,
)
```

The resulting execution path is:

```text

Agent workflow
      |
      v
call_hr_tool()
      |
      v
MCP ClientSession
      |
      | stdio
      v
Northstar MCP Server
      |
      v
Registered MCP tool
      |
      v
Existing retrieval / structured-data / mock-action backend
```

Operational traces record the selected MCP tool, its arguments, its structured result, and the workflow decision based on that result.

### Policy Retrieval Architecture

Stage 5 exposes policy retrieval through MCP with `search_policy_documents` and `get_policy_section`.

The established Stage 3 grounded-answer pipeline remains available to the Stage 4 agent workflows for full policy answer generation and citation verification. This pipeline retrieves policy evidence, applies the relevance guardrail, generates a grounded answer, resolves source markers, and validates citations.

This means the system supports both:

```text
MCP policy evidence retrieval
    -> search_policy_documents
    -> get_policy_section
```

and:

```text
Grounded policy answer generation
    -> existing RAG pipeline
    -> citation validation
```

The employee, PTO, and mock-action capabilities used by the Stage 4 workflows are invoked through MCP.

### Verified MCP Execution

Stage 5 was verified through MCP discovery, direct MCP calls, validation tests, and end-to-end agent execution.

Verified behaviors include:

- Discovery of all five tools with `list_tools()`
- Semantic policy retrieval from the Chroma index through `search_policy_documents`
- Metadata-filtered policy retrieval through `get_policy_section`
- Employee lookup through `lookup_employee_profile`
- PTO balance lookup through `check_pto_balance`
- Confirmation-gated mock PTO submission through `mock_submit_pto_request`
- Controlled handling of invalid, missing, and unknown inputs
- Agent execution that invokes MCP tools rather than directly calling their backend functions

A successful PTO workflow demonstrated the following sequence:

```text
intent_routing
    |
    v
lookup_employee_profile       [MCP]
    |
    v
check_pto_balance             [MCP]
    |
    v
policy_retrieval_and_answering
    |
    v
mock_submit_pto_request       [MCP]
    |
    v
response_synthesis
```

With explicit confirmation, the mock PTO operation returns a synthetic request reference while leaving all HR records unchanged.

### Running the MCP-Integrated Agent

Because the project uses the `src` package from the repository root, the command-line agent can be run with:

```bash
PYTHONPATH=. python scripts/run_agent.py "What is my PTO balance?" --work-email maya.chen@northstaranalytics.com --show-trace
```

A confirmation-gated mock PTO request can be demonstrated with:

```bash
PYTHONPATH=. python scripts/run_agent.py "Request PTO for me" --work-email maya.chen@northstaranalytics.com --employee-id NSA-0001 --start-date 2026-10-15 --end-date 2026-10-16 --requested-days 2 --show-trace
```

The same request can be explicitly confirmed by adding:

```text
--confirm
```

All PTO submission behavior is simulated for demonstration purposes.

## Stage 6 - Web Application

The Northstar HR Agent is available through its public Render Flask web application.

### Public URL

https://northstar-hr-agent-5uub.onrender.com/

### Endpoints

- `GET /`
  - Opens the Northstar HR chatbot interface.

- `POST /chat`
  - Accepts HR policy and workflow requests.
  - Returns:
    - final answer
    - citations
    - supporting snippets
    - concise agent trace
    - intent
    - confirmation and escalation status

- `GET /health`
  - Returns application status and MCP connectivity status.

- `GET /ready`
  - Returns readiness status for the deployed service.

Example health response:

```json
{
  "app": "northstar-hr-agent",
  "mcp": {
    "status": "ok",
    "tool_count": 5
  },
  "status": "ok"
}
```
### Demo Instructions

Open the public chatbot and type:

```text
Demo
```

The chatbot will display reproducible example queries.

#### Demo 1 - PTO Workflow

```text
How much PTO do I have available? My email is maya.chen@northstaranalytics.com
```

This demo exercises:

1. Intent routing
2. MCP employee lookup
3. MCP PTO balance lookup
4. PTO policy RAG retrieval
5. Grounded response synthesis

#### Demo 2 - Remote Work Eligibility

```text
Am I eligible for remote work? My email is maya.chen@northstaranalytics.com
```

This demo exercises:

1. Intent routing
2. MCP employee lookup
3. Remote-work policy RAG retrieval
4. Preliminary eligibility guidance
5. Grounded response synthesis

### Conversational Employee Identification

Employee-specific requests can also be completed as a multi-turn conversation.

Example:

```text
User:
How much PTO do I have?

Northstar:
Provide the employee's work email or exact full name.

User:
maya.chen@northstaranalytics.com
```

When the employee provides the requested email, the chatbot preserves the pending request and resumes the original workflow using the supplied employee identity.

An employee email may also be included directly in the original request:

```text
How much PTO do I have available? My email is maya.chen@northstaranalytics.com
```

### Agent Transparency

Grounded policy responses display:

- The final HR response
- Cited policy sources
- Supporting policy excerpts
- A collapsible concise agent trace

The agent trace allows the grader to inspect the major routing, retrieval, and tool-use steps without exposing internal reasoning.

### Testing

Run the complete automated test suite from the project root:

```bash
python -m pytest -q
```

Current full-suite validation result:

```text
63 passed
```
## Stage 7 - Render Deployment

The Northstar HR Agent is configured for a zero-cost, single-service deployment on Render.

### Deployment Architecture

The Render web service runs the complete application:

- Flask web interface and HTTP endpoints
- Gunicorn production web server
- LangGraph agent orchestrator
- Local stdio MCP server process
- Chroma policy vector store
- Committed fictional policy and structured HR data

The MCP server remains behind the application boundary and is started locally through the stdio client. No separate MCP hosting service or paid database is required.

### Render Configuration

Deployment is defined in `render.yaml`.

```text
Runtime: Python 3.12
Plan: Free
Health check: /ready
```

Build command:

```bash
pip install -r requirements.txt && python scripts/build_policy_index.py
```

Start command:

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 src.web.app:app
```

The build command installs the pinned dependencies and rebuilds the local Chroma index from the committed policy documents. The validated index contains 267 chunks across fourteen policy files.

### Environment Variables

The Render service requires:

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | Provider label; currently `groq` |
| `LLM_API_KEY` | Private Groq API credential |
| `LLM_BASE_URL` | OpenAI-compatible Groq endpoint |
| `LLM_MODEL` | Deployed model identifier |
| `PYTHONHASHSEED` | Set before starting Python to make hash randomization repeatable |

`LLM_API_KEY` is entered as a private Render environment variable and is never committed to Git.

### Storage

The application does not require a paid database or persistent disk.

- Fictional policy documents and structured CSV data are committed to the repository.
- The `chroma_db/` directory is generated during each Render build.
- Runtime filesystem changes are treated as ephemeral.
- Mock PTO submissions do not modify persistent HR records.

### Public Render URL

[https://northstar-hr-agent-5uub.onrender.com](https://northstar-hr-agent-5uub.onrender.com)

Deployment status: Live and validated with the readiness endpoint, MCP health check, policy RAG query, and employee-specific PTO workflow.

### Free-Tier Cold Starts

Render free web services spin down after periods of inactivity. The first request after a spin-down can take a minute or longer while the service starts. During a cold start, the browser may appear to wait before the chatbot loads.
Even while the service is active, policy retrieval and multi-step agent workflows may respond slowly because the free instance has limited CPU and memory and the application performs local embedding, vector retrieval, MCP subprocess, and external model operations. The free service has limited CPU and memory, so policy and multi-step responses can be slow.

If this occurs:

1. Wait for the initial request to complete.
2. Refresh the page if necessary.
3. Submit the demo request after the interface loads.

Requests made while the service remains active should respond more quickly. Cold-start delay is expected free-tier behavior and does not indicate that the application is unavailable.

### Deployment Validation

After each deployment:

1. Open the public application URL.
2. Confirm that `/ready` returns HTTP 200.
3. Confirm that `/health` reports application and MCP status.
4. Submit a general policy question and verify grounded citations.
5. Submit an employee-specific PTO question and verify MCP tool use.
6. Confirm that no real HR data or production system is modified.

## Stage 8: CI/CD

GitHub Actions runs the project checks on pushes and pull requests. The workflow installs the pinned dependencies, performs an application import or startup check, runs the automated test suite, and verifies MCP tool discovery or a tool call. Deployment is gated on successful checks.

To review the latest result, open the repository's **Actions** tab and select the most recent workflow run for the branch being submitted. The workflow run is the source of truth for the current pass/fail status.

## Section 9: Agentic RAG Evaluation

The evaluation suite contains 25 machine-readable cases covering policy Q&A, multi-document questions, tool-requiring workflows, ambiguous requests, and out-of-scope or unsafe requests.

### Evaluation Artifacts

- [Evaluation set](evaluation/northstar_section9_evaluation_set.json)
- [Final consolidated results](evaluation/results/section9_consolidated_final_results.json)
- [Final evaluation report](evaluation/results/section9_final_report.json)
- [Test documentation](evaluation/northstar_section9_evaluation_test_documentation_final.docx)
- [Evaluation instructions](evaluation/README.md)

### Final Results

| Metric | Result |
| --- | ---: |
| Evaluation cases | 25/25 passed |
| Groundedness | 100% across 22 applicable cases |
| Citation accuracy | 100% across 22 applicable cases |
| Gold-answer partial match | 71.49% mean |
| Tool-selection accuracy | 100% |
| Workflow completion | 100% |
| Clarification or escalation accuracy | 100% |
| Action-safety pass rate | 100% |
| Automated tests | 63 passed |

Applicable evaluation metrics appear in the chatbot's **Agent Trace**, including answer quality, agent behavior, safety, latency, run condition, retrieval configuration, and evaluation case.

The primary evaluation run completed 23 cases; two additional attempts were interrupted by confirmed retrieval-service failures and were marked Not Scored. Those two cases were rerun after service recovery. All 25 cases passed their criteria on completed, scored attempts. The interrupted attempts remain documented as reliability evidence. The 71.49% gold-answer partial match is a supplementary lexical-overlap measure, not an answer-correctness rate; semantically equivalent wording and required context can lower the score. The 100% results apply to the 22 cases where the corresponding metrics were applicable.

### Latency and Free-Tier Behavior

A 15-query representative baseline measured approximately 10,240 ms at p50 and 15,924 ms at p95. Cold-start and warm-start measurements are reported separately in the evaluation results. These are application request timings; the separate Render wake-up delay after spin-down can be longer.

Confirmed external quota, rate-limit, timeout, or provider-connectivity interruptions are classified as **Not Scored**, not as incorrect answers. Interrupted attempts are rerun when service becomes available and remain preserved as system-reliability and safe-handling evidence.

### Retrieval Ablation

The `k=3` configuration passed 91.67% of 12 representative cases, while `k=5` passed 100%. The application retains `k=5` because it produced stronger groundedness, citation accuracy, and gold-answer coverage, with higher documented latency.

### Run the Evaluation

The full evaluation consumes external language-model tokens:

`python scripts/run_evaluation.py --mode baseline --delay-seconds 8 --service-retries 1 --retry-backoff-seconds 60`

Run the automated tests without consuming language-model tokens:

`pytest -q`

## AI Tooling and Required Submission Files

OpenAI Codex/ChatGPT was used to assist with implementation, debugging, setup guidance, and documentation. This helped accelerate routine coding and troubleshooting; generated suggestions were reviewed against the project requirements and checked through manual and automated tests. The companion `ai-tooling.md` file records these uses, what worked well, and what required correction or verification.

The required companion files are included with this README and should be committed at the repository root:

- `design-and-evaluation.md` - architecture, RAG and MCP design, guardrails, evaluation questions, expected answers, and results.
- `deployed.md` - deployed application URL, health endpoint, and free-tier cold-start notes.
- `ai-tooling.md` - AI development tools used and their impact.
- `evaluation/` - evaluation cases, expected answers or rubrics, scripts, and reported results.
- `src/mcp_server/` or equivalent - MCP server code and tool definitions.
- `data/structured/` or equivalent - clearly synthetic structured HR data.

The companion files contain the corresponding design/evaluation, deployment, and AI-tooling details. The README also provides an integrated project overview.

### Project Submission Checklist

- Share the GitHub repository with the `quantic-grader` account.
- Submit the GitHub repository link and recorded demo presentation link through the course submission page.
- Record a 7-10 minute screen-share with voiceover showing the deployed application completing both agentic workflows end to end.
- For a group submission, every member must speak, appear on camera, and show government ID, as required by the project brief.
- Include the deployed application URL in this README and keep the companion documentation and evaluation artifacts committed to the repository.

## Section 10: Design Documentation

### 10.a Design choices

#### 10.a.1 Agent framework and orchestration

Northstar uses LangGraph to orchestrate its agent workflows. The workflows need to route between policy-only questions and multi-step PTO or remote-work requests, carry state between steps, and record an operational trace. A graph makes these branches and handoffs explicit, which supports testing and troubleshooting. Deterministic application logic handles safety decisions, while the language model generates grounded responses.

#### 10.a.2 MCP server design and transport

The MCP server exposes policy retrieval and mock HR data or action functions as tools, while reusing the existing application functions for their business logic. The agent connects to this local server as a subprocess over `stdio`. This transport fits the single-service Render deployment: the web app, agent, and MCP server run in the same project environment, so a separate network service and port are unnecessary. MCP still gives the agent a defined tool boundary.

#### 10.a.3 MCP client discovery and calls

The client initializes an MCP session with the local server, calls `list_tools()` to discover tool names, descriptions, and input schemas, and invokes selected tools by name with structured arguments. It normalizes tool results for the agent workflows.

#### 10.a.4 MCP tool schemas

All five MCP tools return structured data. Policy tools return ranked matches with source metadata; their `top_k` argument defaults to 5 and must be between 1 and 10. The tool contracts are:

- `search_policy_documents(query: string, top_k: integer = 5)` searches policy evidence by meaning.
- `get_policy_section(section: string, policy_title: string | null = null, top_k: integer = 5)` retrieves evidence filtered by section and, optionally, policy title.
- `lookup_employee_profile(work_email: string | null = null, full_name: string | null = null)` looks up one employee using a work email or exact full name.
- `check_pto_balance(employee_id: string | null = null, work_email: string | null = null)` retrieves one employee's PTO balance.
- `mock_submit_pto_request(employee_id: string | null = null, start_date: string | null = null, end_date: string | null = null, requested_days: number | null = null, confirmed: boolean = false)` previews or simulates a PTO request; confirmation is required for the mock action, and no real HR record is changed.

Policy tools return controlled statuses such as `ok`, `not_found`, `invalid_request`, and `unavailable`, so the agent can distinguish results from errors and missing evidence.
Narrow, typed arguments keep calls predictable, and the bounded `top_k` limits request size.

#### 10.a.5 Embedding model

The project uses Chroma's local default embedding function, `all-MiniLM-L6-v2`, to embed both policy chunks and search queries. It produces 384-dimensional vectors, keeping document and query embeddings compatible while avoiding a separate paid embedding API.

#### 10.a.6 Chunking strategy

Policy documents are split into overlapping, token-aware chunks with a maximum size of 200 tokens. PDF chunks retain their page references, and CSV chunks retain their row references. Chunk metadata records source and section information so retrieved passages can be cited and traced back to the original material.
Overlap preserves context across chunk boundaries, while the size limit keeps passages focused and source-location metadata supports citations.

#### 10.a.7 Retrieval k

Policy retrieval defaults to `k=5`, returning the five highest-ranked chunks. This provides several passages to ground an answer while keeping the context manageable. The MCP policy tools accept values from 1 through 10 when a workflow needs a narrower or broader result set.

#### 10.a.8 Vector store

ChromaDB stores the policy vectors and citation metadata in the local `chroma_db/` directory and uses cosine distance for similarity ranking. Its local persistence fits the project's policy corpus and works with Chroma's local embedding function, without requiring a separately hosted vector database.

#### 10.a.9 Deployment architecture

The application is deployed as a single Render web service that hosts the chat UI, chat API, LangGraph orchestrator, MCP client, and local MCP server process. The MCP server starts over `stdio` within the service. Mock employee and PTO data remain in the project, and the Chroma index is built from the committed policy documents during deployment. The application calls the configured OpenAI-compatible LLM provider using environment-based settings. This single-service layout keeps the deployment and operations simple without requiring a separate MCP host, vector database, or production HR system.

#### 10.a.10 Safety guardrails

The agent answers policy questions from retrieved Northstar sources, and application code validates citations against those sources. It applies a relevance check before generation and can return an insufficient-evidence response when support is missing. Retrieved documents are treated as reference data rather than instructions. Employee data is limited to supported HR workflows, sensitive matters can be escalated, and the mock PTO action requires explicit confirmation. The system never claims that a mock action changed a real HR record.

### 10.b Architecture

```mermaid
flowchart TD
    USER["User"] --> WEB["Render web app (chat UI, chat API)"]
    WEB --> AGENT["LangGraph agent orchestrator"]
    AGENT --> CLIENT["MCP client"]
    CLIENT -->|"stdio"| SERVER["Local MCP server"]
    SERVER --> MOCK["Mock employee and PTO data"]
    SERVER --> INDEX["Chroma policy RAG index"]
    AGENT --> RAG["Grounded RAG pipeline"]
    RAG --> INDEX
    RAG --> LLM["External LLM provider"]
    LLM --> RAG
    SERVER --> AGENT
    RAG --> AGENT
    AGENT --> WEB
    WEB --> USER

```

The web app, orchestrator, MCP client and server, mock data, and Chroma index run within the Render service. The LLM provider is called externally. MCP policy tools and the grounded RAG pipeline can both retrieve policy evidence from the Chroma index.
### 10.c Demo tasks and MCP call sequences

#### 10.c.1 PTO request guidance

Demo prompt: Can I take three days of PTO next week?

Expected sequence:
1. Call `lookup_employee_profile` with the user work email or exact full name.
2. If the employee is identified, call `check_pto_balance` using the work email returned by the profile lookup.
3. Run the grounded RAG pipeline to retrieve PTO policy evidence. In this workflow, policy retrieval is separate from the MCP calls. The pipeline sends the retrieved passages to the configured LLM, which generates the cited response.
4. Use the balance and policy evidence to explain eligibility, approval requirements, and next steps.

If the user later asks to submit a mock request, call `mock_submit_pto_request` only after explicit confirmation. The mock action does not change a real HR record.

#### 10.c.2 Remote-work eligibility

Demo prompt: May I work remotely from another state or country for six weeks?

Expected sequence:
1. Call `lookup_employee_profile` with the user work email or exact full name.
2. If the employee is identified, run the grounded RAG pipeline to retrieve applicable remote-work, security, tax or location, and approval policies. Policy retrieval is separate from the MCP call in this workflow.
3. The configured LLM uses the employee profile and retrieved policy evidence to generate cited guidance and next steps.
4. If the evidence is incomplete or the case requires approval, explain the limitation and direct the employee to the appropriate HR or manager contact.

Expected MCP call trace: `lookup_employee_profile` with the supplied work email or full name, followed by the returned employee profile. The policy sources and citations appear in the RAG trace.
