"""
UI Components Library - V1.2 Gamified HUD
Restored after corruption.

Components:
- apply_custom_css(): Injects CSS for RPG aesthetics
- render_sidebar_stats(): Character Sheet (Tabs)
- render_transaction_feedback(): Visual log of actions
- render_world_settings(): Configuration panel
- render_formula_panel(): Stats definition panel
"""
import streamlit as st
import time
from decimal import Decimal
from typing import Dict, List, Any
from logic.world_schema import WorldSchema
from logic.unit_registry import UnitRegistry

from logic.localization import get_text, get_display_name, localize_number

def apply_custom_css():
    """Injects game-style CSS"""
    st.markdown("""
    <style>
        /* Global Font & Dark Mode Adjustments */
        .stApp {
            background-color: #0e1117;
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #1a1c24;
            border-right: 1px solid #2d3436;
        }
        
        /* Stat Cards */
        .stat-metric {
            background-color: #262730;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #3d3d3d;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .stat-title { color: #b0bec5; font-size: 0.8rem; text-transform: uppercase; }
        .stat-val { color: #fff; font-size: 1.1rem; font-weight: bold; }
        
        /* Visual Gauges */
        .gauge-container {
            margin-bottom: 12px;
            background: #2d3436;
            border-radius: 4px;
            padding: 4px;
            box-shadow: inset 0 0 5px rgba(0,0,0,0.5);
        }
        .gauge-label {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: #ddd;
            margin-bottom: 2px;
            padding: 0 4px;
        }
        .gauge-bar-bg {
            height: 8px;
            background: #444;
            border-radius: 4px;
            overflow: hidden;
            width: 100%;
        }
        .gauge-bar-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease-in-out;
            box-shadow: 0 0 8px currentColor;
        }
        .pulse-red { animation: pulse-red 1.5s infinite; }
        @keyframes pulse-red {
            0% { box-shadow: 0 0 0 0 rgba(229, 80, 57, 0.7); }
            70% { box-shadow: 0 0 0 6px rgba(229, 80, 57, 0); }
            100% { box-shadow: 0 0 0 0 rgba(229, 80, 57, 0); }
        }
        
        /* Button Glow */
        div.stButton > button[kind="primary"] {
            border: 1px solid #6c5ce7;
            box-shadow: 0 0 10px rgba(108, 92, 231, 0.5);
            transition: all 0.3s ease;
        }
        div.stButton > button[kind="primary"]:hover {
            box-shadow: 0 0 20px rgba(108, 92, 231, 0.8);
            transform: scale(1.02);
        }

        /* Tooltips/Help */
        .tooltip {
            position: relative;
            display: inline-block;
            border-bottom: 1px dotted white;
        }
    </style>
    """, unsafe_allow_html=True)

