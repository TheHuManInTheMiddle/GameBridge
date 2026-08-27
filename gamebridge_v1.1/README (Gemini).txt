# G.A.M.E. B.R.I.D.G.E.

**G**eneralized **A**synchronous **M**odular **E**xtension  
**B**idirectional **R**untime **I**nteraction **D**ialogue **G**uidance **E**nvironment

---

## 🧭 The Core Philosophy: Built by the Contract

While the technical implementation of this system is heavily documented in the accompanying manuals, the code itself cannot be understood without its foundation: **The Human-AI Collaboration Contract (v3.0)**. 

This project was not built using traditional, unconstrained development. It was engineered under a rigid behavioral and architectural treaty designed to solve the cognitive friction of human-agent collaboration. The source code acts as a direct, physical manifestation of that contract.

---

## 🧠 How the Collaboration Contract Shape-Shifted the Code

The contract dictates that the platform must remain a completely decoupled, generalized central hub. Every single architectural boundary in the repository was forced into existence by the following contractual pillars:

### 1. Enforcing Strict Sphere Isolation (The 4-Sphere Rule)
To prevent the agent from writing hardcoded biases or messy dependencies, Section 1.1 of the contract legally bound the system to four completely non-overlapping domains. In the codebase, this is structurally guaranteed:
* **The Bridge (The Core Hub):** Completely blind to application-specific states. It strictly owns the active session, state tracking, and UI loop.
* **The Adapter (The Translator):** Operates on an **Anonymized Target System** principle (tested via Notepad++ as "Target X"). The adapter's *only* contractual right is to scrub raw external data into standard JSON dictionaries that the Bridge can safely digest.
* **The Target App:** The external system being manipulated, kept completely external to the application binary.
* **The Cognitive Model (Theia):** Consumes context via generalized API infrastructure, acting as a modular passenger that can be hot-swapped without altering a single core file.

┌────────────────────────────────────────┐+-------------------------------------------------------------------------+

|                        UIEventQueue (Main Thread)                       |
+-----------------------------------▲-------------------------------------+
                                    | dispatch()
+-----------------------------------+-------------------------------------+

|                        G.A.M.E. B.R.I.D.G.E. Core                       |
|     - Enforces ChannelMatrix            - Manages Session State         |
+─────────────┬────────────────────────────────────────────┬──────────────+

              |                                            |
              | Channel 2: Interaction                     | Channel 1: Conversation
              ▼                                            ▼
+---------------------------+                +----------------------------+

|     Modular Adapters      |                |    Human Operator (PTT)    |
|  - Translates to JSON     |                |  - Asynchronous Chat Flow  |
|  - PyAutoGUI / Hw Targets |                |  - Hardware Hook Controls  |
+─────────────┬─────────────+                +----------------------------+
              |
              ▼
+---------------------------+

|    Target (Notepad++)     |
+---------------------------+
│### 2. Operationalizing Dual Parallel Flows (Channel 1 & Channel 2)
The contract strictly dictates that **human conversation must never block system execution**. If the AI is executing a continuous interaction loop, the operator must still be able to text or talk to it concurrently. 
* **The Code Solution:** This requirement forced the creation of our heavily multi-threaded core. `process_chatt_flow` runs on a completely separate background daemon thread, while a discrete telemetry loop feeds runtime events continuously without ever causing the CustomTkinter UI to stutter or freeze.

### 3. Mitigating "The Blank Page" via Sketched Proofs
Section 1.0 of the contract highlights a human cognitive bottleneck: the tendency to stall when faced with an empty workspace. The contract demands structural outlines and concrete code skeletons to react to, rather than abstract questions.
* **The Code Solution:** Every module implements an explicit **Embedded Connection Map** (`KOPPLINGAR:`) right inside the top header comments. By forcing the system to declare its exact `HÄMTAR FRÅN:` (Imports From) and `ANROPAS AV:` (Invoked By) structural maps, the contract removed assumptions and ensured that every new feature fits perfectly into the existing interface hierarchy.

### 4. Human-in-the-Loop Escalation & Operational Freedom
The contract demands that the user must maintain total freedom to use their machine normally while an automated routine runs, with the ability for the AI to gracefully hand over control when human intervention (such as specific mouse control) is needed.
* **The Code Solution:** This led to our robust **Keyboard Focus Lock** and the `HardwareIO` layer. When the operator triggers a physical lock, the background loops listen seamlessly without locking the underlying OS thread, letting the system drop into a safe, passive telemetry mode instantly.

---

## 🔧 Critical Transactional Fixes

The rigid verification chain dictated by the contract (*Isolate Core Logic → Reproduce → Test → Verify*) allowed us to capture and surgically resolve high-impact runtime anomalies:
* **The Unhashable Type Widget Fix:** The strict initialization checklist forced us to squash Tkinter's native unhashable list errors on startup by strictly binding scalar indices to the SegmentedButton elements before rendering.
* **Safe Push-To-Talk Iteration:** To satisfy the contract's strict memory stability clauses, the audio core was rewritten from dangerous recursive stream triggers into a flat, loop-managed state machine. This entirely eliminated stack overflow vectors during erratic human-to-machine toggle behavior.

---

## 🚀 Technical Architecture Overview

Full parameters, function maps, and usage schemes are available in the system manual.
* **Runtime Environment:** Python 3.10+ (Engineered primarily for Windows environment hooks).
* **Interface Layer:** CustomTkinter (`ctk`) leveraging a thread-safe `UIEventQueue` callback pattern.
* **I/O Engine:** `pyautogui` automation layers protected by a mandatory hardware `FAILSAFE = True` protocol, and native `keyboard` hook monitors.
* **Kognitive Bridge:** General HTTP network providers utilizing Python's native `urllib.request` pipelines to ensure zero heavy external package dependencies.

---

## 📦 Getting Started

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com
   cd game-bridge
   ```
2. Install the core hardware and interface packages:
   ```bash
   pip install customtkinter pyautogui keyboard
   ```
3. Establish your secure local configuration file (`.env`) in the root directory:
   ```env
   TAVILY_API_KEY=tvly-YOUR_KEY_HERE
   ```

### Execution
Launch the primary initialization target to fire up the environment hub:
```bash
python main/main.py
```