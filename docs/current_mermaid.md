flowchart TD

%% ─────────── Developer entry point ───────────
subgraph DEV ["Developer Interaction"]
  direction TB
  U["CLI / (future) UI"]:::actor
end
U -->|spec file / text| P

%% ───────────── Core orchestration ─────────────
subgraph CORE ["meta_agent package"]
  direction TB
  P["SpecSchema & Parser"]:::core --> O
  O["MetaAgentOrchestrator"]:::core --> D
  D["decompose_spec (stub)"]:::core --> PE
  PE["PlanningEngine"]:::core --> SM
  SM["SubAgentManager"]:::core
end

%% ───────────── Sub-agent layer ────────────────
subgraph SUB ["Specialised Sub-Agents"]
  direction LR
  SA1["ToolDesignerAgent"]:::agent
  SA2["CoderAgent"]:::agent
  SA3["TesterAgent"]:::agent
  SA4["ReviewerAgent"]:::agent
  SAH(("…")):::agent
end
SM --> SA1 & SA2 & SA3 & SA4 & SAH

%% ── Zoom-in: ToolDesignerAgent internal flow ──
subgraph TOOL_DESIGNER ["ToolDesigner internals"]
  direction LR
  PB["PromptBuilder"]:::svc --> LC
  CB["ContextBuilder"]:::svc --> LC
  LC["LLMCodeGenerator"]:::svc --> CV
  CV["CodeValidator"]:::svc --> II
  LC -- validation fail --> FM
  FM["FallbackManager"]:::svc -.-> LC
  II["ImplementationInjector"]:::svc --> GT
  GT["GeneratedTool"]:::data
end
SA1 --> TOOL_DESIGNER

%% ──────── Sandbox, validation, registry ───────
subgraph EXEC ["Execution / Validation"]
  GT --> SB["SandboxManager"]:::core
  SB --> VR["validation.py"]:::core
end

subgraph STORAGE
  GT --> RG["ToolRegistry"]:::core
end

%% ───────────── External services ──────────────
subgraph EXT ["External Services"]
  LLM["LLM API"]:::ext --> LC
  AGENTS["OpenAI Agents SDK"]:::ext --> O
end

%% ───────────── Results back to dev ────────────
VR & RG --> F["Artifacts / Results"]:::data --> U

%% ─────────────── Class styling ────────────────
classDef actor fill:#4672b4,color:#fff,stroke:#333;
classDef core  fill:#47956f,color:#fff,stroke:#333;
classDef agent fill:#38a7e0,color:#fff,stroke:#333;
classDef svc   fill:#7a43b6,color:#fff,stroke:#333;
classDef data  fill:#de953e,color:#fff,stroke:#333;
classDef ext   fill:#8b251e,color:#fff,stroke:#333;

class U actor
class P,O,D,PE,SM,SB,VR,RG core
class SA1,SA2,SA3,SA4,SAH agent
class PB,CB,LC,CV,FM,II svc
class GT,F data
class LLM,AGENTS ext
