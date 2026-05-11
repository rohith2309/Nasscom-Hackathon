# Nasscom Hackathon - AI-Powered IT Support Agent System
## Technical Documentation

---

## 1. Detailed Proposed Solution Architecture

### 1.1 Overview
The AI-Powered IT Support Agent System is an intelligent L1 IT Support Assistant designed to streamline incident management and ticket creation. The system leverages Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), and multi-agent orchestration to provide automated first-level support and ticket management.

### 1.2 Solution Objectives
- **Automated Issue Resolution**: Provide immediate solutions from knowledge base using semantic search
- **Intelligent Classification**: Automatically categorize and prioritize incidents
- **Ticket Management**: Create and manage support tickets with appropriate routing
- **Multi-Agent Orchestration**: Coordinate specialized agents for different support functions
- **User Satisfaction Tracking**: Measure resolution effectiveness and feedback

### 1.3 Key Architecture Components

#### A. **User Interface Layer**
- Chat-based interface for user interactions
- Message processing and state management
- Multi-turn conversation support

#### B. **LLM & Intelligence Layer**
- **Primary LLM**: AWS Bedrock (Amazon Nova Lite v1:0)
- **Embedding Model**: Sentence Transformers (all-MiniLM-L6-v2)
- **Structured Outputs**: Pydantic models for deterministic responses
- **Tool Integration**: LangChain tools for external system interaction

#### C. **Orchestration Layer**
- **Workflow Engine**: LangGraph StateGraph
- **State Management**: AgentState for maintaining conversation context
- **Conditional Routing**: Dynamic agent selection based on state
- **Checkpoint System**: Memory saver for persistence

#### D. **Knowledge Base & Retrieval Layer**
- **Vector Database**: ChromaDB Cloud
- **Embedding Strategy**: Sentence-level semantic embeddings
- **Similarity Metrics**: Cosine distance for relevance scoring
- **Confidence Threshold**: 0.7 (70%) for solution recommendations
- **Historical Data**: Closed incidents with resolutions

#### E. **Backend Integration Layer**
- **Ticket System**: AWS Lambda functions for CRUD operations
- **Data Source**: Relational ticket database
- **API Gateway**: RESTful interfaces via Lambda
- **Authentication**: AWS IAM credentials

#### F. **Data Layer**
- **Synthetic Ticket Dataset**: CSV-based ticket history
- **Vector Store**: ChromaDB collections
- **Metadata Storage**: Ticket metadata (resolution, priority, category, status)

### 1.4 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                          │
│                   (Chat Interface)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                    Messages
                         │
         ┌───────────────▼────────────────┐
         │   LangGraph StateGraph         │
         │   (Workflow Orchestration)     │
         └───────────────┬────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐    ┌──────────┐    ┌─────────────┐
   │ RAG     │    │ Classification│ Feedback    │
   │ Check   │    │ Node         │ Node        │
   │ Node    │    │              │             │
   └────┬────┘    └──────┬───────┘    └────┬────┘
        │                │                 │
        └────────────────┼─────────────────┘
                         │
            ┌────────────▼──────────────┐
            │ Ticketing Agent Node      │
            │ (Decision & Tool Binding) │
            └────────────────┬──────────┘
                             │
            ┌────────────────▼──────────────┐
            │ Tools Node                    │
            │ ├─ create_ticket()           │
            │ └─ lookup_ticket()           │
            └────────────────┬──────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
  ┌───────────┐        ┌───────────┐      ┌────────────┐
  │ ChromaDB  │        │ AWS Lambda│      │ Knowledge  │
  │ Cloud     │        │ Ticketing │      │ Base Index │
  │ (Vector)  │        │ System    │      │            │
  └───────────┘        └───────────┘      └────────────┘
