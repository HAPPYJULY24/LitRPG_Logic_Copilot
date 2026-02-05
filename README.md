# LitRPG Logic Copilot

**Logic Copilot** is an AI-powered game logic engine for LitRPG authors. It acts as a "Dungeon Master" sidebar, automatically tracking your character's stats, inventory, gold, and buffs as you write your story.

![Status](https://img.shields.io/badge/Status-Production_Ready-green)
![Version](https://img.shields.io/badge/Version-V1.0-blue)

## 🚀 Features

- **🎮 Immersive HUD**: A game-like interface that sits alongside your writing.
- **🧠 AI Extraction**: Automatically parses "I found 50 gold" -> `Gold +50`.
- **⚡ Reactive Stats**: `Attack = Strength * 2`. Change Strength, Attack updates instantly.
- **📜 Event Sourcing**: Complete history of every action. Retcon mistakes easily.
- **🛡️ Secure Logic**: Atomic transactions prevent negative gold or broken states.

## 📚 Documentation

- **[User Guide](docs/USER_GUIDE.md)**: For authors. How to use the tool.
- **[Developer Handbook](docs/DEVELOPER_HANDBOOK.md)**: For contributors. Architecture, code overview, and setup.
- **[World Schema Guide](docs/WORLD_SCHEMA_GUIDE.md)**: How to configure custom currencies and stats.

## 🛠️ Quick Start (Developers)

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Set API Key (BYOK)**:
   - **Option A (GUI)**: Start the app and enter your key in the Sidebar.
   - **Option B (Env)**: Create a `.env` file:
     ```ini
     GOOGLE_API_KEY=your_gemini_key
     ```
3. **Run App**:
   ```bash
   streamlit run app.py
   ```

---
*Created for the 2026 Advanced Agentic Coding Project*
