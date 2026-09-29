# GameBridge Thin Manual v1.1

## Runtime, Interaction & Plugin Chains

**Purpose:**
This document is the architectural map for continuing GameBridge development.

It is intentionally thin.

It describes **where a flow goes**, **which component owns it**, and **where to continue debugging**.

It is not a general user manual.

---

# 1. CORE PRINCIPLE

GameBridge is middleware.

It connects:

```text
Human
  ↕
AI cognitive runtime
  ↕
GameBridge interaction layer
  ↕
External application / plugin
```

GameBridge is **not** the AI and is **not** the agent.

The active plugin defines application-specific interaction formats.

---

# 2. STARTUP CHAIN

```text
main.py
  ↓
LocalizationCore
  ↓
GameBridgeIOLayer
  ↓
SessionManager
  ↓
ChannelMatrix
  ↓
TelemetryCore
  ↓
GameBridgeCore
  ↓
OllamaClient
  ↓
AILifecycleCore
  ↓
AdapterLoader
  ↓
available adapters
  ↓
GameBridgeGUI
  ↓
core.link_gui()
  ↓
CognitiveRouterCore
```

Important:

```text
TelemetryCore
```

is created once by `main.py`.

Telemetry does **not** create a polling worker.

The Ollama telemetry request callback is bound here:

```text
OllamaClient
  ↓
telemetry_request_callback
  ↓
TelemetryCore.request_telemetry()
```

---

# 3. AI ON / OFF CHAIN

## AI ON

```text
GUI AI toggle
  ↓
function_on_ai_toggle()
  ↓
GameBridgeCore.start_ai_runtime()
  ↓
AILifecycleCore.start_ai()
  ↓
OllamaClient.check_model_status()
  ↓
Ollama /api/show
  ↓
READY / OFFLINE / DISABLED / LOADING
```

AI ON does **not** forcibly unload or reload the model.

The lifecycle currently checks model availability/state.

Future memory restore/indexing belongs here.

---

## AI OFF

```text
GUI AI toggle
  ↓
function_on_ai_toggle()
  ↓
GameBridgeCore.stop_ai_runtime()
  ↓
AILifecycleCore.stop_ai()
  ↓
AILifecycleCore.unload_model()
  ↓
OllamaClient.unload_model()
  ↓
Ollama keep_alive = 0
  ↓
model unloaded
```

AI lifecycle shutdown is separate from cognitive runtime shutdown.

---

# 4. USER INTERACTION CHAIN

A human request creates one interaction ID.

```text
User input
  ↓
GameBridgeCore
  ↓
UserInteractionCore.start(user_text)
  ↓
interaction_id
  ↓
CognitiveRouterCore.route_transactional_flow(...)
  ↓
function_pipeline_worker(...)
```

`UserInteractionCore` only tracks the identity/lifecycle of the human interaction.

It does **not** perform:

* AI reasoning
* routing
* sequencing
* task management

One interaction may contain multiple cognitive steps.

---

# 5. COGNITIVE RUNTIME CHAIN

The important rule:

**OllamaClient owns the cognitive runtime.**

```text
User interaction
  ↓
CognitiveRouterCore
  ↓
function_pipeline_worker
  ↓
OllamaClient.generate_response()
  ↓
ONE cognitive step
  ↓
GameBridge dispatches that step
  ↓
completion acknowledgement
  ↓
OllamaClient.continue_runtime()
  ↓
NEXT cognitive step
  ↓
...
```

GameBridge does not contain a separate sequence engine.

The continuation decision belongs to the AI runtime.

When the runtime has no further step:

```text
continue_runtime()
  ↓
empty result
  ↓
pipeline exits
  ↓
runtime ends
```

Normal cognitive completion:

```text
OllamaClient.stop_runtime()
```

is a **soft runtime stop**.

It clears the current cognitive interaction state.

It does **not** unload the model.

---

# 6. CHANNEL 1

Channel 1 is human communication.

```text
AI result
  ↓
router output separation
  ↓
ordinary text
  ↓
ChannelMatrix.should_route_to_chat()
  ↓
IO Layer
  ↓
GUI
  ↓
AI (Channel 1)
```

Channel 1 is ordinary text.

Channel 1 is not an action payload.

---

# 7. CHANNEL 2

Channel 2 is AI → external application interaction.