```

---

## 2. Low Level Design (LLD)

### 2.1 Component Specifications

#### 2.1.1 RAG Check Node
**Purpose**: Retrieve relevant solutions from knowledge base using semantic similarity

**Input**: 
- User message (from latest message in conversation)
- Agent state

**Processing Flow**:
```
1. Extract query from user message
2. Initialize ChromaDB CloudClient
3. Query Incidents-collection using embedding function
4. Calculate confidence score = 1 - cosine_distance
5. Apply threshold (0.7) for relevance determination
6. Extract metadata (resolution, priority, category)
7. Format context information
```

**Output**:
```json
{
  "is_relevant": Boolean,
  "rag_context": String (formatted resolution + documents)
}
```

**Error Handling**: Returns `is_relevant: False` on exception

---

#### 2.1.2 Classification Node
**Purpose**: Categorize incident and determine priority and assignment group

**Input**:
- Last user message
- Agent state

**Processing Flow**:
```
1. Extract last user message
2. Build classification prompt
3. Invoke structured LLM with ClassificationResult schema
4. Parse category and priority
5. Map category to assignment group using CATEGORY_TO_GROUP dict
```

**Category Mapping**:
| Category | Assignment Group |
|----------|-----------------|
| Infrastructure | INFRA_TEAM_L2 |
| Application | APP_DEV_SUPPORT |
| Security | SOC_SECURITY_TEAM |
| Database | DB_ADMIN_GROUP |
| Network | NETWORK_OPERATIONS |
| Access Management | IAM_IDENTITY_TEAM |

**Output**:
```json
{
  "category": Literal["Infrastructure", "Application", "Security", "Database", "Network", "Access Management"],
  "priority": Literal["Low", "Medium", "High", "Critical"],
  "assignment_group": String
}
```

---

#### 2.1.3 Feedback Node
**Purpose**: Determine user satisfaction with proposed resolution

**Input**:
- Last user message
- Agent state

**Processing Flow**:
```
1. Extract last user message
2. Build feedback analysis prompt
3. Invoke structured LLM with FeedbackCheck schema
4. Parse is_satisfied boolean
```

**Output**:
```json
{
  "is_satisfied": Boolean
}
```

---

#### 2.1.4 Ticketing Agent Node
**Purpose**: Coordinate ticket creation with context-aware decision logic

**Input**:
- Agent state (category, priority, rag_context, is_relevant, messages)

**Processing Flow**:
```
1. Extract state variables (assignment_group, category, rag_context, is_relevant)
2. Determine prompt strategy:
   IF rag_context exists AND is_relevant:
     - Summarize solution for user
     - Ask if issue resolved
   ELSE:
     - Prepare automatic ticket creation
     - Use classification context
3. Bind LLM with tools (create_ticket, lookup_ticket)
4. Prepare system prompt + conditional prompt_addition
5. Invoke LLM with bound tools
6. Return LLM response with tool calls
```

**Tool Function Signatures**:

```python
@tool
def create_ticket(
    title: str, 
    description: str, 
    priority: str, 
    category: str,
    assignement_group: str
) -> str

@tool
def lookup_ticket(ticket_id: str) -> str
```

**External Integration**: AWS Lambda functions
- `Create_ticket`: Invokes Lambda ARN to create ticket
- `Lookup_ticket`: Invokes Lambda ARN to retrieve ticket details

---

#### 2.1.5 Router Functions

**RAG Router**:
```python
def rag_router(state: AgentState) -> Literal["ticketing_agent", "classification_node"]:
    if state.get("is_relevant"):
        return "ticketing_agent"  
    return "classification_node"
```

**Feedback Router**:
```python
def feedback_router(state: AgentState) -> Literal["end", "classification_node"]:
    if state.get("is_satisfied"):
        return "end"             
    return "classification_node"
```

---

### 2.2 State Machine Definition

#### AgentState (Pydantic Model)
```python
class AgentState(MessagesState):
    is_satisfied: bool           # User satisfaction flag
    is_relevant: bool            # RAG relevance flag
    category: str                # Issue category
    priority: str                # Issue priority
    assignment_group: str        # Target support team
    rag_context: str            # Retrieved context from knowledge base
```

---

### 2.3 Workflow Execution Path

#### Successful RAG Path (High Confidence)
```
START → RAG_check_node [is_relevant=True] 
  → rag_router → ticketing_agent [provides solution] 
  → feedback_check 
  → feedback_router → END (if satisfied)
```

#### No Match Path (Low Confidence)
```
START → RAG_check_node [is_relevant=False] 
  → rag_router → classification_node [categorize & prioritize] 
  → ticketing_agent [prepare for ticket creation] 
  → tools node [create_ticket] 
  → feedback_check → feedback_router → classification_node (if unsatisfied)
