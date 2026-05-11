# Nasscom Hackathon - L1 IT Support Agent System

## Complete Project Documentation

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Solution Components](#solution-components)
4. [Data Model](#data-model)
5. [Data Sources & Data Engineering](#data-sources--data-engineering)
6. [Low Level Design (LLD)](#low-level-design-lld)
7. [Data Flow Diagram (DFD)](#data-flow-diagram-dfd)
8. [Sequence Diagrams](#sequence-diagrams)
9. [State Transition Diagram](#state-transition-diagram)

---

## Project Overview

### Project Name

**L1 IT Support Supervisor Agent System (Multi-Agent AI System)**

### Objective

Build an intelligent multi-agent system that automates L1 IT support by:

- Classifying incoming support requests
- Retrieving solutions from a knowledge base (RAG - Retrieval Augmented Generation)
- Creating tickets in the ServiceNow system when needed
- Managing conversation state and routing between specialized agents

### Technology Stack

- **LLM**: Amazon Bedrock (Nova Lite v1 Model)
- **Orchestration**: LangGraph (Agentic Framework)
- **Vector DB**: ChromaDB Cloud (Incident Knowledge Base)
- **Embedding Model**: Sentence Transformers (all-MiniLM-L6-v2)
- **Backend**: Python 3.12+
- **Infrastructure**: AWS (Lambda, Bedrock, ChromaDB Cloud)
- **Data Processing**: Pandas, NumPy
- **Dependencies**: LangChain, LangGraph, Boto3, Pydantic

### Key Features

1. **Multi-Agent Architecture**: Supervisor, RAG Agent, Ticket Agent
2. **Intelligent Routing**: Dynamic routing based on issue type and context
3. **Knowledge Base Integration**: Vector search on closed tickets
4. **Ticket Management**: Create and lookup tickets via ServiceNow Lambda APIs
5. **State Management**: Persistent state tracking with memory checkpoints
6. **Issue Classification**: Automatic categorization and priority assignment

---

## System Architecture

### High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     USER INTERFACE LAYER                             │
│                    (Chat Input / User Query)                         │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                               │
│                  (LangGraph State Machine)                           │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │         Supervisor Agent (Routing Logic)                    │  │
│   │    - Routes based on issue type & state                     │  │
│   │    - Manages conversation flow                              │  │
│   └──────────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ RAG Agent  │  │Ticket Agent│  │Classification
    │            │  │            │  │    Node
    └────────────┘  └────────────┘  └────────────┘
         │               │
         │               │
    ┌────▼───┐      ┌────▼──────────┐
    │ChromaDB │     │ServiceNow APIs│
    │ Cloud   │     │(via Lambda)   │
    └────────┘      └───────────────┘
         │                │
         ▼                ▼
    ┌────────────────────────────────┐
    │   DATA & EXTERNAL SERVICES     │
    │  - Vector DB (Closed Tickets)  │
    │  - ServiceNow Ticketing System │
    │  - AWS Lambda Functions        │
    └────────────────────────────────┘
```

### Architecture Layers

#### 1. **Presentation Layer**

- Command-line chat interface
- User input collection
- Output display to user

#### 2. **Orchestration Layer (LangGraph)**

- State management with `AgentState`
- Graph-based execution flow
- Three main nodes:
  - **SupervisorAgent**: Main orchestrator
  - **RAGAgent**: Knowledge base lookup
  - **TicketAgent**: Ticket operations

#### 3. **Agent Layer**

- **Supervisor Agent**: Decision-making and routing
- **RAG Agent**: Information retrieval from knowledge base
- **Ticket Agent**: Create/Lookup ticket operations

#### 4. **Tool Layer**

- `RAG_check_node`: Vector search tool
- `create_ticket`: Ticket creation tool
- `lookup_ticket`: Ticket lookup tool

#### 5. **Data & Services Layer**

- **ChromaDB Cloud**: Vector database with incident knowledge base
- **AWS Lambda**: Serverless functions for ticket operations
- **ServiceNow Mock**: Simulated ticketing system
- **Bedrock LLM**: Amazon Nova Lite model for reasoning

---

## Solution Components

### 1. **SupervisorAgent** (Orchestrator)

**Location**: `Agents/SpecificAgent/AgentSupervisor.py`

**Responsibility**:

- Main decision-maker for the system
- Routes incoming queries to appropriate agents
- Manages conversation state and flow
- Classifies issues and assigns priorities

**Input**: `AgentState` with user messages
**Output**: `Command` object specifying next agent and state updates

**Routing Rules**:

```
Input (User Query)
    ↓
Supervisor Analyzes:
    - Issue Category (Infrastructure, Database, Network, etc.)
    - Priority Level (Low, Medium, High, Critical)
    - Assignment Group (DB_ADMIN, NETWORK_TEAM, CLOUD_OPS, SERVICE_DESK)
    ↓
Routes to:
    - RAGAgent: For technical questions (first attempt)
    - TicketAgent: When RAG fails or ticket operations needed
    - END: When issue resolved
```

**Key Logic**:

- First occurrence: Route to RAGAgent for knowledge base search
- If RAG succeeds: Present information to user
- If RAG fails: Route to TicketAgent to create ticket
- On resolution: Route to END

### 2. **RAGAgent** (Knowledge Base Retrieval)

**Location**: `Agents/SpecificAgent/AgentRAG.py`

**Responsibility**:

- Retrieves relevant information from closed tickets
- Searches vector database for similar issues
- Returns solutions from knowledge base

**Process**:

1. Accepts user query
2. Calls `RAG_check_node` tool
3. Searches ChromaDB for similar closed tickets
4. Calculates confidence score (1 - similarity distance)
5. If confidence > 0.7: Returns relevant information
6. If confidence < 0.7: Returns "not relevant" signal

**Output Structure**:

```python
{
    "is_relevant": bool,
    "rag_context": str,  # Retrieved solution
    "rag_tried": bool
}
```

### 3. **TicketAgent** (Ticket Management)

**Location**: `Agents/SpecificAgent/AgentTicket.py`

**Responsibility**:

- Creates new support tickets
- Looks up existing tickets by ID
- Uses two tools: `create_ticket` and `lookup_ticket`

**Operations**:

1. **Ticket Creation**: Collects issue details and creates ticket
2. **Ticket Lookup**: Retrieves ticket information by ID

### 4. **Tools**

#### RAG Tool: `RAG_check_node`

**File**: `Agents/AgentTools/RAGTool.py`

- Vector search on ChromaDB
- Embedding: Sentence Transformers (all-MiniLM-L6-v2)
- Threshold: 0.7 confidence score
- Filters: Only searches closed tickets
- Returns: Relevant solutions with confidence

#### Ticket Creation Tool: `create_ticket`

**File**: `Agents/AgentTools/CreateTool.py`

- Invokes AWS Lambda: `Create_ticket`
- Parameters: title, description, priority, category, assignment_group
- Returns: Ticket ID

#### Ticket Lookup Tool: `lookup_ticket`

**File**: `Agents/AgentTools/LookupTool.py`

- Invokes AWS Lambda: `Lookup_ticket`
- Parameters: ticket_id
- Returns: Full ticket details

### 5. **LLM Model**

**Model**: Amazon Bedrock - Nova Lite v1
**Configuration**:

```python
ChatBedrockConverse(
    model="amazon.nova-lite-v1:0",
    temperature=0,  # Deterministic responses
    region_name='us-east-1',
    credentials: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
)
```

**Purpose**: Reasoning, routing decisions, natural language processing

### 6. **State Management**

**State Class**: `AgentState` (in `utils/utility.py`)

**State Variables**:

```python
class AgentState(MessagesState):
    is_satisfied: bool          # User satisfaction flag
    is_relevant: bool           # RAG relevance score
    category: str               # Issue category
    priority: str               # Issue priority (Low/Medium/High/Critical)
    assignment_group: str       # Target team (DB_ADMIN, NETWORK_TEAM, etc.)
    rag_context: str            # Retrieved knowledge base content
    rag_tried: bool             # Tracks if RAG has been attempted
    next_agent: str             # Next agent in routing
    messages: List[BaseMessage] # Conversation history
```

### 7. **Memory & Checkpointing**

- **Type**: MemorySaver (in-memory storage)
- **Persistence**: Session-based with thread_id configuration
- **Purpose**: Maintains conversation history across multiple turns

---

## Data Model

### Entity Relationship Diagram (ERD)

#### Core Entities

```
┌─────────────────┐
│     Ticket      │
├─────────────────┤
│ ticket_id (PK)  │──┐
│ user_id (FK)    │  │
│ title           │  │
│ description     │  │
│ category        │  │
│ priority        │  │
│ status          │  │
│ resolution      │  │
│ created_at      │  │
│ assignment_group│  │
└─────────────────┘  │
        │            │
        │  ┌─────────┼──────────────────┐
        │  │         │                  │
        ▼  ▼         ▼                  ▼
┌──────────────┐  ┌────────────┐  ┌────────────┐
│    User      │  │ Category   │  │ Priority   │
├──────────────┤  ├────────────┤  ├────────────┤
│ user_id (PK) │  │ cat_id (PK)│  │ pri_id (PK)│
│ name         │  │ name       │  │ level      │
│ email        │  │ description│  │ value      │
└──────────────┘  └────────────┘  └────────────┘

┌──────────────────┐     ┌──────────────────┐
│ AssignmentGroup  │     │ TicketStatus     │
├──────────────────┤     ├──────────────────┤
│ group_id (PK)    │     │ status_id (PK)   │
│ name             │     │ status_name      │
│ description      │     │ workflow_state   │
│ team_lead        │     └──────────────────┘
└──────────────────┘
```

### Data Schemas

#### Ticket Schema (From ServiceNow Dataset)

```
{
  "ticket_id": "TKT-1001",          # Unique identifier
  "user_id": "USR-5570",            # Requester
  "title": "Password reset for SAP",# Brief description
  "description": "User locked out...",  # Detailed description
  "category": "Access Management",  # Issue type
  "priority": "P4 - Low",           # Urgency level
  "assignment_group": "IAM",        # Responsible team
  "status": "Closed",               # Ticket status
  "resolution": "Restarted service...", # Solution applied
  "created_at": "2026-01-26 18:00:00" # Creation timestamp
}
```

#### Agent State Schema

```
{
  "messages": [
    {
      "type": "user" | "ai" | "assistant",
      "content": "User query or agent response"
    }
  ],
  "is_satisfied": true/false,
  "is_relevant": true/false,
  "category": "Infrastructure|Database|Network|...",
  "priority": "Low|Medium|High|Critical",
  "assignment_group": "DB_ADMIN|NETWORK_TEAM|CLOUD_OPS|SERVICE_DESK",
  "rag_context": "Retrieved solution text",
  "rag_tried": true/false,
  "next_agent": "RAGAgent|TicketAgent|SupervisorAgent"
}
```

#### ChromaDB Collection Schema

```
{
  "id": "ticket_1001",
  "document": "Password reset for SAP - User locked out after 3 failed attempts...",
  "metadata": {
    "resolution": "Restarted service and cleared cache.",
    "priority": "P4 - Low",
    "category": "Access Management",
    "status": "Closed",
    "assignment_group": "IAM"
  },
  "embedding": [0.123, 0.456, ...]  # 384-dim vector (all-MiniLM-L6-v2)
}
```

### Issue Categories

```
- Infrastructure     (EC2, VPC, networking, servers)
- Application        (Code, services, APIs, frontend)
- Security          (Vulnerabilities, auth, compliance)
- Database          (RDS, queries, connections)
- Network           (VPN, routing, DNS)
- Access Management (SSO, passwords, permissions)
```

### Priority Levels

```
P1 - Critical  (System down, total outage)
P2 - High      (Major service impact)
P3 - Medium    (Partial functionality loss)
P4 - Low       (Minor issues, cosmetic)
```

### Ticket Status Values

```
Open        (New, not started)
In Progress (Being worked on)
Resolved    (Fixed, awaiting user confirmation)
Closed      (Complete, in knowledge base)
```

---

## Data Sources & Data Engineering

### Primary Data Source

**File**: `Data/service_now_sample_dataset.csv`

**Source Type**: ServiceNow Export (Simulated ITSM System)

**Records**: 50 closed tickets with complete metadata

**Data Volume**: ~50 KB CSV file

### Data Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│           DATA INGESTION & PREPARATION PHASE                      │
└──────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
    ┌────────────────────┐    ┌──────────────────────┐
    │ ServiceNow Dataset │    │ Ticket Data CSV      │
    │ (50 records)       │    │ - 50 closed tickets  │
    │ - ticket_id        │    │ - Full metadata      │
    │ - title            │    │ - Resolutions        │
    │ - description      │    │ - Categories         │
    │ - resolution       │    │ - Priorities         │
    │ - status           │    │ - Assignment groups  │
    │ - category         │    │ - Timestamps         │
    │ - priority         │    │ - User IDs           │
    │ - assignment_group │    │ - Status info        │
    │ - created_at       │    └──────────────────────┘
    │ - user_id          │
    └────────────────────┘
                │
                ▼
    ┌────────────────────────────────────────┐
    │  DATA TRANSFORMATION (Embed.py)        │
    │  ┌─────────────────────────────────────┤
    │  │ Step 1: Load CSV with Pandas        │
    │  │ Step 2: Create document corpus:     │
    │  │   Combined: title + " " + description
    │  │ Step 3: Extract metadata:           │
    │  │   - resolution                      │
    │  │   - priority                        │
    │  │   - category                        │
    │  │   - status                          │
    │  │ Step 4: Generate vector embeddings │
    │  │   - Model: all-MiniLM-L6-v2        │
    │  │   - Output: 384-dim vectors         │
    │  └─────────────────────────────────────┤
    └────────────────────────────────────────┘
                │
                ▼
    ┌────────────────────────────────────────┐
    │  VECTOR STORE SETUP                    │
    │  ┌─────────────────────────────────────┤
    │  │ Vector DB: ChromaDB Cloud           │
    │  │ - Tenant: e5b49720-5aa8-4df7-b...   │
    │  │ - Database: ticketing               │
    │  │ - Collection: Incidents-collection  │
    │  │ - Distance Metric: Cosine           │
    │  │ - Storage: Cloud (Distributed)      │
    │  └─────────────────────────────────────┤
    └────────────────────────────────────────┘
                │
                ▼
    ┌────────────────────────────────────────┐
    │  KNOWLEDGE BASE POPULATION             │
    │  ┌─────────────────────────────────────┤
    │  │ For each ticket:                    │
    │  │ 1. Create unique ID: ticket_XXXX    │
    │  │ 2. Add document:                    │
    │  │    (title + description)            │
    │  │ 3. Store metadata:                  │
    │  │    {resolution, priority, ...}      │
    │  │ 4. Compute embeddings (auto)        │
    │  │ 5. Index in vector DB               │
    │  │                                     │
    │  │ Total: 50 vectors indexed           │
    │  └─────────────────────────────────────┤
    └────────────────────────────────────────┘
                │
                ▼
    ┌────────────────────────────────────────┐
    │  QUERY RUNTIME (RAGTool)               │
    │  ┌─────────────────────────────────────┤
    │  │ 1. User query entered               │
    │  │ 2. Embedding computed:              │
    │  │    Query → 384-dim vector           │
    │  │ 3. Similarity search:               │
    │  │    - Metric: Cosine distance        │
    │  │ 4. Retrieve top-2 results           │
    │  │ 5. Filter: status == "Closed"       │
    │  │ 6. Calculate confidence:            │
    │  │    score = 1 - distance             │
    │  │ 7. Threshold check:                 │
    │  │    if score >= 0.7: Return result   │
    │  │    else: Signal "not relevant"      │
    │  └─────────────────────────────────────┤
    └────────────────────────────────────────┘
                │
                ▼
    ┌────────────────────────────────────────┐
    │  RESULTS TO AGENT                      │
    │  ┌─────────────────────────────────────┤
    │  │ {                                   │
    │  │   "is_relevant": true/false,        │
    │  │   "rag_context": "Solution text",   │
    │  │   "rag_tried": true                 │
    │  │ }                                   │
    │  └─────────────────────────────────────┤
    └────────────────────────────────────────┘
```

### Data Engineering Steps

#### Step 1: Data Extraction

- Read ServiceNow CSV export
- Extract 50 closed tickets
- Validate data integrity

#### Step 2: Data Transformation

```python
# Corpus Creation
documents = df['title'] + " - " + df['description']

# Metadata Extraction
metadata = df[['resolution', 'priority', 'category', 'status']].to_dict('records')

# ID Generation
ids = [f"ticket_{i}" for i in range(len(documents))]
```

#### Step 3: Vectorization

- Model: Sentence Transformers (all-MiniLM-L6-v2)
- Output: 384-dimensional embeddings
- Applied to: Combined title + description
- Automatic: ChromaDB handles at index time

#### Step 4: Indexing

- Storage: ChromaDB Cloud (distributed)
- Index Type: HNSW (Hierarchical Navigable Small World)
- Distance Metric: Cosine similarity
- Filtering: Enable status-based filtering

#### Step 5: Query Processing

- Real-time embedding of user query
- Vector similarity search
- Confidence scoring (1 - distance)
- Threshold filtering (0.7 minimum)

### Data Quality Metrics

- **Completeness**: 100% (all 50 records have all fields)
- **Accuracy**: High (actual ITSM data)
- **Timeliness**: Static knowledge base (updated periodically)
- **Relevance**: Curated closed tickets only
- **Consistency**: Standardized categories and priorities

---

## Low Level Design (LLD)

### 1. SupervisorAgent Detailed Flow

```
INPUT: AgentState (with user messages)
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ SupervisorAgentNode(state: AgentState)              │
└─────────────────────────────────────────────────────┘
    │
    ├─ Extract from state:
    │  ├ messages: List[BaseMessage]
    │  ├ rag_tried: bool
    │  ├ is_relevant: bool
    │  └ category, priority, assignment_group
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ Check Completion Conditions                         │
│ ├─ if "successfully created" in last_message       │
│ │   → Return Command(goto=END)                     │
│ │                                                  │
│ ├─ if "status of your ticket" in last_message     │
│ │   → Return Command(goto=END)                     │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ Prepare LLM Input                                   │
│ ├─ system_prompt = SupervisorPrompt (classified)   │
│ ├─ messages = [system_message] + state.messages    │
│ └─ model = ChatBedrockConverse                     │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ LLM Inference (Bedrock Nova Lite)                   │
│ ├─ Input: Structured system prompt + history      │
│ ├─ Output Type: RouteDecision (Pydantic)           │
│ ├─ Fields extracted:                              │
│ │  ├ next_agent: RAGAgent|TicketAgent|FINISH     │
│ │  ├ reason: String                               │
│ │  ├ task_description: String                     │
│ │  ├ category: Issue category                     │
│ │  ├ priority: P1-P4                              │
│ │  └ assignment_group: Team assignment            │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ Routing Logic                                       │
│                                                     │
│ if response.next_agent == "FINISH":               │
│   return Command(                                 │
│     goto=END,                                     │
│     update={"messages": [HumanMessage(...)]}     │
│   )                                               │
│                                                   │
│ else:                                             │
│   return Command(                                 │
│     goto=response.next_agent,                    │
│     update={                                      │
│       "messages": [HumanMessage(...instruction)],│
│       "next_agent": response.next_agent,         │
│       "category": response.category,             │
│       "priority": response.priority,             │
│       "assignment_group": response.assignment_.. │
│     }                                             │
│   )                                               │
└─────────────────────────────────────────────────────┘
    │
    ▼
OUTPUT: Command object (goto, update parameters)
```

### 2. RAGAgent Detailed Flow

```
INPUT: AgentState with user messages
    │
    ▼
┌───────────────────────────────────────────────────┐
│ RagAgentNode(state: AgentState)                   │
│ ├─ Extract: query = state["messages"]            │
│ └─ Create agent with RAG_check_node tool         │
└───────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────┐
│ Invoke RAG Agent                                  │
│ ├─ Input: {"messages": query}                    │
│ ├─ Uses: create_react_agent from LangChain       │
│ └─ Binds: RAG_check_node as tool                 │
└───────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────┐
│ RAG_check_node Tool Execution                    │
│ ├─ Step 1: Extract query from messages           │
│ │   query = state["messages"][-1].content        │
│ │                                                │
│ ├─ Step 2: Initialize ChromaDB Client           │
│ │   ├─ api_key: CHROMA_DB_KEY (env var)        │
│ │   ├─ tenant: e5b49720-5aa8-4df7-bd60-0e8ea24eda7
│ │   ├─ database: ticketing                      │
│ │   └─ CloudClient connection                    │
│ │                                                │
│ ├─ Step 3: Get Collection                        │
│ │   ├─ name: Incidents-collection                │
│ │   ├─ embedding_function: SentenceTransformer   │
│ │   ├─ distance_metric: cosine                  │
│ │   └─ auto-creates if not exists                │
│ │                                                │
│ ├─ Step 4: Query Vector DB                       │
│ │   collection.query(                            │
│ │     query_texts=[query],                       │
│ │     n_results=2,      # Top 2 results          │
│ │     where={"status": "Closed"}  # Filter      │
│ │   )                                            │
│ │                                                │
│ ├─ Step 5: Calculate Confidence Score            │
│ │   ├─ distances = results['distances'][0][0]   │
│ │   ├─ confidence = 1 - distance                 │
│ │   └─ THRESHOLD = 0.7                           │
│ │                                                │
│ ├─ Step 6: Relevance Decision                    │
│ │   if confidence >= 0.7:                        │
│ │     └─ Return relevant = True + context        │
│ │   else:                                         │
│ │     └─ Return relevant = False                 │
│ │                                                │
│ └─ Step 7: Error Handling                        │
│     try/except with fallback response            │
└───────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────┐
│ Return Results                                    │
│ {                                                 │
│   "is_relevant": bool,                           │
│   "rag_context": str (solution text),            │
│   "rag_tried": True                              │
│ }                                                 │
└───────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────┐
│ Agent Formats Response                            │
│ ├─ If relevant: Present solution to user         │
│ └─ If not: Signal for ticket creation            │
└───────────────────────────────────────────────────┘
    │
    ▼
OUTPUT: Command(goto=SupervisorAgent, update={...})
```

### 3. TicketAgent Detailed Flow

```
INPUT: AgentState with user context
    │
    ▼
┌──────────────────────────────────────────────────┐
│ TicketAgentNode(state: AgentState)               │
│ ├─ Extract query from messages                  │
│ ├─ Create agent with tools:                      │
│ │  ├─ create_ticket                              │
│ │  └─ lookup_ticket                              │
│ └─ Invoke with current state                     │
└──────────────────────────────────────────────────┘
    │
    ├────────────────────────────────┬───────────────────┐
    │                                │                   │
    ▼                                ▼                   ▼
┌─────────────────────┐   ┌──────────────────┐  ┌──────────────────┐
│ Ticket Lookup Path  │   │ Ticket Creation  │  │ Tool Invocation  │
├─────────────────────┤   │ Path             │  │ Selection        │
│ if ticket_id found: │   ├──────────────────┤  └──────────────────┘
│                     │   │ Extract fields:  │
│ lookup_ticket(      │   │ ├─ title         │
│   ticket_id=ID      │   │ ├─ description   │
│ )                   │   │ ├─ priority      │
│                     │   │ ├─ category      │
│ ──────────────────→ │   │ └─ assignment_.. │
│ invoke Lambda:      │   │                  │
│ Lookup_ticket       │   │ create_ticket(   │
│ (RequestResponse)   │   │   title,         │
│                     │   │   description,   │
│ receive JSON        │   │   priority,      │
│ response            │   │   category,      │
│                     │   │   assignment_.. │
│                     │   │ )                │
│                     │   │                  │
│                     │   │ ──────────────→  │
│                     │   │ invoke Lambda:   │
│                     │   │ Create_ticket    │
│                     │   │ (RequestResponse)│
│                     │   │                  │
│                     │   │ receive:         │
│                     │   │ {ticket_id}      │
│                     │   │                  │
└─────────────────────┘   └──────────────────┘
    │                                │
    └────────────────┬───────────────┘
                     │
                     ▼
        ┌──────────────────────────────┐
        │ Return Result                │
        │ ├─ Lookup: Full ticket info  │
        │ └─ Create: Ticket created msg
        └──────────────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────┐
        │ Agent Formats Response       │
        │ ├─ Parse result from Lambda  │
        │ └─ Add to conversation       │
        └──────────────────────────────┘
                     │
                     ▼
OUTPUT: Command(goto=SupervisorAgent, update={messages})
```

### 4. LangGraph State Machine Flow

```
┌─────────────────────────────────┐
│      Entry Point: START          │
└──────────────┬──────────────────┘
               │
               ▼
        ┌─────────────────┐
        │ SupervisorAgent │  (Router Node)
        └────────┬────────┘
                 │
         ┌───────┼───────┬──────────┐
         │       │       │          │
         ▼       ▼       ▼          ▼
    RAGAgent TktAgent  FINISH     LOOP
         │       │       │          │
         │       │       │    ┌─────┘
         │       │       │    │
         ├───────┴───────┤    │
         │               │    │
         └─────────┬─────┘    │
                   │          │
         ┌─────────▼──────┐   │
         │ SupervisorAgent│   │
         │  (Re-routing)  │   │
         └────┬───────┬───┘   │
              │       │       │
              ▼       ▼       │
           Next     END◄──────┘
          Agent

Configuration:
- Memory: MemorySaver (in-memory)
- Thread ID: session_v1 (per conversation)
- Checkpointing: Enabled
- Streaming: Event-based
```

### 5. Function Signatures & Data Contracts

#### SupervisorAgentNode

```python
def SupervisorAgentNode(state: AgentState) -> Command[Literal["RAGAgent", "TicketAgent", "__end__"]]:
    """
    Main router for multi-agent system

    Args:
        state: AgentState with messages, context, and tracking flags

    Returns:
        Command object specifying:
        - goto: Next node name (string)
        - update: Dictionary of state updates

    State Updates:
    {
        "messages": [HumanMessage(...)],  # New instruction
        "next_agent": str,                # Agent selected
        "category": str,                  # Issue category
        "priority": str,                  # Priority level
        "assignment_group": str           # Team assignment
    }
    """
```

#### RagAgentNode

```python
def RagAgentNode(state: AgentState) -> Command[Literal["SupervisorAgent"]]:
    """
    Executes RAG search and returns to supervisor

    Args:
        state: AgentState with user query in messages

    Returns:
        Command object with:
        - goto: "SupervisorAgent"
        - update: {"messages": results_from_rag_agent}
    """
```

#### TicketAgentNode

```python
def TicketAgentNode(state: AgentState) -> Command[Literal["SupervisorAgent"]]:
    """
    Creates or looks up tickets

    Args:
        state: AgentState with ticket request in messages

    Returns:
        Command object with:
        - goto: "SupervisorAgent"
        - update: {"messages": ticket_operation_result}
    """
```

#### RAG_check_node Tool

```python
@tool
def RAG_check_node(query: str) -> dict:
    """
    Vector search on incident knowledge base

    Args:
        query: User question string

    Returns:
    {
        "is_relevant": bool,           # >= 0.7 confidence
        "rag_context": str,            # Solution text
        "rag_tried": bool              # Always True
    }
    """
```

#### create_ticket Tool

```python
@tool
def create_ticket(
    title: str,
    description: str,
    priority: str,
    category: str,
    assignement_group: str
) -> str:
    """
    Creates ticket in ServiceNow via Lambda

    Returns:
        "Ticket created successfully with ID: {ticket_id}"
    """
```

#### lookup_ticket Tool

```python
@tool
def lookup_ticket(ticket_id: str) -> str:
    """
    Retrieves ticket details from ServiceNow via Lambda

    Returns:
        JSON string with full ticket information
    """
```

---

## Data Flow Diagram (DFD)

### Level 0: System Context Diagram

```
                    ┌─────────────────────────┐
                    │      END USER           │
                    │   (Chat Interface)      │
                    └────────────┬────────────┘
                                 │
                   ┌─────────────┼─────────────┐
                   │ (1) Query   │ (2) Response│
                   │             │             │
                   ▼             ▼             │
            ┌─────────────────────────────┐   │
            │  L1 IT SUPPORT AGENT SYSTEM │   │
            │   (Multi-Agent Orchestrator)│   │
            └─────┬──────────────────┬────┘   │
                  │                  │        │
        ┌─────────┼──────┬──────────┬┘        │
        │         │      │          │         │
   (3)  │    (4)  │ (5)  │    (6)   │         │
   Data │ Query   │ Get  │ Get Ticket
   Flow │         │Results Lookup/Create
        │         │      │          │         │
        ▼         ▼      ▼          ▼         │
    ┌────────┐ ┌────────────┐  ┌──────────┐ │
    │ChromaDB│ │ Knowledge  │  │ ServiceNow
    │ Cloud  │ │  Base      │  │ Ticketing
    │ (KB)   │ │ (Vectors)  │  │ System    │
    └────────┘ └────────────┘  └──────────┘ │
                                             │
                └─────────────────────────────┘
```

### Level 1: Functional Data Flow

```
USER INPUT LAYER
    │
    ├─ Query: "RDS not accessible, database is down"
    │
    ▼
┌──────────────────────────────────────┐
│ ORCHESTRATION LAYER                  │
│ (LangGraph State Machine)            │
│                                      │
│ ┌────────────────────────────────┐  │
│ │ SupervisorAgent (Routing)       │  │
│ │ - Parse query                   │  │
│ │ - Determine issue category      │  │
│ │ - Assign priority               │  │
│ │ - Route to agent                │  │
│ └────────────┬─────────────────────┤  │
│              │ Routing Decision    │  │
│              ▼                     │  │
│ ┌────────────────────────────────┐  │
│ │ Decision: Send to RAGAgent      │  │
│ └────────────┬─────────────────────┤  │
│              │                     │  │
│              │ State Update:       │  │
│              │ - category: Database
│              │ - priority: High    │  │
│              │ - next_agent: RAGAgent
│              ▼                     │  │
│ ┌────────────────────────────────┐  │
│ │ RAGAgent (Knowledge Retrieval)  │  │
│ │ - Call RAG_check_node tool      │  │
│ └───────────┬────────────────────┘  │
└────────────┼──────────────────────────┘
             │
    ┌────────┴────────────────┐
    │                         │
    ▼                         ▼
┌──────────────────┐  ┌────────────────┐
│ VECTOR DB LAYER  │  │ INFERENCE      │
│  (ChromaDB)      │  │ (Nova Lite)    │
│                  │  │                │
│ 1. Embed query   │  │ Reasoning      │
│ 2. Similarity    │  │ on context     │
│    search        │  │                │
│ 3. Retrieve top  │  │ Structured     │
│    2 results     │  │ output         │
│ 4. Filter:       │  │ (RouteDecision)│
│    status=Closed │  │                │
│ 5. Calculate     │  └────────────────┘
│    confidence    │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────┐
│ RESULTS FLOW                      │
│ ┌──────────────────────────────┐ │
│ │ Result 1: High Confidence    │ │
│ │ ├─ Issue: RDS backup failed  │ │
│ │ ├─ Solution: Increase storage│ │
│ │ ├─ Confidence: 0.82          │ │
│ │ ├─ Status: Closed (KB item)  │ │
│ │ └─ Relevant: TRUE            │ │
│ └──────────────────────────────┘ │
│ ┌──────────────────────────────┐ │
│ │ Result 2: Medium Confidence  │ │
│ │ ├─ Issue: Database down      │ │
│ │ ├─ Solution: Restart service │ │
│ │ ├─ Confidence: 0.76          │ │
│ │ └─ Relevant: TRUE            │ │
│ └──────────────────────────────┘ │
└────────┬─────────────────────────┘
         │
         ▼ (is_relevant = TRUE)
┌──────────────────────────────────┐
│ STATE UPDATE                      │
│ ├─ rag_context: Solution text    │
│ ├─ is_relevant: true             │
│ ├─ rag_tried: true               │
│ └─ messages: [agent_response]    │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ SUPERVISOR RE-ROUTING            │
│ (Check if satisfied)             │
│                                  │
│ Decision: User satisfied?        │
│ → If YES: Route to END           │
│ → If NO: Route to TicketAgent    │
└────────┬─────────────────────────┘
         │
         ▼
OUTPUT LAYER
    │
    ├─ Response to user with solution
    └─ Mark issue as resolved
```

### Level 2: Data Elements & Transformations

```
TRANSFORMATION 1: Query to Vector
─────────────────────────────────
Input:  "RDS not accessible, database is down"
         ↓
Process: Embedding with all-MiniLM-L6-v2
         ↓
Output:  [0.123, 0.456, ..., 0.789]  (384 dimensions)


TRANSFORMATION 2: Vector to Results
───────────────────────────────────
Input:  384-dim query vector
        + 50 closed ticket vectors
        ↓
Process: Cosine similarity calculation
         distance = 1 - cos_similarity
         confidence = 1 - distance
         ↓
Output:  [
           {
             distance: 0.18,
             confidence: 0.82,
             doc: "Password reset...",
             metadata: {...}
           },
           {
             distance: 0.24,
             confidence: 0.76,
             doc: "Database connection pool...",
             metadata: {...}
           }
         ]


TRANSFORMATION 3: Results to Structured Output
──────────────────────────────────────────────
Input:  Raw search results + confidence scores
        ↓
Process: LLM structuring with Pydantic
         Confidence check (>= 0.7)
         Context extraction
         ↓
Output:  {
           "is_relevant": true,
           "rag_context": "Based on similar closed issue...",
           "rag_tried": true
         }


TRANSFORMATION 4: RAG Result to Routing Decision
────────────────────────────────────────────────
Input:  RAG results + conversation history
        ↓
Process: Supervisor LLM evaluation
         - User satisfied?
         - Solution complete?
         - Needs ticket?
         ↓
Output:  RouteDecision {
           "next_agent": "TicketAgent" | "SupervisorAgent",
           "reason": "User needs ticket for escalation",
           "task_description": "Create ticket for...",
           "category": "Database",
           "priority": "High",
           "assignment_group": "DBA_GLOBAL"
         }
```

---

## Sequence Diagrams

### Sequence 1: Happy Path (RAG Finds Solution)

```
User    Supervisor    RAGAgent    ChromaDB    Nova LLM    User(Response)
│           │             │           │           │              │
│ Query     │             │           │           │              │
├──────────>│             │           │           │              │
│           │             │           │           │              │
│           │ Analyze     │           │           │              │
│           │ classify    │           │           │              │
│           ├─ Determine category    │           │              │
│           ├─ Assign priority       │           │              │
│           │             │           │           │              │
│           │ Route       │           │           │              │
│           │ decision    │           │           │              │
│           ├──────────────────────>│           │              │
│           │             │           │           │              │
│           │             │ Invoke    │           │              │
│           │             │ RAG tool  │           │              │
│           │             │           │           │              │
│           │             │ Embed     │           │              │
│           │             │ query     │           │              │
│           │             ├──────────>│           │              │
│           │             │           │           │              │
│           │             │           │ Vector    │              │
│           │             │           │ search    │              │
│           │             │           │           │              │
│           │             │           │ Similarity│              │
│           │             │           │ calc      │              │
│           │             │           │           │              │
│           │             │<──────────┤ Results   │              │
│           │             │           │ (top-2)   │              │
│           │             │           │           │              │
│           │             │ Confidence│           │              │
│           │             │ check     │           │              │
│           │             │ >= 0.7    │           │              │
│           │             │           │           │              │
│           │             │<──────────┤ Return    │              │
│           │             │ {         │ high conf │              │
│           │             │  relevant │ context   │              │
│           │             │  context  │           │              │
│           │             │ }         │           │              │
│           │             │           │           │              │
│           │<────────────┤ Response  │           │              │
│           │             │ from RAG  │           │              │
│           │             │           │           │              │
│           │ Check if    │           │           │              │
│           │ satisfied   │           │           │              │
│           ├──────────────────────────────────>│              │
│           │             │           │           │ Evaluate    │
│           │             │           │           │ satisfaction│
│           │             │           │           │             │
│           │<───────────────────────────────────┤ RouteDecision
│           │             │           │           │             │
│           │ Decision:   │           │           │             │
│           │ Satisfied   │           │           │             │
│           │ → FINISH    │           │           │             │
│           │             │           │           │             │
│<──────────┤             │           │           │             │
│ Solution  │             │           │           │             │
│ returned  │             │           │           │             │
│           │             │           │           │             │

TIME: ~2-3 seconds
PATH SUCCESS RATE: ~70% (when KB has relevant solution)
```

### Sequence 2: Fallback Path (RAG Fails, Create Ticket)

```
User    Supervisor    RAGAgent    ChromaDB    TicketAgent    Lambda    ITSM
│           │             │           │           │             │        │
│ Query     │             │           │           │             │        │
├──────────>│             │           │           │             │        │
│           │ Classify    │           │           │             │        │
│           │ + Route     │           │           │             │        │
│           ├──────────────────────>│           │             │        │
│           │             │           │           │             │        │
│           │             │ Search    │           │             │        │
│           │             │ for       │           │             │        │
│           │             │ similar   │           │             │        │
│           │             │           │           │             │        │
│           │             │<──────────┤ Results  │             │        │
│           │             │ (low conf)│          │             │        │
│           │             │           │          │             │        │
│           │             │ < 0.7     │          │             │        │
│           │             │ threshold │          │             │        │
│           │             │           │          │             │        │
│           │<────────────┤ is_       │          │             │        │
│           │             │ relevant: │          │             │        │
│           │             │ FALSE     │          │             │        │
│           │             │           │          │             │        │
│           │ RAG Failed  │           │          │             │        │
│           │ Re-route to │           │          │             │        │
│           │ Ticketing   │           │          │             │        │
│           ├────────────────────────────────────>│             │        │
│           │             │           │          │             │        │
│           │             │           │          │ Extract     │        │
│           │             │           │          │ context +   │        │
│           │             │           │          │ generate    │        │
│           │             │           │          │ title/desc  │        │
│           │             │           │          │             │        │
│           │             │           │          │ Call tool:  │        │
│           │             │           │          │ create_ticket        │
│           │             │           │          ├────────────>│        │
│           │             │           │          │             │        │
│           │             │           │          │             │ Lambda │
│           │             │           │          │             │ invoked
│           │             │           │          │             │ Create_
│           │             │           │          │             │ ticket
│           │             │           │          │             │        │
│           │             │           │          │             │        │ Insert
│           │             │           │          │             │        │ new
│           │             │           │          │             │        │ ticket
│           │             │           │          │             │        │ in DB
│           │             │           │          │             │        │
│           │             │           │          │             │<───────┤
│           │             │           │          │             │ TKT-XXX
│           │             │           │          │<────────────┤        │
│           │             │           │          │ ticket_id   │        │
│           │             │           │          │             │        │
│           │             │           │          │ Response:   │        │
│           │             │           │          │ "Ticket     │        │
│           │             │           │          │  created... │        │
│           │<────────────────────────────────────┤ TKT-XXXXX"  │        │
│           │             │           │          │             │        │
│           │ Check       │           │          │             │        │
│           │ completion  │           │          │             │        │
│           │ "ticket     │           │          │             │        │
│           │ created"    │           │          │             │        │
│           │ → FINISH    │           │          │             │        │
│           │             │           │          │             │        │
│<──────────┤             │           │          │             │        │
│ Ticket ID │             │           │          │             │        │
│ response  │             │           │          │             │        │
│           │             │           │          │             │        │

TIME: ~3-5 seconds
SUCCESS: 100% (Lambda always creates ticket)
NEW TICKET ID: TKT-XXXXX (added to ITSM)
```

### Sequence 3: Ticket Lookup Path

```
User        Supervisor        TicketAgent        Lambda        ITSM DB
│               │                  │                │             │
│ "Check        │                  │                │             │
│ TKT-1234"     │                  │                │             │
├──────────────>│                  │                │             │
│               │                  │                │             │
│               │ Recognize        │                │             │
│               │ Ticket ID        │                │             │
│               │ pattern          │                │             │
│               │ → Route to       │                │             │
│               │ Ticketing        │                │             │
│               ├─────────────────>│                │             │
│               │                  │                │             │
│               │                  │ LLM decides   │             │
│               │                  │ lookup tool   │             │
│               │                  │ needed        │             │
│               │                  │                │             │
│               │                  │ Call:         │             │
│               │                  │ lookup_ticket │             │
│               │                  │ (TKT-1234)    │             │
│               │                  ├───────────────>│             │
│               │                  │                │             │
│               │                  │                │ Query DB    │
│               │                  │                │ for ticket  │
│               │                  │                │             │
│               │                  │                │<────────────┤
│               │                  │                │ Ticket data:
│               │                  │                │ ├─ Status
│               │                  │                │ ├─ Category
│               │                  │                │ ├─ Priority
│               │                  │                │ ├─ Current
│               │                  │                │ │ resolution
│               │                  │                │ └─ Last update
│               │                  │<───────────────┤             │
│               │                  │ Full ticket   │             │
│               │                  │ details       │             │
│               │                  │ (JSON)        │             │
│               │                  │                │             │
│               │                  │ Format as     │             │
│               │                  │ response      │             │
│               │<─────────────────┤                │             │
│               │ Ticket Status:   │                │             │
│               │ {status, priority│                │             │
│               │  category, ...}  │                │             │
│               │                  │                │             │
│<──────────────┤                  │                │             │
│ Display       │                  │                │             │
│ ticket info   │                  │                │             │
│ to user       │                  │                │             │
│               │                  │                │             │

TIME: ~1-2 seconds
TICKET FOUND: 100% (if ID valid in ITSM)
```

---

## State Transition Diagram

### State Machine Transitions

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT STATE MACHINE                          │
└─────────────────────────────────────────────────────────────────┘

STATES:
─────

[S0] INITIAL
   └─ Empty messages
   └─ rag_tried: false
   └─ is_satisfied: false

[S1] QUERY_RECEIVED
   └─ User message added to messages
   └─ ready for classification

[S2] CLASSIFIED
   └─ category assigned
   └─ priority assigned
   └─ assignment_group assigned

[S3] RAG_SEARCHING
   └─ rag_tried: true (set to in-progress)
   └─ Awaiting knowledge base results

[S4] RAG_SUCCESS
   └─ is_relevant: true
   └─ rag_context: populated with solution
   └─ rag_tried: true

[S5] RAG_FAILED
   └─ is_relevant: false
   └─ rag_context: empty
   └─ rag_tried: true

[S6] TICKET_CREATING
   └─ Invoking ticket creation
   └─ next_agent: TicketAgent

[S7] TICKET_CREATED
   └─ ticket_id assigned
   └─ Response contains "successfully created"

[S8] TICKET_LOOKUP
   └─ Looking up existing ticket
   └─ next_agent: TicketAgent

[S9] TICKET_FOUND
   └─ Ticket details retrieved
   └─ Response contains ticket information

[S10] USER_SATISFIED
   └─ is_satisfied: true
   └─ Resolution complete

[S11] TERMINAL (END)
   └─ Conversation ended
   └─ No further transitions


TRANSITIONS:
───────────

S0 ─── user_inputs_query ──────────> S1
       action: add message to state

S1 ─── supervisor_classifies ───────> S2
       action: extract category, priority, group

S2 ─── send_to_rag_agent ──────────> S3
       action: set rag_tried=true

S3 ─── rag_search_matches ─────────> S4
       action: set is_relevant=true, populate context

S3 ─── rag_search_no_match ────────> S5
       action: set is_relevant=false

S4 ─── user_satisfied ─────────────> S10
       action: supervisor detects completion

S4 ─── user_needs_escalation ──────> S6
       action: set next_agent=TicketAgent

S5 ─── create_ticket_automatically ─> S6
       action: supervisor routes to Ticketing

S6 ─── ticket_created_successfully ─> S7
       action: Lambda returns ticket_id

S7 ─── operation_complete ────────> S11
       condition: "successfully created" in response

S2 ─── user_asks_for_lookup ───────> S8
       action: set next_agent=TicketAgent

S8 ─── ticket_lookup_succeeds ─────> S9
       action: populate ticket_details

S9 ─── information_provided ───────> S11
       condition: user has ticket info

S10 ─── end_conversation ──────────> S11
       action: send END command


DEFAULT TRANSITIONS:
───────────────────

Loop back to S2 (Supervisor) from:
 - S4 (after presenting solution)
 - S7 (after creating ticket)
 - S9 (after showing ticket info)

Condition: if not completion signal


STATE TRANSITION TABLE:
──────────────────────

From State │ Trigger Event              │ To State  │ Action
───────────┼────────────────────────────┼───────────┼──────────────────
S0         │ User sends message         │ S1        │ Update messages
S1         │ Supervisor analysis        │ S2        │ Set category, priority
S2         │ First-time technical issue │ S3        │ Route RAGAgent
S2         │ Ticket ID detected         │ S8        │ Route Lookup
S3         │ Confidence >= 0.7          │ S4        │ Set is_relevant=true
S3         │ Confidence < 0.7           │ S5        │ Set is_relevant=false
S4         │ User says "yes, solved"    │ S10       │ Flag satisfied
S4         │ User needs more help       │ S2        │ Re-route (loop)
S5         │ RAG already tried + failed │ S6        │ Force ticket creation
S6         │ Lambda returns ticket_id   │ S7        │ Update messages
S7         │ "successfully created"     │ S11       │ Send END
S8         │ Ticket details retrieved   │ S9        │ Populate info
S9         │ User has info              │ S11       │ Send END
S10        │ Supervisor confirms end    │ S11       │ Send END
───────────┴────────────────────────────┴───────────┴──────────────────


GUARD CONDITIONS:
────────────────

Transition allowed if:
├─ S3→S4: confidence_score >= 0.7
├─ S5→S6: rag_tried == true AND is_relevant == false
├─ S6→S7: lambda_response.ticket_id exists
├─ S7→S11: "successfully created" IN response.content
├─ S4→S10: is_satisfied == true
├─ S2→S8: ticket_id_pattern MATCHES IN user_query
└─ S9→S11: ticket_details_present == true


TIMEOUT HANDLING:
────────────────

If transition takes > 30 seconds:
 └─ Lambda timeout → Fallback to generic error message
 └─ ChromaDB timeout → Route to TicketAgent


ERROR RECOVERY:
───────────────

Exception during state:
 S3 (RAG search) → S5 (treat as failed)
 S6 (Ticket creation) → Error message → S2 (re-route)
 S8 (Ticket lookup) → Error message → S2 (re-route)
```

### State Transition Flowchart

```
                    ┌─────────────┐
                    │   START     │
                    │  (S0:Empty) │
                    └──────┬──────┘
                           │
                           │ User enters query
                           ▼
                    ┌─────────────┐
                    │   S1:Query  │
                    │  Received   │
                    └──────┬──────┘
                           │
                           │ Supervisor analyzes
                           ▼
                    ┌─────────────┐
                    │   S2:       │
                    │ Classified  │
                    └──────┬──────┘
                    ┌──────┴──────────────────┐
                    │                         │
           Issue?   │ Ticket ID found?       │
                    │                         │
                    ▼                         ▼
            ┌──────────────┐        ┌──────────────┐
            │ S3: RAG      │        │ S8: Ticket   │
            │ Searching    │        │ Lookup       │
            └──────┬───────┘        └──────┬───────┘
                   │                       │
        ┌──────────┴──────────┐            │ Results found
        │                     │            │
    Conf>=0.7            Conf<0.7         ▼
        │                     │      ┌──────────────┐
        ▼                     ▼      │ S9: Ticket   │
   ┌─────────────┐   ┌─────────────┐│ Found        │
   │ S4: RAG     │   │ S5: RAG     ││              │
   │ Success     │   │ Failed      │└────────┬─────┘
   └──────┬──────┘   └──────┬──────┘         │
          │                 │                │ Show to user
          │                 │                │
   ┌──────┴────────┐    ┌───┴──────────┐    │
   │               │    │              │    ▼
   │ Satisfied?    │    │ Create       │  USER HAS INFO
   │ (from context)│    │ Ticket       │  │
   │               │    │              │  │
   YES             NO   │              │  │
   │                    └──────┬───────┘  │
   │                           │           │
   │                    ┌──────▼────────┐  │
   │                    │ S6: Ticket    │  │
   │                    │ Creating      │  │
   │                    └──────┬────────┘  │
   │                           │           │
   │                    Lambda returns     │
   │                    │                  │
   │                    ▼                  │
   │              ┌─────────────┐          │
   │              │ S7: Ticket  │          │
   │              │ Created     │          │
   │              └──────┬──────┘          │
   │                     │                 │
   │                "successfully│         │
   │                 created"    │         │
   │                     │        │        │
   │                     ▼        ▼        │
   └────────────>┌─────────────────────┐  │
                │   S10: User         │  │
                │   Satisfied         │  │
                └──────┬──────────────┘  │
                       │                 │
                       │<────────────────┘
                       │
                       │ All paths converge
                       ▼
                ┌─────────────────┐
                │   S11: END      │
                │   (Terminal)    │
                └─────────────────┘
```

---

## Summary Tables

### Component Interaction Matrix

```
┌──────────────────┬────────────────────────────────────────────────┐
│ Component        │ Interactions                                   │
├──────────────────┼────────────────────────────────────────────────┤
│ SupervisorAgent  │ - Reads: AgentState (messages, flags)         │
│                  │ - Calls: Bedrock LLM for routing              │
│                  │ - Outputs: Command to RAGAgent/TicketAgent/END│
│                  │ - Receives: Results from sub-agents           │
├──────────────────┼────────────────────────────────────────────────┤
│ RAGAgent         │ - Receives: Query from messages               │
│                  │ - Calls: RAG_check_node tool                  │
│                  │ - Calls: ChromaDB cloud client                │
│                  │ - Returns: Solution context to Supervisor     │
├──────────────────┼────────────────────────────────────────────────┤
│ TicketAgent      │ - Receives: User context from messages        │
│                  │ - Calls: create_ticket or lookup_ticket tools │
│                  │ - Calls: AWS Lambda functions                 │
│                  │ - Returns: Ticket results to Supervisor       │
├──────────────────┼────────────────────────────────────────────────┤
│ RAG_check_node   │ - Input: Query string                         │
│                  │ - Calls: ChromaDB for vector search           │
│                  │ - Filters: Status = "Closed"                  │
│                  │ - Outputs: is_relevant, rag_context           │
├──────────────────┼────────────────────────────────────────────────┤
│ create_ticket    │ - Input: title, description, priority, etc.   │
│                  │ - Calls: Lambda function                      │
│                  │ - Calls: ServiceNow mock backend              │
│                  │ - Outputs: Ticket ID                          │
├──────────────────┼────────────────────────────────────────────────┤
│ lookup_ticket    │ - Input: ticket_id                            │
│                  │ - Calls: Lambda function                      │
│                  │ - Queries: ITSM database                      │
│                  │ - Outputs: Full ticket details                │
├──────────────────┼────────────────────────────────────────────────┤
│ ChromaDB         │ - Stores: 50 incident vectors + metadata      │
│                  │ - Receives: Query vectors from RAGTool        │
│                  │ - Computes: Cosine similarity                 │
│                  │ - Returns: Top-2 results                      │
├──────────────────┼────────────────────────────────────────────────┤
│ Bedrock LLM      │ - Receives: System prompt + conversation      │
│                  │ - Outputs: Structured RouteDecision           │
│                  │ - Model: Nova Lite v1                         │
│                  │ - Temp: 0 (deterministic)                     │
├──────────────────┼────────────────────────────────────────────────┤
│ AWS Lambda       │ - Receives: Ticket operation request (JSON)   │
│                  │ - Executes: ServiceNow API calls              │
│                  │ - Returns: Ticket ID or details               │
├──────────────────┼────────────────────────────────────────────────┤
│ LangGraph Engine │ - Manages: Node execution order               │
│                  │ - Maintains: AgentState throughout flow       │
│                  │ - Checkpoints: State with MemorySaver         │
│                  │ - Routes: Based on Command objects            │
└──────────────────┴────────────────────────────────────────────────┘
```

### Data Volume & Performance

```
Metric                  │ Value           │ Notes
────────────────────────┼─────────────────┼─────────────────────
Knowledge Base Size     │ 50 tickets      │ From CSV dataset
Vector Dimension        │ 384-dim         │ all-MiniLM-L6-v2
Total Vectors Stored    │ 50              │ In ChromaDB
Query Latency (RAG)     │ 500-800ms       │ Embedding + Search
LLM Latency (Bedrock)   │ 1-2 seconds     │ Token generation
Lambda Exec Time        │ 200-500ms       │ API calls to ServiceNow
Average Response Time   │ 2-4 seconds     │ End-to-end per turn
Memory per Session      │ ~10-50MB        │ Conversation history
Max Concurrent Sessions │ Unlimited       │ Depends on infra
────────────────────────┴─────────────────┴─────────────────────
```

---

## Appendix: Technical Specifications

### Environment Variables Required

```
AWS_ACCESS_KEY_ID          # AWS credentials
AWS_SECRET_ACCESS_KEY      # AWS credentials
CHROMA_DB                  # ChromaDB API key
```

### Dependencies

```
boto3>=1.42.87            # AWS SDK
chromadb>=1.5.5           # Vector DB client
langchain>=1.2.15         # LLM framework
langchain-aws>=1.4.3      # AWS integration
langchain-core>=1.2.26    # Core components
langgraph>=1.1.6          # Orchestration engine
numpy>=2.4.4              # Numerical computing
pandas>=3.0.2             # Data processing
pydantic>=2.12.5          # Data validation
python-dotenv>=1.2.2      # Environment config
sentence-transformers>=5.3.0  # Embedding model
```

### API Endpoints

```
AWS Bedrock:            us-east-1 region
ChromaDB Cloud:         e5b49720-5aa8-4df7-bd60-0e8ea24aeda7
Lambda Functions:
  - Create_ticket:      arn:aws:lambda:us-east-1:022880635234:function:Create_ticket
  - Lookup_ticket:      arn:aws:lambda:us-east-1:022880635234:function:Lookup_ticket
```

---

**Document Version**: 1.0
**Last Updated**: May 2026
**Project Status**: Development Phase