```text
AI cognitive step
  ↓
router output separation
  ↓
plugin-defined JSON/action payload
  ↓
ChannelMatrix.should_route_to_adapter()
  ↓
IO Layer.send_to_kanal_2()
  ↓
active adapter.execute_interaction()
  ↓
external application
```

The active plugin defines the valid action format.

GameBridge must not invent application-specific Channel 2 actions.

---

# 8. TELEMETRY CHAIN

Telemetry is application information flowing back toward the AI.

It is **not an instruction**.

Current request-driven chain:

```text
AI cognitive runtime
  ↓
telemetry request
  ↓
OllamaClient.telemetry_request_callback
  ↓
TelemetryCore.request_telemetry()
  ↓
IO Layer.read_from_kanal_2()
  ↓
active adapter.read_telemetry()
  ↓
external application
  ↓
actual application state
  ↓
telemetry result
  ↓
OllamaClient
  ↓
runtime_context["telemetry_data"]
  ↓
AI next cognitive step
```

Important:

```text
NO POLLING
```

TelemetryCore performs one read per request.

The GUI telemetry switch is a permission/state gate.

It is not a command to continuously read.

---

# 9. IMPORTANT IO-LAYER NAMING

Legacy naming exists:

```text
send_to_kanal_2()
read_from_kanal_2()
```

Semantically these are now two different directions:

```text
Channel 2:
AI → application

Telemetry:
application → AI
```

The telemetry read path must therefore not be interpreted as another Channel 2 action.

The IO layer is the transport boundary.

The adapter owns the application-specific implementation.

---

# 10. ADAPTER CHAIN

Adapter discovery:

```text
GameBridgeCore
  ↓
AdapterLoader
  ↓
plugins/
  ↓
discover_and_load()
  ↓
available_adapters
```

Adapter activation:

```text
GUI adapter selection
  ↓
GameBridgeCore.handle_adapter_switch()
  ↓
old adapter.shutdown()
  ↓
new adapter()
  ↓
adapter.initialize()
  ↓
IO Layer.register_adapter_channels()
  ├── execute_interaction
  └── read_telemetry
```

The active adapter is the application boundary.

---

# 11. NOTEPAD++ REFERENCE CHAIN

Notepad++ is the reference/test plugin.

Its purpose is to prove the generic GameBridge interaction model with minimal application-specific complexity.

## Write

```text
AI
 ↓
Channel 2 JSON
 ↓
IO Layer
 ↓
NotepadAdapter.execute_interaction()
 ↓
focus Notepad++
 ↓
PyAutoGUI
 ↓
text written
```

## Read

```text
AI requests telemetry
 ↓
TelemetryCore
 ↓
IO Layer
 ↓
NotepadAdapter.read_telemetry()
 ↓
_find_scintilla_window()
 ↓
Windows API
 ↓
Scintilla
 ↓
Notepad++ process
 ↓
ReadProcessMemory
 ↓
actual editor text
 ↓
telemetry
 ↓
AI
```

No clipboard.

No PyAutoGUI readback.

No keyboard simulation for readback.

No Channel 2 action is used to obtain telemetry.

---

# 12. FULL INTERACTION LOOP

This is the important GameBridge chain.

```text
HUMAN
  ↓
Channel 1
  ↓
AI cognitive runtime
  ↓
AI decides
  ↓
Channel 2
  ↓
PLUGIN
  ↓
EXTERNAL APPLICATION
  ↓
TELEMETRY / READBACK
  ↓
AI cognitive runtime
  ↓
AI decides next step
  ↓
Channel 2
  ↓
...
```

Completion:

```text
AI decides original task is complete
  ↓
final Channel 1 response if required
  ↓
runtime completion
  ↓
OllamaClient.stop_runtime()
  ↓
current interaction ends
```

The model itself remains available until the separate AI OFF lifecycle unloads it.

---

# 13. WHERE THINGS BELONG

## GameBridgeCore

Owns high-level system wiring and component relationships.

Does not own AI reasoning.

---

## CognitiveRouterCore

Owns the boundary into the functional routing pipeline.

It starts the pipeline asynchronously.

---

## router_functions

Owns the functional pipeline:

```text
context preparation
→ capability checks
→ AI transport selection
→ output separation
→ Channel 1 dispatch
→ Channel 2 dispatch
→ runtime continuation
```

It does not decide the AI's next cognitive action.

