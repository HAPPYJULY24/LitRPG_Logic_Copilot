# Logic Copilot POC V1.0 - System Overview

## 1. Introduction
**Logic Copilot** is a bilingual (English/Chinese) AI-assisted writing tool designed for LitRPG and Xianxia authors. It acts as an intelligent "Game Master" that reads your narrative text and automatically manages the tedious numerical logistics of your story—tracking gold, inventory, stats, and buffs in real-time.

### Core Philosophy
- **Narrative First**: You write the story; the system handles the math.
- **Event Sourcing**: Every change is stored as an immutable event. State is derived, not stored.
- **Bilingual Native**: Full support for English and Chinese UIs and number formatting (e.g., "1000" vs "1k" vs "10亿").

---

## 2. Key Features (POC V1.0)

### 🌍 Bilingual Support (New!)
- **Language Switcher**: Toggle instantly between English (🇺🇸) and Simplified Chinese (🇨🇳).
- **Localized Formatting**:
  - English: `10,000` or `10k`
  - Chinese: `1万` or `1亿` (Wan/Yi support for large numbers)
- **Smart Prompting**: The AI automatically adjusts its extraction logic based on the selected UI language.

### 🧠 Intelligent Extraction
- **LLM-Powered**: Uses Google Gemini to understand complex narrative causality.
  - *Input*: "I bought the sword for 500 gold and gained 10 strength."
  - *Output*: `{-500 Gold, +1 Sword, +10 STR}`
- **Fuzzy Matching**: Matches "Iron Sword" to existing "Rusty Iron Sword" in inventory based on context.

### 🛡️ Resilience & Security
- **Atomic Batches**: Transactions are processed in "All-or-Nothing" batches. If one logic rule fails (e.g., negative gold), the entire batch rolls back.
- **Cost Supervision**: Real-time dashboard of Token usage and estimated USD cost.
- **Cloud Persistence**: 
  - **Auto-Save**: Atomic writes protect against crashes.
  - **Backup/Restore**: Download your state as JSON or restore from a file.

### ⚙️ Customizable World Logic
- **World Schemas**: Switch between different economies:
  - **Classic Fantasy**: Gold/Silver/Copper (1 GP = 100 CP)
  - **Xianxia**: Spirit Stones (Low/Mid/High)
  - **Sci-Fi**: Credits (Decimal)
- **Formula Engine**: Define custom stats like `Attack Power = Strength * 2 + Agility`.

---

## 3. System Architecture

### The Logic Core (`logic/`)
The system is built on a strict **Event Sourcing** architecture.

1.  **`LedgerEngine`**: The brain. It holds a list of immutable `Events`. To get the current "Character Sheet", it replays all events from the beginning (`reduce()` function).
2.  **`LLMExtractor`**: The eyes. It converts unstructured text into structured JSON transactions.
3.  **`UnitRegistry`**: The calculator. Handles currency conversion and display formatting.
4.  **`UsageTracker`**: The accountant. Tracks API costs.

### Data Flow
1.  **User Input** -> **LLM Extractor** -> **JSON Transactions**
2.  **JSON Transactions** -> **LedgerEngine** (Validation)
3.  **LedgerEngine** -> **Event Log** (Append)
4.  **Event Log** -> **State Replay** -> **UI Render**

---

## 4. Folder Structure (Cleaned)
```
d:/personal/Logic Copilot/
├── app.py                 # Main Entry Point (Streamlit)
├── ui_components.py       # UI Rendering Logic
├── logic/                 # Core Logic Modules
│   ├── ledger_engine.py   # Event Sourcing Engine
│   ├── llm_extractor.py   # AI Interface
│   ├── localization.py    # Translation Data
│   └── ...
├── saves/                 # User Data (JSON)
└── docs/                  # This Documentation
```