```

---

## 3. Data Sources and Data Engineering Steps

### 3.1 Data Sources

#### 3.1.1 Primary Data Source
**Synthetic Ticket Dataset** (`Data/synthetic_tickets_dataset.csv`)
- **Records**: 19+ IT support tickets
- **Source Type**: Synthetic/Training data
- **Format**: CSV with delimiter `,`
- **Encoding**: UTF-8

#### 3.1.2 Data Attributes
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| ticket_id | String | Unique ticket identifier | INCW454L |
| title | String | Brief issue description | Switch port failure on SW-ACCESS-02 |
| description | String | Detailed problem statement | Wireless users unable to maintain stable connections |
| category | String | Issue classification | Network, Infrastructure, Database, etc. |
| priority | String | Urgency level | Critical, High, Medium, Low |
| resolution | String | Applied solution | Corrected VLAN configuration |
| created_date | Date | Ticket creation timestamp | 17-09-2025 10:36 |
| status | String | Ticket state | Resolved, Closed |
| resolution_time_hours | Integer | Time to resolution | 37 |

---

### 3.2 Data Engineering Pipeline

#### Step 1: Data Extraction
```
Source: synthetic_tickets_dataset.csv
Process:
  - Read CSV using pandas.read_csv()
  - Validate encoding and delimiter
  - Handle missing values (if any)
```

#### Step 2: Data Transformation
```
Operations:
  1. Text Concatenation
     search_text = title + " " + description
     
  2. Metadata Extraction
     metadata = ['resolution', 'priority', 'category', 'status']
     
  3. ID Generation
     ids = [f"ticket_{i}" for i in range(len(text))]
```

#### Step 3: Embedding Generation
```
Model: SentenceTransformer ('all-MiniLM-L6-v2')
Process:
  1. Initialize embedding function via chromadb
  2. Transform search_text to embeddings
  3. Dimension: 384-dimensional vectors
  4. Similarity metric: Cosine distance
```

#### Step 4: Vector Store Ingestion
```
Destination: ChromaDB Cloud
Process:
  1. Initialize CloudClient with credentials
  2. Create/retrieve 'Incidents-collection'
  3. Add documents with:
     - documents: search_text
     - metadatas: metadata records
     - ids: generated IDs
  4. Configure HNSW index with cosine space
```

#### Step 5: Query Processing
```
At Runtime:
  1. Accept user query (latest message)
  2. Generate embedding for query
  3. Execute similarity search (n_results=2)
  4. Filter by where={"status": "Closed"}
  5. Calculate confidence_score = 1 - distance
  6. Apply threshold (0.7)
```

---

### 3.3 Data Quality Measures

- **Validation**: Check for duplicate records before embedding
- **Filtering**: Only closed/resolved incidents in retrieval
- **Scoring**: Confidence threshold prevents low-quality matches
- **Metadata**: Ensures resolution context is available
- **Error Handling**: Graceful fallback to classification on retrieval failure

---

## 4. Data Model & Entity Relationship Diagram

### 4.1 Core Entities

#### Entity 1: Ticket
```
Ticket {
  ticket_id: PRIMARY_KEY (UUID/String)
  title: String (255)
  description: String (1000)
  category: Foreign_Key → Category
  priority: Foreign_Key → Priority
  status: Foreign_Key → Status
  created_date: DateTime
  resolved_date: DateTime (nullable)
  resolution_time_hours: Integer
}
```

#### Entity 2: Category
```
Category {
  category_id: PRIMARY_KEY (INT)
  name: Enum String
  assignment_group: String
  description: String (500)
}
```

#### Entity 3: Priority
```
Priority {
  priority_id: PRIMARY_KEY (INT)
  level: Enum String (Low, Medium, High, Critical)
  sla_hours: Integer
  escalation_threshold: Integer
}
```

#### Entity 4: Status
```
Status {
  status_id: PRIMARY_KEY (INT)
  name: Enum String (Open, In Progress, Resolved, Closed)
  description: String
}
```

#### Entity 5: Resolution
```
Resolution {
  resolution_id: PRIMARY_KEY (UUID)
  ticket_id: Foreign_Key → Ticket
  resolution_text: String (2000)
  resolution_type: Enum (Automated, Manual)
  confidence_score: Decimal (0-1)
  resolved_by: String (Agent name)
}
```

#### Entity 6: ConversationMessage
```
ConversationMessage {
  message_id: PRIMARY_KEY (UUID)
  ticket_id: Foreign_Key → Ticket
  sender: Enum (User, Agent, System)
  content: String (5000)
  timestamp: DateTime
  message_type: Enum (Text, Tool_Call, Tool_Response)
}
```

---

### 4.2 Entity Relationship Diagram (ERD)

```
┌─────────────────────────────────────────────────────────────┐
│                        Category                             │
│  ┌──────────────────────────────────────┐                  │
│  │ category_id (PK)                     │                  │
│  │ name (Infrastructure, Application...)│                  │
│  │ assignment_group                     │                  │
│  │ description                          │                  │
│  └──────────────────────────────────────┘                  │
│                    ▲                                        │
│                    │ (1:M)                                  │
└────────────────────┼────────────────────────────────────────┘
                     │
    ┌────────────────┼──────────────────┐
    │                │                  │
    │                │                  │