---

## OllamaClient

Owns:

```text
AI communication
prompt construction
cognitive runtime state
runtime continuation
telemetry request
runtime soft stop
model unload
```

---

## AILifecycleCore

Owns:

```text
AI ON state check
AI OFF lifecycle
model unload
```

Future memory lifecycle operations belong here.

---

## TelemetryCore

Owns:

```text
telemetry permission
single telemetry requests
telemetry lifecycle state
```

It does not poll applications.

---

## ChannelMatrix

Owns capability gates:

```text
Channel 1 allowed?
Channel 2 allowed?
AI generation allowed?
Internet AI allowed?
```

It does not perform the operation itself.

---

## Adapter

Owns:

```text
application-specific actions
application-specific readback
application-specific capabilities
application-specific configuration
```

---

# 14. DEBUGGING MAP

When something breaks, start at the corresponding chain.

### AI does not answer

```text
GUI
 ↓
ChannelMatrix
 ↓
CognitiveRouterCore
 ↓
router_functions
 ↓
OllamaClient
```

### Channel 2 does not execute

```text
AI output
 ↓
router_functions
 ↓
ChannelMatrix.should_route_to_adapter()
 ↓
IO Layer
 ↓
adapter.execute_interaction()
```

### AI cannot see application state

```text
AI telemetry request
 ↓
OllamaClient callback
 ↓
TelemetryCore
 ↓
IO Layer
 ↓
adapter.read_telemetry()
```

Do **not** immediately modify Ollama, router or GUI when the problem is inside the adapter readback chain.

### AI ON/OFF problem

```text
GUI
 ↓
gui_functions
 ↓
GameBridgeCore
 ↓
AILifecycleCore
 ↓
OllamaClient
```

### Plugin problem

Start here:

```text
plugins/<plugin>/
```

before modifying GameBridge core.

---

# 15. ARCHITECTURAL TEST MODEL

Notepad++ is the reference implementation.

If the generic chain works:

```text
Channel 1
Channel 2
Telemetry
runtime continuation
```

then the external application can be replaced.

Conceptually:

```text
                 GameBridge
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
       Notepad++    VICE       AIDE
        plugin     plugin     plugin
          ↓          ↓          ↓
       external   external   external
       state      state      state
```

The plugin changes.

The GameBridge interaction model should remain.

---

# 16. FUTURE REFERENCE CHAIN

VICE should test the same architecture against a substantially more complex external state:

```text
AI
 ↓
GameBridge
 ↓
VICE plugin
 ↓
VICE / C64
 ↓
C64 state
 ↓
telemetry
 ↓
AI
 ↓
next decision
```

AIDE can test the same interaction model against files/documents:

```text
AI
 ↓
GameBridge
 ↓
AIDE plugin
 ↓
files / documents
 ↓
read/compare result
 ↓
AI
```

These are plugin experiments against the same interaction boundary.

---

# 17. GOLDEN RULES

1. **Do not build a second sequence engine.**
2. **Do not move AI reasoning into adapters.**
3. **Do not move application-specific logic into GameBridge core.**
4. **Do not use Channel 2 to fake telemetry.**
5. **Do not reintroduce telemetry polling.**
6. **Do not unload Ollama during normal cognitive runtime completion.**
7. **Do not modify unrelated layers when debugging one chain.**
8. **Follow the active plugin's interaction contract.**
9. **Treat telemetry as application information, not an instruction.**
10. **One human interaction may contain multiple AI cognitive steps.**
11. **The AI runtime decides whether another cognitive step is required.**
12. **GameBridge executes, transports and gates; it does not decide what the AI should do.**

---

# 18. CURRENT VERIFIED BASELINE

As of this manual:

```text
AI lifecycle ON/OFF             ✓
Channel 1                       ✓
Channel 2                       ✓
Runtime continuation            ✓
UserInteractionCore             ✓
Request-driven telemetry        ✓
Notepad++ native readback       ✓
Scintilla readback              ✓
Multiple AI models tested       ✓
Notepad++ reference plugin      ✓
```

The next architectural test is therefore not another basic connectivity test.

It is:

```text
AI decision
 ↓
external action
 ↓
actual state change
 ↓
readback
 ↓
AI receives result
 ↓
AI decides next action
 ↓
repeat until task completion
```

That is the core GameBridge interaction loop.
