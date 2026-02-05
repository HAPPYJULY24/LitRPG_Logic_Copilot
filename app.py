"""
Logic Copilot V1.7 - Bilingual & Hardened
- V1.7: Added Internationalization (i18n) & Manual Mode
- V1.6: Compact Event Log & Search
- V1.5: Draft Mode & Cloud Persistence
- V1.2: Gamified HUD
"""
import streamlit as st
import ui_components as ui
from logic.ledger_engine import LedgerEngine
from logic.llm_extractor import LLMExtractor
from logic.usage_tracker import UsageTracker
from logic.localization import get_text
from typing import Tuple, List, Dict
import hashlib
import time
import inspect
import importlib
import logic.llm_extractor

# HOT RELOAD FIX: Ensure LLMExtractor is up to date
importlib.reload(logic.llm_extractor)
from logic.llm_extractor import LLMExtractor

# STALE OBJECT DETECTION
# If the existing extractor in session_state is from an old class definition (missing 'language' param),
# we must clear it to force re-initialization.
if 'extractor' in st.session_state:
    try:
        sig = inspect.signature(st.session_state.extractor.extract_transactions)
        if 'language' not in sig.parameters:
            print("🔄 Detected stale LLMExtractor. Reloading...")
            del st.session_state['extractor']
    except Exception:
        pass

# ==========================================
# 0. Language State (Bilingual)
# ==========================================
# 0.5 API Key Injection (BYOK) - MUST be before LLMExtractor init
if "user_api_key" in st.session_state and st.session_state.user_api_key:
    import os
    os.environ["GOOGLE_API_KEY"] = st.session_state.user_api_key

if 'language' not in st.session_state:
    st.session_state.language = "zh"

# Helper for Caching
@st.cache_data(show_spinner=False)
def _get_cached_extraction(text: str, schema_signature: str, _extractor, default_unit: str, language: str = "zh") -> Tuple[List[Dict], Dict]:
    """
    Cached wrapper for LLM extraction.
    schema_signature ensures cache invalidation when rules change.
    _extractor is excluded from hashing (singleton).
    """
    return _extractor.extract_transactions(text, default_unit=default_unit, language=language)

# ==========================================
# 1. Page Config & CSS
# ==========================================
st.set_page_config(
    page_title=get_text("ui_title", st.session_state.language),
    page_icon="⚔️",
    layout="wide"
)

# Inject Game CSS
ui.apply_custom_css()

# ==========================================
# 2. Initialize Session State
# ==========================================
if 'ledger' not in st.session_state:
    # Load World Schema from config file if exists
    schema_path = "saves/world_config.json"
    import os
    if os.path.exists(schema_path):
        st.session_state.ledger = LedgerEngine(world_schema_path=schema_path)
    else:
        # V1.0 Release: Memory-Only Mode for Public Demo
        st.session_state.ledger = LedgerEngine(save_path=None)

if 'unit_registry' not in st.session_state:
    st.session_state.unit_registry = st.session_state.ledger.unit_registry

if 'extractor' not in st.session_state:
    try:
        st.session_state.extractor = LLMExtractor()
        st.session_state.llm_ready = True
    except Exception as e:
        st.session_state.llm_ready = False
        st.session_state.llm_error = str(e)

if 'last_transactions' not in st.session_state:
    st.session_state.last_transactions = []

if 'usage_tracker' not in st.session_state:
    st.session_state.usage_tracker = UsageTracker()

# Onboarding State
if 'first_time_user' not in st.session_state:
    import os
    has_save_file = os.path.exists("saves/save_slot_1_events.json")
    has_events = len(st.session_state.ledger.events) > 0
    st.session_state.first_time_user = not has_save_file and not has_events

if 'tutorial_dismissed' not in st.session_state:
    st.session_state.tutorial_dismissed = False

if 'first_success_shown' not in st.session_state:
    st.session_state.first_success_shown = False

# Rate Limiting State
if 'last_request_time' not in st.session_state:
    st.session_state.last_request_time = 0
if 'request_count' not in st.session_state:
    st.session_state.request_count = 0

# Ephemeral Warning
if 'deployment_check' not in st.session_state:
    import socket
    hostname = socket.gethostname().lower()
    st.session_state.is_cloud = any(x in hostname for x in ['streamlit', 'heroku', 'render'])
    st.session_state.deployment_check = True

