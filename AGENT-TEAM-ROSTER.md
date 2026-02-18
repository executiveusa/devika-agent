# SYNTHIA Agent Team Roster
## Complete List of All Agent Team Members

**Generated:** 2026-02-18  
**Total Agents:** 16 Built-in + 6 Domain Experts (Placeholder)

---

## Agent Categories

### PRIMARY Agents (Always Active)
These agents are always running and handle core functionality.

| # | Agent Name | Role | File Location | Archon X Link |
|---|------------|------|---------------|---------------|
| 1 | **Planner** | Generates step-by-step plans from user prompts | `src/agents/planner/` | Required |
| 2 | **Researcher** | Extracts search queries and research context | `src/agents/researcher/` | Required |
| 3 | **Coder** | Generates code from plans and researched context | `src/agents/coder/` | Required |
| 4 | **Formatter** | Cleans and formats crawled web content | `src/agents/formatter/` | Required |

### ACTION Agents (Triggered by Intent)
These agents are activated based on user intent detection.

| # | Agent Name | Role | Trigger Keywords | File Location | Archon X Link |
|---|------------|------|------------------|---------------|---------------|
| 5 | **Runner** | Executes code in sandboxed environment | "run", "execute", "test" | `src/agents/runner/` | Required |
| 6 | **Patcher** | Debugs and fixes issues | "fix", "debug", "patch" | `src/agents/patcher/` | Required |
| 7 | **Feature** | Implements new features | "implement", "add feature" | `src/agents/feature/` | Required |
| 8 | **Reporter** | Generates documentation and reports | "report", "document" | `src/agents/reporter/` | Required |
| 9 | **Answer** | Provides direct answers to questions | "what", "how", "why" | `src/agents/answer/` | Required |

### SUPPORT Agents (Background Operations)
These agents provide supporting functionality.

| # | Agent Name | Role | File Location | Archon X Link |
|---|------------|------|---------------|---------------|
| 10 | **Architect** | Architecture analysis and design recommendations | `src/synthia/agents/architect.py` | Required |
| 11 | **Tester** | Quality assurance and test generation | `src/synthia/agents/tester.py` | Required |
| 12 | **Documenter** | Documentation generation (README, API docs) | `src/synthia/agents/documenter.py` | Required |
| 13 | **Security** | Security analysis and vulnerability scanning | `src/synthia/agents/security.py` | Required |

### ORCHESTRATOR Agents
These agents coordinate and manage other agents.

| # | Agent Name | Role | File Location | Archon X Link |
|---|------------|------|---------------|---------------|
| 14 | **Decision** | Handles special commands (git clone, browser) | `src/agents/decision/` | Required |
| 15 | **Internal Monologue** | Tracks agent thoughts and state | `src/agents/internal_monologue/` | Required |
| 16 | **Action** | Determines next action from user intent | `src/agents/action/` | Required |

### DOMAIN Experts (Placeholder - Future Implementation)
Specialized knowledge agents for specific domains.

| # | Agent Name | Role | Status | Repo | Archon X Link |
|---|------------|------|--------|------|---------------|
| 17 | **Web Design Expert** | Web development best practices | Placeholder | TBD | Required |
| 18 | **Physics Expert** | Physics calculations and knowledge | Placeholder | TBD | Required |
| 19 | **Chemistry Expert** | Chemistry domain knowledge | Placeholder | TBD | Required |
| 20 | **Math Expert** | Mathematical operations | Placeholder | TBD | Required |
| 21 | **Medical Expert** | Healthcare domain knowledge | Placeholder | TBD | Required |
| 22 | **Stack Overflow** | Programming Q&A retrieval | Placeholder | TBD | Required |

---

## Agent Details

### 1. Planner
- **Category:** PRIMARY
- **Purpose:** Takes user prompts and generates step-by-step execution plans
- **Input:** User prompt string
- **Output:** Structured plan with steps, focus areas, and summary
- **Prompt Template:** `src/agents/planner/prompt.jinja2`
- **Memory Usage:** Reads project context, stores plan for other agents

### 2. Researcher
- **Category:** PRIMARY
- **Purpose:** Extracts search queries from plans and gathers context
- **Input:** Plan from Planner
- **Output:** Ranked search queries, relevant context
- **Prompt Template:** `src/agents/researcher/prompt.jinja2`
- **Memory Usage:** Stores search results for project

### 3. Coder
- **Category:** PRIMARY
- **Purpose:** Generates code based on plans and researched context
- **Input:** Plan + Research context
- **Output:** Code files with proper structure
- **Prompt Template:** `src/agents/coder/prompt.jinja2`
- **Memory Usage:** Stores code patterns for future reference

### 4. Formatter
- **Category:** PRIMARY
- **Purpose:** Cleans and formats crawled web content
- **Input:** Raw crawled content
- **Output:** Clean, structured content
- **Prompt Template:** `src/agents/formatter/prompt.jinja2`
- **Memory Usage:** Stores formatted content

### 5. Runner
- **Category:** ACTION
- **Purpose:** Executes code in sandboxed environment
- **Input:** Code to execute, language specification
- **Output:** Execution results, errors, output
- **Prompt Template:** `src/agents/runner/prompt.jinja2`
- **Sandbox:** Docker-based isolation (src/sandbox/code_runner.py)

