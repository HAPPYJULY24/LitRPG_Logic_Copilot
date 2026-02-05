"""
Localization Module for Logic Copilot
Handles bilingual support (English/Chinese) for UI and Logic display.
"""
from decimal import Decimal

# Translation Dictionary
TRANSLATIONS = {
    "en": {
        # Valid options: "en", "zh"
        "ui_title": "LitRPG Logic Copilot",
        "ui_subtitle": "Gamified HUD Interface - Immersive Writing Experience",
        "sidebar_hud": "🛡️ HUD System",
        "tab_items": "🎒 Items",
        "tab_buffs": "✨ Buffs",
        "tab_story": "📖 Story Engine",
        "tab_settings": "🌍 World Settings",
        "label_input": "Narrative Input",
        "placeholder_input": "Example:\nLin Feng defeated the Goblin Chief, gaining 50 Gold and Iron Sword x1.\nStrength +10, Level up to 25.",
        "submit_btn": "⚡ Process Action",
        "clear_log": "🗑️ Clear Log",
        "confirm_clear_title": "⚠️ Clear all transactions?",
        "confirm_yes": "✅ Yes, Delete",
        "confirm_no": "❌ Cancel",
        "status_active": "Active",
        "wealth": "Wealth",
        "attributes": "ATTRIBUTES",
        "empty": "Empty",
        "none": "None",
        "prompt_lang_instruction": "IMPORTANT: All string values in the JSON output, especially the 'reason' and 'name' fields (if not found in schema), MUST be strictly in English.",
        "deployment_warning_title": "⚠️ Cloud Deployment Notice",
        "deployment_warning_msg": "Data is stored in temporary memory. It will be lost if the app restarts.",
        
        # API & Setup
        "key_setup": "🔑 API Key Setup",
        "key_label": "Google Gemini API Key",
        "key_help": "Get your key at aistudio.google.com",
        "btn_test_conn": "📡 Test Connection",
        "err_no_key": "❌ No API Key found.",
        "toast_conn_success": "✅ Connection Successful!",
        "err_conn_fail": "Connection Failed: {}",
        
        # Cost & Usage
        "cost_title": "💰 Cost Supervision",
        "cost_total": "Total Used",
        "cost_saved": "Saved",
        "lbl_tokens": "⚡ Tokens: {}",
        
        # Persistence
        "persist_title": "💾 Cloud Persistence",
        "tab_backup": "📥 Backup",
        "tab_restore": "📤 Restore",
        "btn_download": "Download JSON",
        "lbl_upload": "Upload Save File",
        "err_invalid_save": "❌ Invalid Save File.",
        "info_loaded": "Loaded {} events (Time: {})",
        "btn_confirm_restore": "🔴 Confirm Restore",
        "toast_restore_success": "✅ Save loaded!",
        "btn_reset": "💣 Reset All Data",
        "msg_no_events": "No events to save.",
        "caption_no_events": "No events yet.",
        
        # Manual Mode & Tutorial
        "msg_welcome": "👋 Welcome! Type a sentence like 'I found 10 gold' to start.",
        "btn_dismiss": "Dismiss Tutorial",
        "toggle_manual": "🛠️ Manual JSON Mode",
        "hdr_manual_input": "💻 Manual JSON Input",
        "btn_exec_batch": "⚡ Execute Batch",
        
        # Errors & Feedback
        "err_session_limit": "⛔ Session Request Limit Reached. Refresh page.",
        "msg_cooldown": "⏳ Cooldown: {}s",
        "err_json_list": "❌ Output must be a List `[...]`",
        "err_json_syntax": "❌ JSON Syntax Error: {}",
        "err_llm": "LLM Error: {}",
        "status_thinking": "Thinking...",
        "status_extracting": "Extracting...",
        "status_complete": "Complete!",
        "toast_auto_adapt": "🤖 Auto-Adapted: Switched to {}",
        "err_rejected": "⛔ Transaction Rejected: {}",
        "toast_formula_err": "⚠️ Formula Error: {}",
        "info_no_action": "No actionable events found.",
        
        # History
        "hdr_history": "📜 Event History",
        "lbl_search": "🔍 Search History",
        "info_no_match": "No matching events.",
        
        # World Settings
        "hdr_world_schema": "🌍 World Schema (Currency & Stats)",
        "info_current_sys": "Current System: **{}**",
        "lbl_select_preset": "Select Preset",
        "btn_apply_schema": "Apply World Schema",
        "msg_schema_switched": "Switched to {}!",
        "warn_schema_compat": "Note: Existing event log events with old currency units may cause errors. Recommended to Clear Data.",
        "exp_currency": "💰 Active Currency Rules",
        "exp_limits": "🛡️ Safety Limits",
        "lbl_max_gold": "Max Gold Cap",
        "lbl_allow_debt": "Allow Negative Debt",
        
        # Formula Engine
        "hdr_formula": "⚗️ Formula Engine",
        "desc_formula": "Define how secondary stats are calculated.",
        "info_no_formulas": "No formulas defined yet.",
        "hdr_add_formula": "##### Add/Update Formula",
        "lbl_stat_name": "Stat Name (e.g., Attack)",
        "lbl_expr": "Expression (e.g., Strength * 2)",
        "btn_save_formula": "Save Formula",
        "msg_formula_reg": "Registered: {} = {}"
    },
    "zh": {
        "ui_title": "网文逻辑副驾 (Logic Copilot)",
        "ui_subtitle": "游戏化抬头显示界面 - 沉浸式写作体验",
        "sidebar_hud": "🛡️状态面板 (HUD)",
        "tab_items": "🎒 物品栏",
        "tab_buffs": "✨ 状态/Buff",
        "tab_story": "📖 故事引擎",
        "tab_settings": "🌍 世界设定",
        "label_input": "剧情输入 (Narrative Input)",
        "placeholder_input": "示例：\n林风击败了哥布林首领，获得 50 金币和铁剑 ×1。\n力量+10，等级提升到 25 级。",
        "submit_btn": "⚡ 执行剧情 (Process)",
        "clear_log": "🗑️ 清空记录",
        "confirm_clear_title": "⚠️ 确认清空所有记录？",
        "confirm_yes": "✅ 确认删除",
        "confirm_no": "❌ 取消",
        "status_active": "运行中",
        "wealth": "财富",
        "attributes": "基础属性",
        "empty": "空",
        "none": "无",
        "prompt_lang_instruction": "IMPORTANT: All string values in the JSON output, especially the 'reason' and 'name' fields (if not found in schema), MUST be strictly in Simplified Chinese (简体中文). Do not mix English and Chinese.",
        "deployment_warning_title": "⚠️ 云端部署提示",
        "deployment_warning_msg": "数据存储在临时内存中，应用重启后将会丢失，请及时导出。",
        
        # API & Setup
        "key_setup": "🔑 API 密钥设置",
        "key_label": "Google Gemini API Key",
        "key_help": "前往 aistudio.google.com 获取密钥",
        "btn_test_conn": "📡 测试连接",
        "err_no_key": "❌ 未找到 API 密钥。",
        "toast_conn_success": "✅ 连接成功！",
        "err_conn_fail": "连接失败: {}",
        
        # Cost & Usage
        "cost_title": "💰 成本监控",
        "cost_total": "总消耗",
        "cost_saved": "已节省",
        "lbl_tokens": "⚡ Token 消耗: {}",
        
        # Persistence
        "persist_title": "💾 云端持久化",
        "tab_backup": "📥 备份 (Backup)",
        "tab_restore": "📤 恢复 (Restore)",
        "btn_download": "下载 JSON 存档",
        "lbl_upload": "上传存档文件",
        "err_invalid_save": "❌ 无效的存档文件。",
        "info_loaded": "已加载 {} 个事件 (时间: {})",
        "btn_confirm_restore": "🔴 确认恢复",
        "toast_restore_success": "✅ 存档已加载！",
        "btn_reset": "💣 重置所有数据",
        "msg_no_events": "没有可保存的事件。",
        "caption_no_events": "暂无事件。",
        
        # Manual Mode & Tutorial
        "msg_welcome": "👋 欢迎！输入一段剧情（如“获得10枚金币”）即可开始。",
        "btn_dismiss": "关闭教程",
        "toggle_manual": "🛠️ 手动 JSON 模式",
        "hdr_manual_input": "💻 手动 JSON 输入",
        "btn_exec_batch": "⚡ 执行批处理",
        
        # Errors & Feedback
        "err_session_limit": "⛔ 会话请求达到上限。请刷新页面。",
        "msg_cooldown": "⏳ 冷却中: {}秒",
        "err_json_list": "❌ 输出必须是列表 `[...]`",
        "err_json_syntax": "❌ JSON 语法错误: {}",
        "err_llm": "LLM 错误: {}",
        "status_thinking": "思考中...",
        "status_extracting": "提取中...",
        "status_complete": "完成！",
        "toast_auto_adapt": "🤖 自动适配: 已切换至 {}",
        "err_rejected": "⛔ 交易被拒绝: {}",
        "toast_formula_err": "⚠️ 公式错误: {}",
        "info_no_action": "未发现有效事件。",
        
        # History
        "hdr_history": "📜 事件历史",
        "lbl_search": "🔍 搜索历史",
        "info_no_match": "无匹配事件。",
        
        # World Settings
        "hdr_world_schema": "🌍 世界规则 (货币与属性)",
        "info_current_sys": "当前系统: **{}**",
        "lbl_select_preset": "选择预设",
        "btn_apply_schema": "应用世界规则",
        "msg_schema_switched": "已切换至 {}!",
        "warn_schema_compat": "注意: 建议清空旧数据以避免单位冲突。",
        "exp_currency": "💰 当前货币规则",
        "exp_limits": "🛡️ 安全限制",
        "lbl_max_gold": "金币上限",
        "lbl_allow_debt": "允许负债",
        
        # Formula Engine
        "hdr_formula": "⚗️ 公式引擎",
        "desc_formula": "定义二级属性的计算方式。",
        "info_no_formulas": "暂无定义公式。",
        "hdr_add_formula": "##### 添加/更新公式",
        "lbl_stat_name": "属性名 (如: Attack)",
        "lbl_expr": "表达式 (如: Strength * 2)",
        "btn_save_formula": "保存公式",
        "msg_formula_reg": "已注册: {} = {}"
    }
}