┌───▼──────────────┐ │         ┌────────▼───────────┐
│   Status         │ │         │    Priority        │
├──────────────────┤ │         ├────────────────────┤
│ status_id (PK)   │ │         │ priority_id (PK)   │
│ name             │ │         │ level              │
│ description      │ │         │ sla_hours          │
└────────────────┬─┘ │         │ escalation_thresh. │
                 │   │         └────────┬───────────┘
                 │   │                  │
                 │   │                  │
            ┌────▼───▼──────────────────▼────┐
            │         Ticket                 │
            ├─────────────────────────────────┤
            │ ticket_id (PK)                  │
            │ title                           │
            │ description                     │
            │ category_id (FK)                │
            │ priority_id (FK)                │
            │ status_id (FK)                  │
            │ created_date                    │
            │ resolved_date                   │
            │ resolution_time_hours           │
            └────┬─────────────────────┬──────┘
                 │ (1:M)               │ (1:M)
     ┌───────────▼──┐        ┌────────▼──────────┐
     │ Resolution   │        │Conversation      │
     ├──────────────┤        │Message            │
     │ resolution_id│        ├───────────────────┤
     │ ticket_id(FK)│        │ message_id (PK)   │
     │ resolution   │        │ ticket_id (FK)    │
     │ resolution   │        │ sender            │
     │ confidence   │        │ content           │
     │ resolved_by  │        │ timestamp         │
     └──────────────┘        │ message_type      │
                             └───────────────────┘
```

---

### 4.3 Relationships Summary

| From | To | Type | Cardinality | Description |
|------|----|----|----------|-------------|
| Category | Ticket | 1:M | One category has many tickets | Issue classification |
| Priority | Ticket | 1:M | One priority level has many tickets | Urgency assignment |
| Status | Ticket | 1:M | One status has many tickets | Ticket lifecycle |
| Ticket | Resolution | 1:M | One ticket has many resolutions | Multiple attempts |
| Ticket | ConversationMessage | 1:M | One ticket has many messages | Multi-turn dialogue |

---

## 5. Data Flow Diagram (DFD)

### 5.1 Level 0 - Context Diagram

```
        ┌─────────────┐
        │   USER      │
        └──────┬──────┘
               │
          Chat Messages
               │
        ┌──────▼───────────────────────────┐
        │                                  │
        │   IT Support Agent System        │
        │   (Context Level)                │
        │                                  │
        └──────┬───────────────────────────┘
               │
      ┌────────┴──────────┐
      │                   │
      ▼                   ▼
  ┌────────────┐    ┌──────────────┐
  │ Knowledge  │    │ Ticketing    │
  │ Base       │    │ System       │
  │ (ChromaDB) │    │ (Lambda)     │
  └────────────┘    └──────────────┘