### 6. Patcher
- **Category:** ACTION
- **Purpose:** Debugs and fixes issues in existing code
- **Input:** Error description, existing code
- **Output:** Fixed code with explanation
- **Prompt Template:** `src/agents/patcher/prompt.jinja2`

### 7. Feature
- **Category:** ACTION
- **Purpose:** Implements new features in existing projects
- **Input:** Feature specification, existing codebase
- **Output:** Modified files with new feature
- **Prompt Template:** `src/agents/feature/prompt.jinja2`

### 8. Reporter
- **Category:** ACTION
- **Purpose:** Generates comprehensive project reports
- **Input:** Project files, context
- **Output:** PDF report with overview, API docs, setup instructions
- **Prompt Template:** `src/agents/reporter/prompt.jinja2`

### 9. Answer
- **Category:** ACTION
- **Purpose:** Provides direct answers to user questions
- **Input:** Question, context
- **Output:** Direct answer with explanation
- **Prompt Template:** `src/agents/answer/prompt.jinja2`

### 10. Architect (SYNTHIA)
- **Category:** SUPPORT
- **Purpose:** Analyzes project architecture and provides recommendations
- **Input:** Scan result from Repository Scanner
- **Output:** Architecture report with components, dependencies, issues
- **File:** `src/synthia/agents/architect.py`
- **Features:** Component detection, dependency graph, Mermaid diagrams

### 11. Tester (SYNTHIA)
- **Category:** SUPPORT
- **Purpose:** Generates and runs tests for code quality
- **Input:** Code files, test requirements
- **Output:** Test files, coverage reports
- **File:** `src/synthia/agents/tester.py`
- **Features:** Unit tests, integration tests, E2E tests

### 12. Documenter (SYNTHIA)
- **Category:** SUPPORT
- **Purpose:** Generates comprehensive documentation
- **Input:** Project files, context
- **Output:** README, API docs, CHANGELOG, CONTRIBUTING
- **File:** `src/synthia/agents/documenter.py`
- **Features:** Multi-format output, API endpoint detection

### 13. Security (SYNTHIA)
- **Category:** SUPPORT
- **Purpose:** Scans for security vulnerabilities and secrets
- **Input:** Project files
- **Output:** Security report with issues, recommendations
- **File:** `src/synthia/agents/security.py`
- **Features:** SQL injection, XSS, hardcoded secrets, dependency vulnerabilities

### 14. Decision
- **Category:** ORCHESTRATOR
- **Purpose:** Handles special commands that don't fit other agents
- **Input:** Command string
- **Output:** Executed command result
- **Prompt Template:** `src/agents/decision/prompt.jinja2`
- **Commands:** git clone, browser interaction, special operations

### 15. Internal Monologue
- **Category:** ORCHESTRATOR
- **Purpose:** Tracks agent thoughts and internal state
- **Input:** Agent state updates
- **Output:** Thought stream for UI display
- **Prompt Template:** `src/agents/internal_monologue/prompt.jinja2`

### 16. Action
- **Category:** ORCHESTRATOR
- **Purpose:** Determines appropriate action from user intent
- **Input:** User message
- **Output:** Action keyword (run, test, deploy, fix, implement, report)
- **Prompt Template:** `src/agents/action/prompt.jinja2`

---

## Agent Communication Protocol

### Webhook Integration

All agents report to Archon X via the webhook system:

```python
from src.synthia.webhook import ArchonXWebhook

webhook = ArchonXWebhook(
    endpoint="https://archonx.yappyverse.ai/webhook",
    api_key="your-api-key"
)

# Agent reports task completion
webhook.report_task_completion(
    agent_name="Coder",
    task_id="task-123",
    project_name="my-app",
    result={
        "files_created": ["main.py", "utils.py"],
        "lines_of_code": 250,
        "status": "success"
    }
)
```

### Memory Linking

Each agent can access shared memory:

```python
from src.synthia.memory import MemoryManager, MemoryLayer

memory = MemoryManager()

# Store knowledge from agent
memory.store(
    key="coder:pattern:auth-flow",
    value={"pattern": "oauth", "provider": "google"},
    layer=MemoryLayer.PROJECT,
    agent="Coder",
    tags=["auth", "oauth"]
)

# Retrieve context for agent
context = memory.get_context(
    prompt="Add authentication",
    project_name="my-app"
)
```

---

## Individual Agent Repositories (Future)

Each agent should have its own repository with:

1. **Dedicated Codebase**
   - Agent logic
   - Prompt templates
   - Tests
   - Documentation

2. **Memory Linking**
   - Local memory storage
   - Archon X sync
   - Team memory sharing

3. **Webhook Integration**
   - Task start notification
   - Progress updates
   - Completion reports

4. **Independent Deployment**
   - Docker container
   - API endpoint
   - Health monitoring

### Repository Structure Template

```
agent-{name}/
  src/
    agent.py
    prompts/
      system.jinja2
      task.jinja2
  tests/
    test_agent.py
  memory/
    local.db
  config/
    config.toml
  Dockerfile
  README.md
  requirements.txt
```

---

## Next Steps

1. **Create Individual Repositories**
   - Set up GitHub repos for each agent
   - Configure Archon X webhooks
   - Set up memory synchronization

2. **Implement Domain Experts**
   - Build specialized knowledge bases
   - Create prompt templates for each domain
   - Integrate with existing agents

3. **Build Agent Swarm**
   - Implement sub-agent factory
   - Create task delegation system
   - Build swarm coordinator

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-18