if st.session_state.get('is_cloud', False):
    st.warning(f"""
    **{get_text("deployment_warning_title", st.session_state.language)}**  
    {get_text("deployment_warning_msg", st.session_state.language)}
    """, icon="⚠️")

# Demo Mode Warning (Always Show for V1.0)
if True:
    st.info(f"ℹ️ {get_text('deployment_warning_msg', st.session_state.language)}", icon="💾")

# ==========================================
# 3. Sidebar Layout
# ==========================================
with st.sidebar:
    # Language Switcher
    lang_options = {"🇺🇸 English": "en", "🇨🇳 中文": "zh"}
    current_label = [k for k, v in lang_options.items() if v == st.session_state.language][0]
    
    selected_lang_label = st.radio(
        "Language / 语言", 
        options=list(lang_options.keys()),
        index=list(lang_options.keys()).index(current_label),
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # Handle switch
    new_lang = lang_options[selected_lang_label]
    if new_lang != st.session_state.language:
        st.session_state.language = new_lang
        st.rerun()

    # API Key Configuration (BYOK)
    st.divider()
    st.subheader(get_text("key_setup", st.session_state.language))
    
    def on_api_key_change():
        # Force reload of extractor when key changes
        if 'extractor' in st.session_state:
            del st.session_state['extractor']
    
    st.text_input(
        get_text("key_label", st.session_state.language),
        type="password",
        key="user_api_key",
        help=get_text("key_help", st.session_state.language),
        on_change=on_api_key_change
    )
    
    if st.button(get_text("btn_test_conn", st.session_state.language)):
        import os
        key = st.session_state.get("user_api_key") or os.getenv("GOOGLE_API_KEY")
        if not key:
            st.error(get_text("err_no_key", st.session_state.language))
        else:
            try:
                from google import genai
                client = genai.Client(api_key=key)
                # Simple ping to list models or generate
                resp = client.models.generate_content(model="gemini-2.5-flash", contents="Ping")
                st.toast(get_text("toast_conn_success", st.session_state.language), icon="🟢")
            except Exception as e:
                st.error(get_text("err_conn_fail", st.session_state.language).format(e))

    # Cost Dashboard (Restored)
    st.subheader(get_text("cost_title", st.session_state.language))
    tracker = st.session_state.usage_tracker
    summary = tracker.get_summary()

    col_cost1, col_cost2 = st.columns(2)
    col_cost1.metric(get_text("cost_total", st.session_state.language), f"${summary['cost_usd']:.4f}")
    col_cost2.metric(get_text("cost_saved", st.session_state.language), f"${summary['saved_usd']:.4f}", delta_color="normal")
    st.caption(get_text("lbl_tokens", st.session_state.language).format(f"{summary['total_tokens']:,}"))

    ui.render_sidebar_stats(
        st.session_state.ledger.get_state(), 
        st.session_state.unit_registry,
        events_count=len(st.session_state.ledger.events),
        lang=st.session_state.language
    )
    
    # Cloud Persistence (Restored)
    st.divider()
    st.subheader(get_text("persist_title", st.session_state.language))
    save_tab, load_tab = st.tabs([get_text("tab_backup", st.session_state.language), get_text("tab_restore", st.session_state.language)])

    # === Tab 1: Export (Backup) ===
    with save_tab:
        ledger = st.session_state.ledger
        if len(ledger.events) > 0:
            import json
            from datetime import datetime
            
            # Package save data with metadata
            save_data = {
                "version": "1.7.0",
                "timestamp": datetime.now().isoformat(),
                "events": ledger.events,
                "last_event_id": ledger._event_id_counter,
                "active_buffs": ledger.temporal_state.to_dict()
            }
            
            save_json = json.dumps(save_data, indent=2, ensure_ascii=False)
            filename = f"litrpg_save_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            
            st.download_button(
                label=get_text("btn_download", st.session_state.language),
                data=save_json,
                file_name=filename,
                mime="application/json",
                help="Download current progress.",
                use_container_width=True
            )
        else:
            st.caption(get_text("msg_no_events", st.session_state.language))

    # === Tab 2: Import (Restore) ===
    with load_tab:
        uploaded_file = st.file_uploader(
            get_text("lbl_upload", st.session_state.language), 
            type=["json"], 
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            try:
                import json
                restored_data = json.load(uploaded_file)
                if "events" not in restored_data:
                    st.error(get_text("err_invalid_save", st.session_state.language))
                else:
                    event_count = len(restored_data["events"])
                    timestamp = restored_data.get("timestamp", "Unknown")
                    st.info(get_text("info_loaded", st.session_state.language).format(event_count, timestamp[:19]))
                    
                    if st.button(get_text("btn_confirm_restore", st.session_state.language), type="primary", use_container_width=True):
                        ledger.events = restored_data["events"]
                        ledger._event_id_counter = restored_data.get("last_event_id", len(ledger.events))
                        if "active_buffs" in restored_data:
                            ledger.temporal_state.from_dict(restored_data["active_buffs"])
                        ledger._events_hash = None
                        ledger.get_state()
                        st.toast(get_text("toast_restore_success", st.session_state.language), icon="🎉")
                        st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    # Reset Button
    st.divider()
    if st.button(get_text("btn_reset", st.session_state.language)):
        st.session_state.ledger = LedgerEngine()
        st.session_state.last_transactions = []
        import os
        if os.path.exists("saves/save_slot_1_events.json"):
            os.remove("saves/save_slot_1_events.json")
        st.rerun()

# ==========================================
# 4. Main Interface
# ==========================================
st.title(get_text("ui_title", st.session_state.language))
st.caption(get_text("ui_subtitle", st.session_state.language))

# Tabs
tab1, tab2 = st.tabs([
    get_text("tab_story", st.session_state.language), 
    get_text("tab_settings", st.session_state.language)
])

with tab1:
    # Tutorial
    if st.session_state.first_time_user and not st.session_state.tutorial_dismissed:
        st.info(get_text("msg_welcome", st.session_state.language))
        if st.button(get_text("btn_dismiss", st.session_state.language)):
            st.session_state.tutorial_dismissed = True
            st.rerun()

    # Manual Mode Toggle (Restored)
    is_offline = getattr(st.session_state.extractor, 'is_offline', False)
    manual_mode = st.toggle(get_text("toggle_manual", st.session_state.language), value=is_offline)

    # Input Area
    with st.form("action_form", clear_on_submit=False):
        if manual_mode:
            st.subheader(get_text("hdr_manual_input", st.session_state.language))
            user_input = st.text_area(
                label=get_text("lbl_json_input", st.session_state.language),
                height=180,
                value='[\n  {"action": "gain", "type": "gold", "value": "10", "unit": "GP", "reason": "Manual Entry"}\n]',
                help="Enter raw JSON event list.",
                label_visibility="collapsed"
            )
            submit_label = get_text("btn_exec_batch", st.session_state.language)
        else:
            user_input = st.text_area(
                get_text("label_input", st.session_state.language),
                height=180,
                placeholder=get_text("placeholder_input", st.session_state.language),
                label_visibility="collapsed"
            )
            submit_label = get_text("submit_btn", st.session_state.language)
    
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            submitted = st.form_submit_button(submit_label, type="primary", use_container_width=True)
        with col3:
            if st.form_submit_button(get_text("clear_log", st.session_state.language), use_container_width=True):
                 st.session_state.clear_confirm = True
                 st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Logic Processing
    if st.session_state.get("clear_confirm"):
        st.warning(get_text("confirm_clear_title", st.session_state.language))
        col_c1, col_c2 = st.columns(2)
        if col_c1.button(get_text("confirm_yes", st.session_state.language), key="yes_del"):
             st.session_state.last_transactions = []
             st.session_state.clear_confirm = False
             st.rerun()
        if col_c2.button(get_text("confirm_no", st.session_state.language), key="no_del"):
             st.session_state.clear_confirm = False
             st.rerun()

    # Rate Limiting Logic (Restored)
    if submitted and user_input:
        import time
        now = time.time()
        count = st.session_state.request_count
        cooldown = 1.0 if manual_mode else 3.0
        if count >= 10: cooldown = 30.0
        
        if count >= 100:
            st.error(get_text("err_session_limit", st.session_state.language))
            st.stop()
            
        time_since_last = now - st.session_state.last_request_time
        if time_since_last < cooldown:
            st.warning(get_text("msg_cooldown", st.session_state.language).format(f"{cooldown - time_since_last:.1f}"))
            st.stop()
            
        st.session_state.last_request_time = now
        st.session_state.request_count += 1

    if submitted and user_input:
        transactions = []
        
        if manual_mode:
            import json
            try:
                transactions = json.loads(user_input)
                if not isinstance(transactions, list):
                    st.error(get_text("err_json_list", st.session_state.language))
                    transactions = []
            except Exception as e:
                st.error(get_text("err_json_syntax", st.session_state.language).format(e))
        else:
            # AI Mode
            if not st.session_state.llm_ready:
                st.error(get_text("err_llm", st.session_state.language).format(st.session_state.get('llm_error')))
            else:
                with st.status(get_text("status_thinking", st.session_state.language), expanded=True) as status:
                    st.write(get_text("status_extracting", st.session_state.language))
                    # Generate Schema Signature
                    ledger = st.session_state.ledger
                    # Fix: UnitRegistry uses 'rules' or 'schema.conversions', not 'units'
                    schema_sig = f"{ledger.unit_registry.base_unit}:{sorted(ledger.unit_registry.rules.keys())}"
                    
                    try:
                        transactions, usage = _get_cached_extraction(
                            user_input, 
                            schema_sig, 
                            st.session_state.extractor, 
                            st.session_state.unit_registry.schema.base_unit,
                            st.session_state.language
                        )
                    except Exception as e:
                        st.error(get_text("err_conn_fail", st.session_state.language).format(e))
                        status.update(label="Error", state="error", expanded=True)
                        st.stop()
                    
                    if usage:
                         # Fix: track_usage expects a single 'metadata' dict
                        st.session_state.usage_tracker.track_usage(usage)
                        cost = st.session_state.usage_tracker.total_cost_usd # Use total or calculate delta if needed
                        st.caption(f"Cost: ${cost:.6f}")
                    
                    status.update(label=get_text("status_complete", st.session_state.language), state="complete", expanded=False)

        # Batch Processing
        if transactions:
            ledger = st.session_state.ledger
            success, message = ledger.process_batch(transactions)
            
            # V1.2.5 Smart Fix Logic (Restored)
            if not success and isinstance(message, list) and len(message) > 0:
                import re
                from logic.world_schema import WorldSchema
                from logic.unit_registry import UnitRegistry
                error_msg = message[0]
                match = re.search(r"Unknown unit: (.+)\. Available", error_msg)
                
                if match:
                    detected_unit = match.group(1).strip()
                    recommended_preset = WorldSchema.detect_schema_for_unit(detected_unit)
                    if recommended_preset:
                        new_schema = getattr(WorldSchema, recommended_preset)()
                        ledger.unit_registry = UnitRegistry(new_schema)
                        new_schema.save_to_file("saves/world_config.json")
                        st.toast(get_text("toast_auto_adapt", st.session_state.language).format(new_schema.currency_name), icon="🔄")
                        success, message = ledger.process_batch(transactions)
            
            if success:
                st.session_state.last_transactions = transactions
                ledger.save_events_to_file("saves/save_slot_1_events.json")
                if not st.session_state.first_success_shown:
                    st.balloons()
                    st.session_state.first_success_shown = True
                st.rerun()
            else:
                st.error(get_text("err_rejected", st.session_state.language).format(message))
                # Improved Math Error Feedback
                msg_str = str(message)
                if "division by zero" in msg_str.lower() or "math" in msg_str.lower():
                     st.toast(get_text("toast_formula_err", st.session_state.language).format(msg_str), icon="➗")
                with st.expander("Debug"):
                    st.json(transactions)
        elif not manual_mode and not st.session_state.get('llm_error'):
             st.info(get_text("info_no_action", st.session_state.language))

    # Feedback Display
    if st.session_state.last_transactions:
        ui.render_transaction_feedback(
            st.session_state.last_transactions, 
            st.session_state.unit_registry,
            lang=st.session_state.language
        )

    # Event History (Searchable)
    st.divider()
    st.subheader(get_text("hdr_history", st.session_state.language)) # Translate?
    
    events = st.session_state.ledger.events
    if not events:
        st.caption(get_text("caption_no_events", st.session_state.language))
    else:
        search_query = st.text_input(get_text("lbl_search", st.session_state.language), label_visibility="collapsed")
        filtered_events = [e for e in events if not search_query or search_query.lower() in str(e).lower()]
        
        if not filtered_events:
            st.info(get_text("info_no_match", st.session_state.language))
        else:
            # Compact Table
            data = []
            for e in reversed(filtered_events):
                eid = e.get('event_id')
                # details...
                data.append({"ID": eid, "Msg": f"{e.get('action')} {e.get('type')}", "Val": e.get('value')})
            st.dataframe(filtered_events, use_container_width=True, height=300)

with tab2:
    ui.render_world_settings(st.session_state.ledger, lang=st.session_state.language)
    st.divider()
    ui.render_formula_panel(st.session_state.ledger, lang=st.session_state.language)