def _render_gauge(label, value, color="#4CAF50", max_value=None, is_negative=False):
    """
    Renders a colorful progress bar. 
    If max_value is None, defaults to 100% fill but shows value text.
    """
    percentage = 100
    if max_value and max_value > 0:
        try:
            percentage = max(0, min(100, (float(value) / float(max_value)) * 100))
        except:
            percentage = 100
            
    val_display = f"{value}"
    if max_value:
        val_display += f" / {max_value}"
        
    pulse_class = "pulse-red" if (is_negative or (max_value and percentage < 20)) else ""
    alert_icon = "🚨" if is_negative else ""
    
    st.markdown(f"""
    <div class="gauge-container {pulse_class}">
        <div class="gauge-label">
            <span>{label} {alert_icon}</span>
            <span>{val_display}</span>
        </div>
        <div class="gauge-bar-bg">
            <div class="gauge-bar-fill" style="width: {percentage}%; background-color: {color}; color: {color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar_stats(state: Dict, unit_registry: Any, events_count: int = 0, lang: str = "zh"):
    """
    Renders the HUD.
    """
    st.sidebar.title(get_text("sidebar_hud", lang))
    
    # 0. Session Overview
    col_s1, col_s2 = st.sidebar.columns(2)
    col_s1.metric("Events", events_count)
    
    col_s2.metric("Status", get_text("status_active", lang), delta_color="normal")
    
    st.sidebar.divider()
    
    # 1. Primary Gauges (HP/MP/Energy)
    # Detect stats named "HP", "Health", "MP", "Mana", "XP"
    # Merge base + computed
    all_stats = {**state.get("stats", {}), **state.get("computed_stats", {})}
    
    # Define Gauge Configs
    gauge_defs = [
        {"keys": ["HP", "HEALTH", "LIFE"], "color": "#e55039", "max_key": "MAXHP"},
        {"keys": ["MP", "MANA", "MAGIC"], "color": "#0984e3", "max_key": "MAXMP"},
        {"keys": ["SP", "STAMINA", "ENERGY"], "color": "#f6b93b", "max_key": "MAXSP"},
        {"keys": ["XP", "EXPERIENCE"], "color": "#6c5ce7", "max_key": "NEXTLEVELXP"}
    ]
    
    # Process Gauges
    processed_keys = set()
    
    for gauge in gauge_defs:
        found_key = None
        for k in all_stats.keys():
            if k.upper() in gauge["keys"]:
                found_key = k
                break
        
        if found_key:
            val = all_stats[found_key]
            # Try to find max
            max_val = None
            max_key_candidate = gauge.get("max_key") # Only default provided, user might not have set it
            
            # Smart check for MaxXYZ stat
            for k in all_stats.keys():
                if k.upper() == f"MAX{found_key.upper()}": 
                    max_val = all_stats[k]
                    processed_keys.add(k)
                    break
            
            is_neg = isinstance(val, (int, float, Decimal)) and val < 0
            
            # Display Name Mapping (Key Map Trap Safeguard)
            display_label = get_display_name(found_key, lang)
            
            _render_gauge(display_label, val, color=gauge["color"], max_value=max_val, is_negative=is_neg)
            processed_keys.add(found_key)

    st.sidebar.divider()
    
    # 2. Key Attributes (Remainder)
    st.sidebar.caption(get_text("attributes", lang))
    
    # Currency
    gold_cp = state.get("gold_cp", Decimal("0"))
    # localized number if requested, but unit registry usually handles formatting? 
    # UnitRegistry handles suffix (unit), but not '10亿'. 
    # Let's keep unit_registry format for consistency with units, or augment it?
    # For now, let's trust unit_registry.format_display but maybe wrapping the number part could be complex.
    # Let's just translate the Label "Wealth".
    formatted_gold = unit_registry.format_display(gold_cp)
    st.sidebar.metric(get_text("wealth", lang), formatted_gold)
    
    # Other Stats
    leftover_stats = {k:v for k,v in all_stats.items() if k not in processed_keys}
    if leftover_stats:
        cols = st.sidebar.columns(2)
        idx = 0
        for k, v in leftover_stats.items():
            str_v = str(v)
            display_k = get_display_name(k, lang)
            if "TBD" in str_v:
                cols[idx%2].warning(f"{display_k}: {v}") # Highlight TBD
            else:
                cols[idx%2].metric(display_k, str_v)
            idx += 1
            
    # 3. Inventory & Buffs (Tabs)
    st.sidebar.divider()
    tab_inv, tab_buff = st.sidebar.tabs([get_text("tab_items", lang), get_text("tab_buffs", lang)])
    
    with tab_inv:
        inv = state.get("inventory", {})
        if not inv:
            st.caption(get_text("empty", lang))
        else:
            for k, v in inv.items():
                if v > 0:
                    st.markdown(f"**{k}** <span style='float:right'>x{v}</span>", unsafe_allow_html=True)

    with tab_buff:
        buffs = state.get("buffs", [])
        if not buffs:
            st.caption(get_text("none", lang))
        else:
            for b in buffs:
                st.info(f"✨ {b}")


def render_transaction_feedback(transactions: List[Dict], unit_registry: Any, lang: str = "zh"):
    """
    Renders the "Success" message and detailed log of actions.
    """
    if not transactions:
        return

    st.subheader("📜 Action Log")
    
    for tx in transactions:
        action = tx.get('action')
        type_ = tx.get('type')
        value = tx.get('value')
        name = tx.get('name')
        unit = tx.get('unit')
        reason = tx.get('reason', '')
        
        # Color coding
        box_style = "border-left: 5px solid #00b894;" # Default Success Green
        icon = "📝"
        message = ""
        
        if type_ == "gold":
            icon = "💰"
            # Localize numbers for very large gold values? 
            # Ideally yes, but 'value' here is a string from JSON.
            if action == "gain":
                message = f"Gained **{value} {unit}**" if lang == "en" else f"获得 **{value} {unit}**"
            else:
                message = f"Lost **{value} {unit}**" if lang == "en" else f"失去 **{value} {unit}**"
                box_style = "border-left: 5px solid #e17055;" # Red for loss
                
        elif type_ == "stat":
            icon = "📊"
            box_style = "border-left: 5px solid #0984e3;" # Blue
            display_name = get_display_name(name, lang)
            message = f"{action.title()} **{display_name}** by {value}" if lang == "en" else f"**{display_name}** {action} {value}"
            
        elif type_ == "item":
            icon = "🎒"
            box_style = "border-left: 5px solid #6c5ce7;" # Purple
            qty = tx.get('quantity', 1)
            # Inventory items are NOT translated (Fuzzy Match Policy)
            message = f"{action.title()} **{qty}x {name}**" if lang == "en" else f"{action} **{name} ×{qty}**"
            
        elif type_ == "buff":
            icon = "✨"
            box_style = "border-left: 5px solid #fdcb6e;" # Yellow
            message = f"Applied Buff: **{name}**" if lang == "en" else f"获得状态: **{name}**"
            
        st.markdown(f"""
        <div class="transaction-box" style="{box_style}">
            <div style="font-size: 1.1em;">{icon} {message}</div>
            <div style="font-size: 0.8em; color: #aaa; margin-top: 4px;">{reason}</div>
        </div>
        """, unsafe_allow_html=True)

def render_world_settings(ledger: Any, lang: str = "zh"):
    """
    Renders the World Schema configuration panel.
    """
    st.subheader(get_text("hdr_world_schema", lang))
    
    # 1. Preset Selector
    current_name = ledger.unit_registry.schema.currency_name
    st.info(get_text("info_current_sys", lang).format(current_name))
    
    presets = {
        "Classic Fantasy (GP/SP/CP)": "classic_fantasy",
        "Modern System (USD $)": "modern",
        "Sci-Fi (Credits)": "scifi_credits",
        "Xianxia (Power)": "xianxia", 
        "Time (Years/Days)": "time_based"
    }
    
    selected_preset = st.selectbox(get_text("lbl_select_preset", lang), list(presets.keys()))
    
    if st.button(get_text("btn_apply_schema", lang), type="primary"):
        # Load new schema
        method_name = presets[selected_preset]
        new_schema = getattr(WorldSchema, method_name)()
        
        # Apply to Ledger
        ledger.unit_registry = UnitRegistry(new_schema)
        
        # Persist
        save_path = getattr(ledger, 'world_schema_path', "saves/world_config.json")
        new_schema.save_to_file(save_path)
        
        st.success(get_text("msg_schema_switched", lang).format(selected_preset))
        st.warning(get_text("warn_schema_compat", lang))
        time.sleep(1)
        st.rerun()

    # 2. Currency Details (Read-only view of active schema)
    with st.expander(get_text("exp_currency", lang), expanded=True):
        schema = ledger.unit_registry.schema
        st.write(f"**Base Unit**: {schema.base_unit}")
        st.write("**Conversions:**")
        
        # Format conversions nicely
        for unit, rate in schema.conversions.items():
            if unit != schema.base_unit:
                st.write(f"- 1 {unit} = {rate} {schema.base_unit}")
    
    # 3. Limits
    with st.expander(get_text("exp_limits", lang)):
        max_gold = st.number_input(get_text("lbl_max_gold", lang), value=1_000_000_000, disabled=True)
        st.toggle(get_text("lbl_allow_debt", lang), value=False, disabled=True)


def render_formula_panel(ledger: Any, lang: str = "zh"):
    """
    Renders the Formula Engine configuration interactively.
    """
    st.subheader(get_text("hdr_formula", lang))
    st.markdown(get_text("desc_formula", lang))
    
    # Display existing formulas
    formulas = ledger.formula_engine.formulas
    
    if not formulas:
        st.info(get_text("info_no_formulas", lang))
    else:
        for stat, expression in formulas.items():
            col1, col2 = st.columns([1, 3])
            col1.markdown(f"**{stat}** =")
            col2.code(expression, language="python")
            
    # Add new formula
    with st.form("add_formula"):
        st.markdown(get_text("hdr_add_formula", lang))
        col1, col2 = st.columns(2)
        with col1:
            new_stat = st.text_input(get_text("lbl_stat_name", lang))
        with col2:
            new_expr = st.text_input(get_text("lbl_expr", lang))
            
        if st.form_submit_button(get_text("btn_save_formula", lang)):
            if new_stat and new_expr:
                try:
                    ledger.formula_engine.register_formula(new_stat, new_expr)
                    st.success(get_text("msg_formula_reg", lang).format(new_stat, new_expr))
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
