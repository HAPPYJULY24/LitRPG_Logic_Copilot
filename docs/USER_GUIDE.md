# Logic Copilot User Guide (V1.0 Official)

## 🚀 Getting Started

1.  **Launch**: Run `streamlit run app.py` in your terminal.
2.  **API Key Setup**: Enter your Google Gemini API Key in the sidebar (or use `.env` file).
3.  **Language**: Click the radio button in the sidebar (🇺🇸 / 🇨🇳) to select your preferred language.
4.  **Appreciation**: The sidebar shows your current stats, gold, and inventory.

## ✍️ Story Mode (Automatic)
This is the main way to use Logic Copilot.

1.  **Write**: Type your story snippet in the main text box.
    > *Example*: "After defeating the wolf, I found a **Spirit Gem** and gained **500 XP**. I also bought a **Potion** for 5 silver."
2.  **Submit**: Click **Process Action** (or `CRTL+ENTER`).
3.  **Review**: The system will show a feedback log of what changed.
    - ✅ Gained 500 XP
    - ➕ Added "Spirit Gem"
    - ➖ Removed 50 Silver (auto-converted to Copper if needed)
    - ➕ Added "Potion"

## 🛠️ Manual Mode (Offline/Debug)
If you want to manually edit data or if you are offline:

1.  Toggle **"🛠️ Manual JSON Mode"** above the text box.
2.  Enter raw JSON commands:
    ```json
    [
      {"action": "gain", "type": "gold", "value": 100, "unit": "GP"},
      {"action": "set", "type": "stat", "name": "Strength", "value": 15}
    ]
    ```
3.  Click **Execute Batch**.

## 💾 Saving & Loading
> **⚠️ DEMO MODE WARNING**: Logic Copilot runs by default in "Memory-Only Mode". **Refreshing the page will wipe your data.** You MUST manually export your save if you wish to keep it.

**Backup / Transfer**:
1.  Go to Sidebar -> **Cloud Persistence**.
2.  **Backup**: Click "Download JSON" to save your character to your computer.
3.  **Restore**: Upload a `.json` file and click "Confirm Restore" to load a previous state.

**Reset**:
- Click **"💣 Reset All Data"** in the sidebar to delete everything and start fresh.

## 📊 Cost Supervision
The sidebar displays a **Cost** tracker.
- **Total Used**: Estimated cost of LLM tokens in USD.
- **Tokens**: Total input/output tokens consumed.
