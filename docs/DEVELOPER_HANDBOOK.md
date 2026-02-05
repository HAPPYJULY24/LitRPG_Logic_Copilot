# Developer Handbook (V1.0 Official)

## 🏗️ Architecture: Event Sourcing
Logic Copilot does not store the "State" (e.g., "Current Gold: 100"). Instead, it stores the **History**:
1.  Start: 0
2.  Event 1: +50 Gold
3.  Event 2: -10 Gold
4.  **Current State (Derived)**: 40 Gold.
    > **Note**: In Demo Mode (V1.0), this history is stored in session memory only.

### Why?
- **Audit Trail**: We can explain *exactly* how the player got here.
- **Undo/Rollback**: Trivial to implement (just remove the last event).
- **Resilience**: If calculations change (e.g., Gold value changes), replaying events updates the state automatically.

## 📂 Key Modules

### 1. `logic/ledger_engine.py`
- **`process_batch(transactions)`**: Main entry point.
- **`reduce(events)`**: Replays history to calculate state.
- **`_auto_save()`**: Atomic write implementation.

### 2. `logic/llm_extractor.py`
- Handles communication with Google Gemini.
- **`extract_transactions(text, language)`**:
  - Injects system prompt based on `language` ('en'/'zh').
  - Returns raw JSON.

### 3. `logic/localization.py` (New in V1.7)
- **`get_text(key, lang)`**: Returns UI strings.
- **`localize_number(value, lang)`**:
  - `en`: 1.5M, 10k
  - `zh`: 150万, 1亿

## 🧪 Testing
We use a mix of unit tests and integration scripts.
- **`tests/`**: Contains formal Unit Tests.
- **Integration**:
  - Run `python tests/integration_test_bilingual.py` to test the full pipeline (Text -> LLM -> Ledger) without the UI.

## 🔄 Extension Guide

### Adding a New Language
1.  Open `logic/localization.py`.
2.  Add a new key to the `TRANSLATIONS` dict (e.g., `"jp"`).
3.  Update `app.py` line 90 (`lang_options`) to include the new language.

### Adding a Custom Stat
1.  Open `saves/world_config.json` (or edit via UI).
2.  Add a formula: `"Mana = Intelligence * 10"`.
3.  The `FormulaEngine` will automatically compute this during `reduce()`.
