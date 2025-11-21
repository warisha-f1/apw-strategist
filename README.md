Autonomous Pit Wall (apw) F1 Strategist:

1. Overview:
This multi-agent AI system provides optimal, data-driven pit stop and race strategy advice for a Formula 1 team. It is built to fulfill all Capstone requirements for multi-agent architecture, custom tool integration, and advanced memory/context management.



2. Core Multi-Agent Features:
| Requirement | Implementation | Why It Matters |
| :--- | :--- | :--- |
| **Multi-Agent System** | **Sequential** (Intent $\rightarrow$ Simulation) and **Loop Agents** (Optimization). | Separates complex tasks for speed and reliability. |
| **Custom Tool Use** | **`calculate_race_delta`** tool. | Prevents the LLM from hallucinating numbers; guarantees deterministic, accurate race simulations. |
| **A2A Protocol** | **`A2AMessage`** (Pydantic-validated). | Enforces a strict, reliable communication format between all agents. |
| **Long-Term Memory** | SQLite database with **Context Compaction**. | Stores all past decisions and dynamically informs new strategy advice. |
| **Agent Evaluation** | **`tests/test_evaluation.py`** suite (Mocking). | Verifies the functional correctness of the Custom Tool and Intent Classifier. |



3. System Architecture:
The project is structured around the following agents and modules:

Intent Agent (intent_agent.py): The first agent in the sequence. It classifies the user's input into one of four intents: NEW_STRATEGY, OPTIMIZE_STRATEGY, DELETE_ENTRY, or REVIEW_HISTORY.

Dispatcher (main.py): Reads the intent and routes the task to the appropriate downstream agent.

Simulation Agent (part of main.py): The core LLM-powered agent for NEW_STRATEGY. It uses the Custom Tool (tools/simulation_tool.py) to generate a delta and save the result to memory.

Loop Agent (decision_loop_agent.py): Activated by OPTIMIZE_STRATEGY. It runs an iterative loop that calls the Custom Tool multiple times to find the single best pit lap.

Memory Agent (part of database.py): Handles all persistence operations (save, retrieve, delete) based on messages received via the A2A Protocol.



4. Execution Summary:
Key Agent Flow:
i. Intent Agent classifies the user's request (NEW_STRATEGY, OPTIMIZE_STRATEGY).
ii. Dispatcher routes the request.
iii. Loop Agent runs the run optimization command, iterating through pit laps (15-30) to find the single best delta.

Key Commands:
1. Command:- python main.py
   Action:- Start the system.

2. Command:- What lap should I pit on?	
   Action:- Runs a single strategy simulation.

3. Command:- run optimization
   Action:- Activates the Loop Agent to find the absolute best pit lap.

4. Command:- history
   Action:- Recalls strategies from Long-Term Memory.

5. Command:- delete <ID>
   Action:- Removes a specific entry from Long-Term Memory (e.g., delete 5).



5. Agent Evaluation:
The system's integrity is verified via (python -m unittest discover tests).

EXAMPLE:
1. Single Strategy Check (Tests LLM and Custom Tool):
Use this command to verify the Intent Agent correctly identifies a NEW_STRATEGY and the Simulation Agent successfully calls the Custom Tool once for a deterministic calculation.

Command to use: "If our current tire life is good, what is the time gain or loss of pitting on lap 25 for a new set of Hard tires?"

2. Full Optimization Check (Tests Loop Agent):
This is the most complex test. It verifies the Intent Agent classifies OPTIMIZE_STRATEGY and triggers the Loop Agent to run an iterative loop that calls the Custom Tool multiple times (e.g., Laps 15-35) to find the single best pit lap.

Command to use: "Run a full optimization search to find the best possible pit stop lap using the Medium tires."

3. Memory & Context Check (Tests Context Compaction):
This question ensures the system can correctly retrieve the results from the previous two runs (which are saved in Long-Term Memory) and use them to inform a new, final decision, proving your Context Compaction works.

Command to use: "Review my last two strategy attempts and tell me which strategy type (single pit stop or the optimized one) is currently showing the best time gain."