# Stat Name Mapping (Canonical -> Display)
# Only commonly used standard RPG stats are mapped. 
# Custom user stats will be displayed as-is (Title Case).
STAT_MAPPINGS = {
    "zh": {
        "HP": "生命值",
        "HEALTH": "生命值",
        "LIFE": "生命值",
        "MP": "法力值",
        "MANA": "法力值",
        "MAGIC": "魔法值",
        "SP": "体力值",
        "STAMINA": "耐力",
        "ENERGY": "能量",
        "XP": "经验值",
        "EXPERIENCE": "经验值",
        "LEVEL": "等级",
        "STR": "力量",
        "STRENGTH": "力量",
        "AGI": "敏捷",
        "AGILITY": "敏捷",
        "DEX": "灵巧",
        "DEXTERITY": "灵巧",
        "INT": "智力",
        "INTELLIGENCE": "智力",
        "WIS": "感知",
        "WISDOM": "感知",
        "CHA": "魅力",
        "CHARISMA": "魅力",
        "LUCK": "幸运",
        "SANITY": "理智",
        "DEFENSE": "防御",
        "ATTACK": "攻击",
        "SPEED": "速度"
    }
}

def get_text(key: str, lang: str = "zh") -> str:
    """Retrieve UI text for the specific language."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["zh"]).get(key, key)

def get_display_name(key: str, lang: str = "zh") -> str:
    """
    Map canonical stat keys (e.g. 'HP') to display names (e.g. '生命值').
    If no mapping exists, return the key as-is (capitalized).
    """
    if lang == "zh":
        upper_key = key.upper()
        return STAT_MAPPINGS["zh"].get(upper_key, key)
    return key

def localize_number(value, lang: str = "zh") -> str:
    """
    Format large numbers for Chinese context (e.g. 10000 -> 1万).
    For English, uses standard K/M/B suffixes.
    """
    try:
        num = float(value)
    except:
        return str(value)

    if lang == "zh":
        if num >= 100_000_000: # 亿
            return f"{num/100_000_000:.2f}亿".replace(".00", "")
        elif num >= 10_000: # 万
            return f"{num/10_000:.2f}万".replace(".00", "")
        return f"{num:.2f}".replace(".00", "")
    else:
        # Standard English Formatting
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.2f}B".replace(".00", "")
        elif num >= 1_000_000:
            return f"{num/1_000_000:.2f}M".replace(".00", "")
        elif num >= 1_000:
            return f"{num/1_000:.2f}K".replace(".00", "")
        return f"{num:.2f}".replace(".00", "")