```

---

### 5.2 Level 1 - Main DFD

```
┌────────────────────────────────────────────────────────────────────┐
│                        User Interface                              │
│                    (Chat Application)                              │
└────────────────┬───────────────────────────────────────────────────┘
                 │ D1: User Query Message
                 │
         ┌───────▼──────────────────────┐
         │  1.0 Message Parser          │
         │  (Extract & Validate)        │
         └───────┬──────────────────────┘
                 │ D2: Parsed Query
                 │
         ┌───────▼──────────────────────┐
         │  2.0 RAG Check Node          │
         │  (Semantic Search)           │
         └───────┬──────────────────────┘
                 │ D3: Search Query
                 │
      ┌──────────▼──────────────┐
      │                         │
      │  3.0 Vector Retrieval   │
      │  (ChromaDB Cloud)       │
      │                         │
      └──────────┬──────────────┘
                 │ D4: Search Results
                 │
         ┌───────▼──────────────────────┐
         │  4.0 Confidence Scoring      │
         │  (Similarity Analysis)       │
         └───────┬──────────────────────┘
                 │
            ┌────┴──────────┐
    YES:    │ High Conf.    │ NO: Low Conf.
    (>=0.7) │               │ (<0.7)
            │               │
      ┌─────▼──────┐  ┌─────▼──────────────┐
      │ 5.0 Format │  │ 6.0 Classification │
      │ Solution   │  │ Node               │
      │            │  │                    │
      └─────┬──────┘  └──────┬─────────────┘
            │                │ D5: Category & Priority
            │                │
            │         ┌──────▼──────────────┐
            │         │ 7.0 LLM Analysis   │
            │         │ (Structured Output)│
            │         └──────┬─────────────┘
            │                │
      ┌─────▼────────────────▼─────────┐
      │  8.0 Ticketing Agent Node      │
      │  (Decision & Tool Selection)   │
      └─────┬────────────────────────┬─┘
            │ D6: Tool Calls        │ D7: Ticket Decision
            │                       │
      ┌─────▼────────────────┐   ┌──▼────────────────┐
      │ 9.0 Execute Tools    │   │ 10.0 State Update │
      │ ├─ create_ticket()   │   │                   │
      │ └─ lookup_ticket()   │   │                   │
      └─────┬────────────────┘   └────────┬──────────┘
            │ D8: Tool Response   │ D9: Updated State
            │                     │
      ┌─────▼─────────────────────▼────────┐
      │ 11.0 AWS Lambda Backend            │
      │ (Ticket Management System)          │
      └─────┬───────────────────────────────┘
            │ D10: Ticket Data (create/query)
            │
      ┌─────▼───────────────────────────┐
      │ 12.0 Database Operations        │
      │ (Relational Ticket Database)    │
      └─────┬───────────────────────────┘
            │ D11: Ticket Record
            │
      ┌─────▼────────────────────────────────┐
      │ 13.0 Feedback Check                 │
      │ (Parse User Satisfaction)            │
      └─────┬────────────────────────────────┘
            │
        ┌───┴──────────┐
        │ Satisfied?   │
    YES │              │ NO
        │              │
      ┌─▼──┐        ┌──▼────────┐
      │END │        │ Re-classify│
      └────┘        │ & Retry    │
                    └────────────┘

Legend:
D1-D11 = Data Flows
1.0-13.0 = Processes
[Boxes] = Processes
```

---

### 5.3 Data Store Specifications

| Store | Type | Technology | Purpose |
|-------|------|-----------|---------|
| DS-1: Knowledge Base | Persistent | ChromaDB Cloud | Store embeddings & resolutions |
| DS-2: Ticket DB | Persistent | Relational DB (via Lambda) | Store ticket records |
| DS-3: Conversation State | Temporary | Memory | Maintain message history |
| DS-4: Metadata Cache | Temporary | In-Memory | Category/Priority mappings |

---

## 6. Sequence Diagram

### 6.1 Successful Resolution Path (RAG Hit)

```
User      UI          LLM         RAG        State    Ticketing  Output
 │         │           │          │          │        Agent       │
 ├────────>│ Query      │          │          │         │         │
 │         ├──────────>│          │          │         │         │
 │         │ message   │          │          │         │         │
 │         │           │                    │         │         │
 │         │           ├─────────────────>  │         │         │
 │         │           │ Extract Query      │         │         │
 │         │           │ <────────────────┤ │         │         │
 │         │           │ Result            │         │         │
 │         │           │                    │         │         │
 │         │           ├──────────────────────────┐  │         │
 │         │           │ Call RAG_check_node()   │  │         │
 │         │           │ <──────────────────────┤  │         │
 │         │           │ is_relevant=True       │  │         │
 │         │           │ rag_context="..."      │  │         │
 │         │           │                        │  │         │
 │         │           ├────────────────────────────┤         │
 │         │           │ Format Solution        │  │ ├─────> │
 │         │           │ Update State           │  │ │       │
 │         │           │ <─────────────────────┤  │ │       │
 │         │           │ Message Response      │  │ │       │
 │         │           │ <────────────────────────┤        │
 │         │ Solution  │                          │         │
 │<────────┤ Response  │                          │         │
 │         │           │                          │         │
 │ Query   │ "Does this│                          │         │
 │<────────┤ solve it?"│                          │         │
 │         │           │                          │         │
 │ Yes     │           │                          │         │
 ├────────>│ Satisfaction│                        │         │
 │         ├──────────>│ Check Feedback         │         │
 │         │           ├────────────────────────────────┤ 
 │         │           │ is_satisfied=True              │
 │         │           │ <────────────────────────────┤
 │         │           │ Return END                     │
 │         │<──────────┤ Conversation Closed           │
 │         │ Success   │                               │
 │<────────┤ Message   │                               │
 │         │           │                               │
```

---

### 6.2 No RAG Match & Ticket Creation Path

```
User      UI          LLM         RAG       Classification  Ticketing    Lambda    Output
 │         │           │          │            │            Agent       │         │
 ├────────>│ Query      │          │            │             │          │        │
 │         ├──────────>│          │            │             │          │        │
 │         │ message   │          │            │             │          │        │
 │         │           │                       │             │          │        │
 │         │           ├──────────────────┐   │             │          │        │
 │         │           │ Query ChromaDB   │   │             │          │        │
 │         │           │ <────────────────┤   │             │          │        │
 │         │           │ Distance=0.95    │   │             │          │        │
 │         │           │ confidence<0.7   │   │             │          │        │
 │         │           │ is_relevant=False│   │             │          │        │
 │         │           │ <────────────────────────────────┐ │          │        │
 │         │           │ Route: Classification│           │ │          │        │
 │         │           │                  │   ├──────────>│ │          │        │
 │         │           │                  │   │ Analyze   │ │          │        │
 │         │           │                  │   │ Message   │ │          │        │
 │         │           │                  │   │ <───────┤ │          │        │
 │         │           │                  │   │ category  │ │          │        │
 │         │           │                  │   │ priority  │ │          │        │
 │         │           │                  │   │ group     │ │          │        │
 │         │           │                  │   │<──────────────────────>│        │
 │         │           │                  │   │          │ │ Ticketing Decision │
 │         │           │                  │   │          │ │ Prepare Tool Call  │
 │         │           │                  │   │          │ │ <──────────────┤  │
 │         │           │                  │   │          │ │ Tool Response  │  │
 │         │           │                  │   │          │ │ call create_   │  │
 │         │           │                  │   │          │ │ ticket()       │  │
 │         │           │                  │   │          │ ├──────────────>│  │
 │         │           │                  │   │          │ │ Payload:      │  │
 │         │           │                  │   │          │ │ {title, desc..│  │
 │         │           │                  │   │          │ │<──────────────┤  │
 │         │           │                  │   │          │ │ Lambda Call   │  │
 │         │           │                  │   │          │ ├──────────────────>│
 │         │           │                  │   │          │ │ Create Ticket │  │
 │         │           │                  │   │          │ │ <─────────────────┤
 │         │           │                  │   │          │ │ {ticket_id}   │  │
 │         │           │                  │   │          │ │ <──────────────┤  │
 │         │           │                  │   │          │ │ Return Success│  │
 │         │<──────────┤                  │   │          │<┤ Response      │  │
 │         │ Ticket ID │                  │   │          │ │               │  │
 │<────────┤ Created!  │                  │   │          │ │               │  │
 │ No      │           │                  │   │          │ │               │  │
 ├────────>│ Still     │                  │   │          │ │               │  │
 │         │ Issue?    │                  │   │          │ │               │  │
 │ Yes     │           │                  │   │          │ │               │  │
 ├────────>│ Continue  │ (Re-enter cycle) │   │          │ │               │  │
 │         │           │                  │   │          │ │               │  │
```

---

## 7. State Transition Diagram

### 7.1 Conversation State Machine

```
                      ┌──────────────┐
                      │    START     │
                      └──────┬───────┘
                             │
                             │ User Message Received
                             │
                    ┌────────▼────────────┐
                    │  RAG_CHECK_NODE     │
                    │  ───────────────   │
                    │ Query Knowledge    │
                    │ Base & Score       │
                    └────────┬──────┬────┘
                             │      │
                    ┌────────┘      └────────┐
         is_relevant│                       │is_relevant
              =True │                       │=False
                    │                       │
          ┌─────────▼──────────────┐   ┌───▼──────────────┐
          │ CLASSIFICATION_NODE    │   │ TICKETING_AGENT  │
          │ ───────────────────    │   │ ───────────────  │
          │ Categorize & Prioritize│   │ Format Solution  │
          │ Set Assignment Group   │   │ & Present to User│
          └─────────────┬──────────┘   └────────┬─────────┘
                        │                       │
                        └───────────┬───────────┘
                                    │
                            ┌───────▼──────────┐
                            │ FEEDBACK_CHECK   │
                            │ ──────────────  │
                            │ User Satisfied? │
                            └───┬──────────┬──┘
                                │          │
                     is_satisfied   is_satisfied
                         │ =True        │=False
                         │              │
                    ┌────▼─┐   ┌───────▼───────────┐
                    │ END  │   │ CLASSIFICATION_   │
                    │(Loop │   │ NODE (Retry)      │
                    │ Ends)│   │                   │
                    └──────┘   └────────┬──────────┘
                                        │
                                        │ Categorize & Prioritize
                                        │ (Update Context)
                                        │
                                  ┌─────▼──────────────┐
                                  │ TICKETING_AGENT    │
                                  │ ─────────────────  │
                                  │ Create Ticket      │
                                  └─────┬──────────────┘
                                        │
                                  ┌─────▼──────────────┐
                                  │ TOOLS_NODE         │
                                  │ ─────────────────  │
                                  │ Execute Tool Call: │
                                  │ create_ticket()    │
                                  └─────┬──────────────┘
                                        │
                                  ┌─────▼──────────────┐
                                  │ TICKETING_AGENT    │
                                  │ ─────────────────  │
                                  │ Format Success Msg │
                                  │ "Ticket ID: ..."   │
                                  └─────┬──────────────┘
                                        │
                                        │
                                  ┌─────▼──────────────┐
                                  │ FEEDBACK_CHECK     │
                                  │ ─────────────────  │
                                  │ Confirm Resolution │
                                  └────────────────────┘
```

---

### 7.2 State Transition Table

| Current State | Event | Action | Next State | Output |
|---------------|-------|--------|-----------|--------|
| START | User Message | Parse & Extract Query | RAG_CHECK_NODE | Query Processed |
| RAG_CHECK_NODE | High Confidence (≥0.7) | Format Solution | TICKETING_AGENT | Solution Presented |
| RAG_CHECK_NODE | Low Confidence (<0.7) | Prepare Classification | CLASSIFICATION_NODE | N/A |
| CLASSIFICATION_NODE | Category & Priority Determined | Update State | TICKETING_AGENT | Context Updated |
| TICKETING_AGENT | Solution Available | Explain to User | FEEDBACK_CHECK | Awaiting User Response |
| TICKETING_AGENT | No Solution (Low Conf) | Prepare Ticket Creation | TOOLS_NODE | Ticket Input Ready |
| TOOLS_NODE | Tool Execution | Invoke create_ticket() Lambda | TICKETING_AGENT | ticket_id Returned |
| FEEDBACK_CHECK | is_satisfied = True | Terminate Conversation | END | Success |
| FEEDBACK_CHECK | is_satisfied = False | Re-classify Issue | CLASSIFICATION_NODE | Cycle Retry |
| CLASSIFICATION_NODE → TICKETING_AGENT → TOOLS_NODE | Repeat Cycle | Create Ticket | FEEDBACK_CHECK | New Ticket ID |
| FEEDBACK_CHECK | Final Satisfaction | Terminate | END | Conversation Closed |

---

### 7.3 State Variables Through Lifecycle

```
┌──────────────────────────────────────────────────────────────────┐
│ AgentState Evolution During Workflow                             │
└──────────────────────────────────────────────────────────────────┘

Initial State (User enters query):
{
  messages: [HumanMessage(content="User query...")],
  is_satisfied: None,
  is_relevant: None,
  category: None,
  priority: None,
  assignment_group: None,
  rag_context: None
}
                            │
                            │ After RAG_CHECK_NODE
                            ▼
State after RAG (High Confidence):
{
  messages: [...],
  is_satisfied: None,
  is_relevant: True,           ◄── UPDATED
  category: "Network",         ◄── From metadata
  priority: "Critical",        ◄── From metadata
  assignment_group: None,
  rag_context: "Resolution: Fixed DNS..." ◄── UPDATED
}
                            │
                            │ After TICKETING_AGENT
                            ▼
State after Agent Response:
{
  messages: [..., AIMessage(content="The solution is...")],
  is_satisfied: None,
  is_relevant: True,
  category: "Network",
  priority: "Critical",
  assignment_group: "NETWORK_OPERATIONS",
  rag_context: "Resolution: Fixed DNS..."
}
                            │
                            │ After FEEDBACK_CHECK
                            ▼
Final State (Satisfied):
{
  messages: [..., HumanMessage("Yes, it works!")],
  is_satisfied: True,          ◄── UPDATED
  is_relevant: True,
  category: "Network",
  priority: "Critical",
  assignment_group: "NETWORK_OPERATIONS",
  rag_context: "Resolution: Fixed DNS..."
}
                            │
                            │ Route: feedback_router → END
                            ▼
        Conversation Terminated (Success)

─────────────────────────────────────────────────────────────────

Alternative Path (No RAG Match):

After RAG_CHECK_NODE (Low Confidence):
{
  messages: [...],
  is_satisfied: None,
  is_relevant: False,          ◄── UPDATED
  category: None,
  priority: None,
  assignment_group: None,
  rag_context: ""              ◄── Empty
}
                            │
                            │ Route: rag_router → CLASSIFICATION_NODE
                            ▼
After CLASSIFICATION_NODE:
{
  messages: [...],
  is_satisfied: None,
  is_relevant: False,
  category: "Infrastructure",  ◄── UPDATED
  priority: "High",            ◄── UPDATED
  assignment_group: "INFRA_TEAM_L2" ◄── UPDATED
  rag_context: ""
}
                            │
                            │ After TICKETING_AGENT (prepare ticket)
                            ▼
After TICKETING_AGENT (Tool Binding):
{
  messages: [..., AIMessage(tool_calls=[create_ticket(...)])],
  is_satisfied: None,
  is_relevant: False,
  category: "Infrastructure",
  priority: "High",
  assignment_group: "INFRA_TEAM_L2",
  rag_context: ""
}
                            │
                            │ After TOOLS_NODE execution
                            ▼
After Tool Execution:
{
  messages: [..., ToolMessage(content="Ticket created with ID: INC12345")],
  is_satisfied: None,
  is_relevant: False,
  category: "Infrastructure",
  priority: "High",
  assignment_group: "INFRA_TEAM_L2",
  rag_context: ""
}
                            │
                            │ After FEEDBACK_CHECK
                            ▼
Final Check:
{
  messages: [...],
  is_satisfied: False,         ◄── User wants to continue
  is_relevant: False,
  category: "Infrastructure",
  priority: "High",
  assignment_group: "INFRA_TEAM_L2",
  rag_context: ""
}
                            │
                            │ Route: feedback_router → CLASSIFICATION_NODE (retry)
                            ▼
        Cycle repeats or conversation ends based on user choice
```

---

## 8. Key System Characteristics

### 8.1 Performance Parameters
- **RAG Threshold**: 0.7 (70% confidence)
- **Max Retrieval Results**: 2 documents
- **Embedding Dimension**: 384 (Sentence-Transformers model)
- **Similarity Metric**: Cosine distance (converted to confidence score)
- **Supported Categories**: 6 (Infrastructure, Application, Security, Database, Network, Access Management)
- **Priority Levels**: 4 (Low, Medium, High, Critical)

### 8.2 Error Handling Strategy
- **RAG Failures**: Graceful fallback to classification
- **LLM Call Failures**: Return error message to user
- **Tool Invocation Failures**: Return failure message, suggest retry
- **State Corruption**: Reinitialize from message history

### 8.3 Integration Points
- **LLM**: AWS Bedrock (Amazon Nova Lite v1:0)
- **Vector DB**: ChromaDB Cloud
- **Ticketing Backend**: AWS Lambda functions
- **Database**: Relational database (via Lambda)
- **Auth**: AWS IAM credentials

---

## 9. Deployment & Dependencies

### 9.1 Core Dependencies
```
boto3>=1.42.87                  # AWS SDK
chromadb>=1.5.5                 # Vector Database
langchain>=1.2.15               # LLM Framework
langchain-aws>=1.4.3            # AWS Integration
langchain-core>=1.2.26          # Core Components
langgraph>=1.1.6                # Workflow Orchestration
sentence-transformers>=5.3.0    # Embedding Model
pydantic>=2.12.5                # Data Validation
python-dotenv>=1.2.2            # Environment Variables
```

### 9.2 Environment Configuration
```
Required Environment Variables:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- CHROMA_DB (API key for ChromaDB Cloud)
```

---

## 10. Conclusion

This AI-Powered IT Support Agent System demonstrates a sophisticated multi-agent orchestration pattern combining RAG technology with LLM-based decision making. The system is designed to:

1. **Maximize Automation**: Provide solutions from knowledge base when available
2. **Intelligent Classification**: Categorize issues for appropriate team routing
3. **Seamless Ticket Management**: Create and manage tickets with context awareness
4. **User Satisfaction**: Track and measure resolution effectiveness
5. **Scalability**: Leverage cloud-based vector DB and serverless compute

The architecture supports iterative refinement and can be enhanced with additional agents, improved classification models, and extended integration with various IT systems.

---

**Document Version**: 1.0  
**Date**: May 10, 2026  
**Author**: Technical Documentation Team  
**Status**: Final
