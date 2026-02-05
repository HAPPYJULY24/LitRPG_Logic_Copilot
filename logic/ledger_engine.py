"""
LedgerEngine V1.1 - Event Sourcing Architecture
负责处理所有数值逻辑与数据落盘 (The Symbolic Side)

BREAKING CHANGES from V1.0:
- Storage format changed from {gold, inventory} to event log
- State is now COMPUTED via reduce(), not stored directly
- Supports retconning (modifying historical events)
- Integrates UnitRegistry, FormulaEngine, TemporalState
"""
import json
import os
import shutil
import difflib  # V1.5: For Fuzzy Matching
import re
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from logic.unit_registry import UnitRegistry
from logic.formula_engine import FormulaEngine
from logic.temporal_state import TemporalState
from logic.rule_engine import RuleEngine  # V1.1.2: Global rule modifiers
from logic.world_schema import WorldSchema, load_or_default  # V1.2: Dynamic schemas


class LedgerEngine:
    """
    Event Sourcing-based ledger for LitRPG stat tracking.
    
    Core Principles:
    1. State is COMPUTED, not stored (Event Sourcing)
    2. Events are immutable and append-only
    3. Retconning = modify event + replay
    4. Temporal context tracked during replay (for buff expiry)
    5. Hash-based caching prevents Streamlit rerun lag
    """
    
    def __init__(self, save_path="saves/save_slot_1_events.json", world_schema: Optional[WorldSchema] = None, world_schema_path: Optional[str] = None, strict_mode: bool = False):
        """
        Initialize ledger with Event Sourcing architecture.
        
        Args:
            save_path: Path to event log file (V1.1 format). If None, runs in Memory-Only Mode.
            world_schema: WorldSchema instance (V1.2, optional)
            world_schema_path: Path to schema JSON file (V1.2, optional)
            strict_mode: If True, raises exceptions on underflow. If False (Draft Mode), allows negative balances.
            
        V1.2: If both schema params are None, uses Classic Fantasy preset.
        """
        self.save_path = save_path
        self.strict_mode = strict_mode  # V1.5: Draft Mode
        
        # Event Sourcing: Store events, not state
        self.events: List[Dict] = []
        self._event_id_counter = 0
        
        # Performance: Cache computed state
        self._cached_state: Optional[Dict] = None
        self._events_hash: Optional[int] = None
        
        # V1.2: Load world schema
        if world_schema:
            schema = world_schema
        else:
            schema = load_or_default(world_schema_path)
        
        # Core engines (V1.2: pass schema to UnitRegistry)
        self.unit_registry = UnitRegistry(schema)
        self.formula_engine = FormulaEngine()
        self.temporal_state = TemporalState()
        self.rule_engine = RuleEngine()  # V1.1.2: Global modifiers
        
        # Register default formulas (can be customized later)
        self._register_default_formulas()
        
        # Load events from disk
        # Load events from disk
        self.load_events()

        # --- V1.4.1 FIX: Expanded Whitelist ---
        # Covers: XP, Currency, HP/MP/Stamina, Combat Stats, and Abstract concepts (Debt/%)
        self.UNROBUST_STATS = {
            'XP', 'EXPERIENCE', 
            'GOLD', 'GP', 'SP', 'CP', 'CREDITS', 'MONEY', 'USD', '$', 'CENT',
            'HEALTH', 'HP', 'LIFE',
            'MANA', 'MP', 'MAGIC',
            'STAMINA', 'ENERGY',
            'FATIGUE', 'DEBT', 'STRESS',
            'DAMAGE', 'DEFENSE', 'ATTACK', 'POWER'
        }
    
    def _register_default_formulas(self):
        """
        Register default computed stats.
        Users can add more via register_formula().
        """
        # Example: Attack = Strength * 2 + Level
        # (These are just examples; actual formulas depend on game rules)
        pass
    
    @staticmethod
    def _clean_number(value_str: str) -> str:
        """
        Sanitize number strings by strictly enforcing numeric content.
        
        CRITICAL SECURITY FIX (V1.3):
        - NO LONGER falls back to original string if regex fails.
        - Returns "0" if no valid number found.
        - REJECTS "Infinity", "NaN" to prevent state corruption.
        
        Args:
            value_str: Raw string
            
        Returns:
            Cleaned numeric string (or "0")
        """
        if not isinstance(value_str, str):
            value_str = str(value_str)
        
        # Remove commas and percentages
        clean = value_str.replace(',', '').replace('%', '')
        
        # Extract number using regex
        import re
        # Match only legitimate finite numbers (integers or decimals)
        # Rejects "Infinity", "NaN" implicitly as they don't match \d
        match = re.search(r'-?\d+(\.\d+)?', clean)
        
        if match:
            val_str = match.group(0)
            # Double-check against Decimal's finite check just to be sure
            try:
                d = Decimal(val_str)
                if not d.is_finite():
                    return "0"
                return val_str
            except:
                return "0"
                
        return "0"
    
    def register_formula(self, stat_name: str, expression: str):
        """
        Register a computed stat formula.
        
        Args:
            stat_name: Name of computed stat (e.g., "Attack")
            expression: Formula (e.g., "Strength * 2 + Level")
        """
        self.formula_engine.register_formula(stat_name, expression)
        self._invalidate_cache()

    def normalize_entity_name(self, raw_name: str, existing_names: List[str]) -> Tuple[str, bool]:
        """
        V1.5: Fuzzy match entity name against known inventory keys.
        
        Args:
            raw_name: Input name (e.g., "Rottn Core")
            existing_names: List of known names (e.g., ["Rotten Core"])
            
        Returns:
            (Best Name, Is Ambiguous)
            - If exact match: (raw_name, False)
            - If strong single match (>0.8): (match, False)
            - If ambiguous matches (scores close): (raw_name, True)
            - If no match: (raw_name, False)
        """
        if not raw_name or not existing_names:
            return raw_name, False
            
        # Exact match check first
        if raw_name in existing_names:
            return raw_name, False
            
        # Pre-compute numeric skeleton
        raw_skeleton = re.sub(r'\d+', '', raw_name)
        
        candidates = []
        for name in existing_names:
            # 1. Numeric Safety Check: If names differ ONLY by numbers breakdown, treat as distinct.
            # e.g. "Item 1" vs "Item 2" -> Skeletons "Item " vs "Item " -> Match -> Distinct!
            # Wait, if skeletons match, it means ONLY numbers differ. So we should SKIP fuzzy match.
            name_skeleton = re.sub(r'\d+', '', name)
            if raw_skeleton == name_skeleton and raw_name != name:
                continue
                
            ratio = difflib.SequenceMatcher(None, raw_name.lower(), name.lower()).ratio()
            # Raise base threshold to 0.9 to prevent "Elixir of Life" vs "Elixir of Light" merging
            if ratio > 0.9:  
                candidates.append((ratio, name))
        
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        if not candidates:
            return raw_name, False
            
        best_ratio, best_name = candidates[0]
        
        # Threshold check (Double verification)
        if best_ratio < 0.9:
            return raw_name, False
            
        # Ambiguity check (V1.5.1)
        if len(candidates) > 1:
            second_ratio, second_name = candidates[1]
            if (best_ratio - second_ratio) < 0.1:
                return raw_name, True
                
        return best_name, False
            
        # Ambiguity check (V1.5.1)
        if len(candidates) > 1:
            second_ratio, second_name = candidates[1]
            if (best_ratio - second_ratio) < 0.1:
                print(f"DEBUG: Ambiguous! {best_name} ({best_ratio}) vs {second_name} ({second_ratio})")
                return raw_name, True
                
        return best_name, False
    
    def load_events(self):
        """Load event log from disk"""
        # Memory-Only Mode
        if self.save_path is None:
            self.events = []
            self._event_id_counter = 0
            return

        if os.path.exists(self.save_path):
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.events = data.get("events", [])
                self._event_id_counter = data.get("last_event_id", 0)
                
                # Restore temporal state
                if "active_buffs" in data:
                   self.temporal_state.from_dict(data["active_buffs"])
        else:
            # First run: initialize empty log
            self.events = []
            self._event_id_counter = 0
    
    def _auto_save(self):
        """
        Atomic write with backup protection.
        
        CRITICAL: Prevents data corruption if process crashes mid-write.
        """
        # Memory-Only Mode
        if self.save_path is None:
            return

        import json
        import os
        import shutil
        
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        
        # Create backup of current file
        if os.path.exists(self.save_path):
            backup_path = self.save_path + ".backup"
            try:
                shutil.copy(self.save_path, backup_path)
            except OSError:
                pass 
        
        # Serialize current state
        data = {
            "events": self.events,
            "last_event_id": self._event_id_counter,
            "active_buffs": self.temporal_state.to_dict()
        }
        
        # Atomic write (write to temp file, then replace)
        temp_path = self.save_path + ".tmp"
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Atomic swap (os.replace is atomic on all platforms)
            os.replace(temp_path, self.save_path)
        except Exception as e:
            print(f"CRITICAL SAVE ERROR: {e}")

    def save_events_to_file(self, filepath: str = None):
        """
        Public wrapper for manual saving.
        """
        if filepath:
            # Update path if provided (allows 'Save As' functionality)
            self.save_path = filepath
        self._auto_save()
    
    def _invalidate_cache(self):
        """Invalidate cached state (forces reduce() on next get_state())"""
        self._events_hash = None
    
    def _get_initial_state(self) -> Dict:
        """
        Get initial empty state structure.
        
        Returns:
            Empty state dict
        """
        return {
            "gold_cp": Decimal("0"),  # Stored in base unit (Copper)
            "inventory": {},
            "stats": {},  # Base stats (Strength, Level, etc.)
            "computed_stats": {},  # Calculated stats (Attack, etc.)
            "buffs": [],  # Active buff IDs
            "alerts": []  # V1.5: Critical state warnings
        }
    
    def _apply_event(self, state: Dict, event: Dict, context: Dict) -> Dict:
        """
        Apply a single event to state.
        
        Args:
            state: Current state
            event: Event to apply
            context: Temporal context {chapter, word_count, timestamp}
            
        Returns:
            Updated state
        """
        # V1.1.2: Global rules are applied in add_event() before storage
        # So we NO LONGER apply them here during replay (would cause double-application)
        
        action = event.get("action")
        event_type = event.get("type")
        
        # Handle different event types
        if event_type == "gold":
            # Currency transactions
            value_raw = event.get("value", "0")
            
            # V1.5: Handle Indeterminate Values
            if value_raw in [None, "", "TBD", "tbd"]:
                event["requires_manual_fix"] = True
                return state  # Skip calculation
            
            value_str = str(value_raw)
            unit = event.get("unit", "CP")
            
            # Convert to base unit using UnitRegistry
            clean_val = self._clean_number(value_str)
            cp_value = self.unit_registry.to_base(clean_val, unit)
            
            if action == "gain":
                state["gold_cp"] += cp_value
            elif action == "lose":
                # ===== P0 FIX: Gold Balance Check (V5.1 + V1.5 Draft Mode) =====
                if state["gold_cp"] < cp_value:
                    if self.strict_mode:
                        # Convert back to display units for error message
                        have_gp = state["gold_cp"] / 100
                        need_gp = cp_value / 100
                        raise ValueError(
                            f"Insufficient gold: need {need_gp:.2f} GP, have {have_gp:.2f} GP"
                        )
                    else:
                        # V1.5 Draft Mode: Allow negative && mark implicit
                        event["is_implicit"] = True
                        if "logs" not in event: event["logs"] = []
                        event["logs"].append("Warning: Gold underflow allowed in Draft Mode")
                # ====================================================================
                state["gold_cp"] -= cp_value
            elif action == "set":
                # BUG FIX: Ensure SET respects unit conversion!
                # print(f"DEBUG: Setting Gold. Input: {value_str} {unit} -> Base: {cp_value}")
                state["gold_cp"] = cp_value
        
        elif event_type == "item":
            # Inventory transactions
            raw_name = event.get("name")
            
            # V1.5: Fuzzy Matching
            # Check against existing inventory keys AND Schema unit keys
            known_keys = list(state["inventory"].keys())
            name, is_ambiguous = self.normalize_entity_name(raw_name, known_keys)
            
            if is_ambiguous:
                 event["requires_manual_fix"] = True
                 if "logs" not in event: event["logs"] = []
                 event["logs"].append(f"Ambiguous match for '{raw_name}' - please verify.")
                 # Fallback to raw_name (don't auto-convert)
                 name = raw_name
            
            # If name changed (and valid), update event (back-annotation)
            elif name != raw_name:
                event["original_name"] = raw_name
                event["name"] = name
                if "logs" not in event: event["logs"] = []
                event["logs"].append(f"Fuzzy Matched: {raw_name} -> {name}")
            
            # V1.5: Handle Indeterminate Qty
            qty_raw = event.get("qty", 1)
            if qty_raw in [None, "", "TBD", "tbd"]:
                event["requires_manual_fix"] = True
                return state

            # HOTFIX: Sanitize qty string before Decimal conversion
            qty_str = self._clean_number(str(qty_raw))
            qty = Decimal(qty_str)
            
            # ===== P0 FIX: Quantity Validation (V5.1 - Negative Exploit Prevention) =====
            # Note: Negative Qty in "gain" is weird, currently blocked. 
            if qty <= 0:
                if self.strict_mode:
                     raise ValueError(f"Invalid quantity: {qty}. Must be positive.")
                # If not strict mode, maybe allow? But prompt focused on "lose" underflow.
                # We'll keep positive validation for now unless user really wants bug compatibility.
            # ============================================================================
            
            current_qty = state["inventory"].get(name, Decimal("0"))
            
            if action == "gain":
                state["inventory"][name] = current_qty + qty
            elif action == "lose":
                # ===== P0 FIX: Balance Check (V5.1 + V1.5 Draft Mode) =====
                if current_qty < qty:
                    if self.strict_mode:
                        raise ValueError(
                            f"Insufficient {name}: need {qty}, have {current_qty}"
                        )
                    else:
                        # V1.5 Draft Mode: Allow negative
                        event["is_implicit"] = True
                        if "logs" not in event: event["logs"] = []
                        event["logs"].append(f"Warning: Item {name} underflow allowed")
                # ================================================================
                state["inventory"][name] = current_qty - qty
        
        elif event_type == "stat":
            # Base stat changes
            name = event.get("name")
            
            # V1.5: Handle Indeterminate Value
            val_raw = event.get("value", 0)
            if val_raw in [None, "", "TBD", "tbd"]:
                event["requires_manual_fix"] = True
                return state
                
            # HOTFIX: Sanitize value string before Decimal conversion
            value_str = self._clean_number(str(val_raw))
            value = Decimal(value_str)
            
            current_value = state["stats"].get(name, Decimal("0"))
            
            if action == "gain":
                state["stats"][name] = current_value + value
            elif action == "lose":
                state["stats"][name] = current_value - value
            elif action == "set":
                state["stats"][name] = value
            
            # Mark dependent formulas as dirty
            self.formula_engine.mark_dirty(name)
        
        elif event_type == "buff":
            # Buff management
            if action == "gain":
                # ===== V1.2.1 HOTFIX: Soft Fallback for Missing Expiry =====
                # If LLM fails to extract expiry info, use safe defaults instead of failing
                if not event.get('expiry_type'):
                    event['expiry_type'] = 'chapter'
                
                if not event.get('expiry_value'):
                    # Only require expiry_value for non-permanent buffs
                    if event.get('expiry_type') != 'permanent':
                        event['expiry_value'] = 1
                # ==========================================================
                
                # ===== V1.2.3 HOTFIX: Sanitize Buff Effects =====
                # Clean percentage signs and filter non-numeric values from effects
                raw_effects = event.get("effects", {})
                sanitized_effects = {}
                
                for stat_name, stat_value in raw_effects.items():
                    try:
                        # Clean the value (remove %, units, etc.)
                        clean_val = self._clean_number(str(stat_value))
                        # Verify it can be converted to Decimal
                        Decimal(clean_val)  # Test conversion
                        sanitized_effects[stat_name] = clean_val
                    except (ValueError, Exception) as e:
                        # Skip non-numeric effects (e.g., "increased", "boosted")
                        pass
                # ==========================================================
                
                # Add buff (handled by temporal_state)
                buff_id = self.temporal_state.add_buff(
                    name=event.get("name", "Unknown Buff"),
                    effects=sanitized_effects,  # ← Use cleaned effects
                    expiry_type=event.get("expiry_type", "permanent"),
                    expiry_value=event.get("expiry_value"),
                    description=event.get("description", "")
                )
                if buff_id not in state["buffs"]:
                    state["buffs"].append(buff_id)
        
        elif event_type == "chapter_start":
            # Temporal marker (updates context, not state)
            pass
        
        elif event_type == "word_count_delta":
            # Temporal marker
            pass
        
        return state
    
    def reduce(self, events: List[Dict]) -> Dict:
        """
        Replay all events to compute final state.
        
        CRITICAL: Temporal context is tracked DURING replay,
        not after, to handle buff expiry correctly.
        
        Args:
            events: List of events to replay
            
        Returns:
            Computed final state
        """
        state = self._get_initial_state()
        context = {
            "chapter": 0,
            "word_count": 0,
            "timestamp": None
        }
        
        for event in events:
            # Update temporal context from event markers
            if event.get("type") == "chapter_start":
                context["chapter"] += 1
            
            if "word_count_delta" in event:
                context["word_count"] += event["word_count_delta"]
            
            if "timestamp" in event:
                context["timestamp"] = event["timestamp"]
            
            # CRITICAL: Check buff expiry BEFORE applying event
            expired_buffs = self.temporal_state.check_expiry(
                current_chapter=context["chapter"],
                word_count=context["word_count"],
                timestamp=context["timestamp"]
            )
            
            # Remove expired buffs from state
            for expired_id in expired_buffs:
                if expired_id in state["buffs"]:
                    state["buffs"].remove(expired_id)
            
            # Apply event
            state = self._apply_event(state, event, context)
        
        # Compute derived stats with buff effects
        buff_effects = self.temporal_state.get_active_effects()
        
        # Combine base stats with buff effects
        combined_stats = state["stats"].copy()
        for stat, modifier in buff_effects.items():
            current = combined_stats.get(stat, Decimal("0"))
            combined_stats[stat] = current + modifier
        
        # P0 FIX: Inject temporal context (chapter, word_count) into stats for formula evaluation
        # This allows formulas like "Agility - (chapter - 3)" to resolve "chapter"
        combined_stats["chapter"] = Decimal(context["chapter"])
        combined_stats["word_count"] = Decimal(context["word_count"])
        
        # Recalculate all formulas
        state["computed_stats"] = self.formula_engine.get_all_computed_stats(combined_stats)
        
        # V1.5.1: Critical State Alerts (Regenerated fresh each reduce)
        # Check both base stats and computed stats
        all_stats = {**state["stats"], **state["computed_stats"]}
        CRITICAL_KEYS = {'HP', 'HEALTH', 'LIFE', 'MP', 'MANA', 'STAMINA', 'ENERGY'}
        
        state["alerts"] = []  # Clear previous alerts (though state is fresh each reduce anyway)
        
        for k, v in all_stats.items():
            if k.upper() in CRITICAL_KEYS:
               if v < 0:
                   state["alerts"].append(f"CRITICAL: {k} is negative ({v})")
        
        return state
    
    def get_state(self) -> Dict:
        """
        Get current state with intelligent caching.
        
        CRITICAL: Only replays if events have changed (hash check)
        to avoid Streamlit rerun performance trap.
        
        Returns:
            Current computed state
        """
        # Compute hash of event list
        current_hash = hash(tuple(str(e) for e in self.events))
        
        if self._events_hash != current_hash:
            # Events changed, need to replay
            self._cached_state = self.reduce(self.events)
            self._events_hash = current_hash
        
        return self._cached_state
    
    def add_event(self, event: Dict) -> Tuple[bool, str]:
        """
        Add a new event to the log (append-only).
        
        Args:
            event: Event dictionary
            
        Returns:
            (success: bool, message: str)
        """
        # Assign event ID
        self._event_id_counter += 1
        event["event_id"] = self._event_id_counter
        
        # V1.1.2: Apply global rules to event BEFORE storing
        # This ensures the stored event reflects post-rule values
        context = {"chapter": 0, "word_count": 0, "timestamp": None}  # Current context
        event = self.rule_engine.apply_rules(event, context)
        
        # Validate event would not cause invalid state
        test_events = self.events + [event]
        try:
            test_state = self.reduce(test_events)
            
            # Check for negative values
            if self.strict_mode and test_state["gold_cp"] < 0:
                return False, f"金币不足 (会导致负值: {test_state['gold_cp']})"
            
            for item, qty in test_state["inventory"].items():
                if self.strict_mode and qty < 0:
                    return False, f"物品 [{item}] 数量不足 (会导致负值: {qty})"
            
            for stat, value in test_state["stats"].items():
                if self.strict_mode and value < 0:
                    return False, f"属性 [{stat}] 不能为负数 (会导致: {value})"
            
        except Exception as e:
            return False, f"事件校验失败: {str(e)}"
        
        # Validation passed, append event
        self.events.append(event)
        self._invalidate_cache()
        self._auto_save()
        
        return True, "Success"

    def _validate_security_rules(self, event: Dict) -> Tuple[bool, str]:
        """
        Enforce strict security bounds to mitigate Prompt Injection.
        
        Rules:
        1. RESOURCE_CAP: Max gain per event (Gold=1000, Item=10, Stat=5).
        2. KEYWORD_BLOCK: Reject suspicious 'reason' strings with NORMALIZATION.
        
        Args:
            event: The candidate event
            
        Returns:
            (is_safe: bool, error_message: str)
        """
        # --- 1. KEYWORD BLOCKLIST (ENHANCED V1.3) ---
        blocked_keywords = ["ignoreprompt", "ignoreprevious", "cheatcode", "developeroverride", "systemoverride", "ignoreinstructions", "disregardprevious"]
        
        # Normalize: lowercase, remove spaces and underscores, remove special chars
        import re
        reason_raw = str(event.get("reason", "")).lower()
        reason_norm = re.sub(r'[\s_\W]+', '', reason_raw)  # Strip all non-alphanumeric
        
        for kw in blocked_keywords:
            if kw in reason_norm:
                return False, f"Security Alert: Blocked suspicious keyword '{kw}' (detected in '{reason_raw}')"

        # --- 2. NUMERICAL BOUNDS (WHITELIST MECHANISM V1.4) ---
        action = event.get("action")
        evt_type = event.get("type")
        
        # Use simple trusted parsing for checks (event hasn't been added yet)
        def get_decimal(k, default="0"):
            return Decimal(self._clean_number(str(event.get(k, default))))
        
        if action == "gain":
            val = get_decimal("value")
            
            # ALLOWLIST: These attributes/units allow high values (e.g. +1000 XP)
            # Normalized to Uppercase
            WHITELIST_HIGH_CAP = self.UNROBUST_STATS
            SAFE_LIMIT_HIGH = 999999
            SAFE_LIMIT_STD = 20     # For regular stats (Strength, etc.)
            
            if evt_type == "gold":
                # Check Currency Unit
                unit = str(event.get("unit", "")).upper()
                
                # If matches whitelist, allow huge gains. Else, use a reasonable default (10k).
                # User's "MONEY" etc likely appear here.
                # If the unit is recognized as high-cap, use HIGH_LIMIT.
                limit = SAFE_LIMIT_HIGH if unit in WHITELIST_HIGH_CAP else 10000
                
                if val > limit:
                    return False, f"Security Alert: Gold/Currency gain {val} exceeds safety limit ({limit})."
            
            elif evt_type == "stat":
                # Check Stat Name
                name = str(event.get("name", "")).upper()
                
                # XP is a stat, so it needs the high limit.
                limit = SAFE_LIMIT_HIGH if name in WHITELIST_HIGH_CAP else SAFE_LIMIT_STD
                
                if val > limit:
                    return False, f"Security Alert: Stat increase {val} exceeds safety limit ({limit})."

            elif evt_type == "item":
                qty = get_decimal("qty", "1")
                if qty > 50:
                    return False, f"Security Alert: Item quantity {qty} exceeds safety limit (50)."
            
        return True, "Safe"
    
    def process_batch(self, transactions: List[Dict]) -> Tuple[bool, List[str]]:
        """
        原子性执行一批交易。要么全部成功，要么全部失败。
        
        Args:
            transactions: 交易指令列表
            
        Returns:
            (success: bool, logs: list)
        """
        logs = []
        
        # Convert transactions to events
        events_to_add = []
        for tx in transactions:
            # SECURITY CHECK (V1.3)
            is_safe, security_msg = self._validate_security_rules(tx)
            if not is_safe:
                return False, [f"⛔ Transaction Blocked: {security_msg}"]
                
            self._event_id_counter += 1
            event = tx.copy()
            event["event_id"] = self._event_id_counter
            events_to_add.append(event)
        
        # Test if batch is valid
        test_events = self.events + events_to_add
        try:
            test_state = self.reduce(test_events)
            
            # Validate final state
            if self.strict_mode and test_state["gold_cp"] < 0:
                return False, [f"交易批次失败: 金币不足 (最终值: {test_state['gold_cp']} CP)"]
            
            for item, qty in test_state["inventory"].items():
                if self.strict_mode and qty < 0:
                    return False, [f"交易批次失败: 物品 [{item}] 数量不足 (最终值: {qty})"]
            
        except Exception as e:
            return False, [f"交易批次失败: {str(e)}"]
        
        # All valid, commit
        self.events.extend(events_to_add)
        self._invalidate_cache()
        self._auto_save()
        
        # Generate success logs
        for event in events_to_add:
            action = event.get("action", "").upper()
            event_type = event.get("type")
            
            if event_type == "gold":
                value = event.get("value")
                unit = event.get("unit", "CP")
                logs.append(f"{action} {value} {unit}")
            elif event_type == "item":
                name = event.get("name")
                qty = event.get("qty", 1)
                logs.append(f"{action} {name} x{qty}")
            elif event_type == "stat":
                name = event.get("name")
                value = event.get("value")
                logs.append(f"{action} {name} +{value}")
            elif event_type == "buff":
                name = event.get("name")
                logs.append(f"Buff Applied: {name}")
        
        return True, logs
    
    def modify_event(self, event_id: int, new_data: Dict) -> Tuple[bool, str]:
        """
        Modify a historical event and replay (retconning).
        
        Args:
            event_id: ID of event to modify
            new_data: Fields to update
            
        Returns:
            (success: bool, message: str)
        """
        # Find event
        event_index = None
        for i, evt in enumerate(self.events):
            if evt.get("event_id") == event_id:
                event_index = i
                break
        
        if event_index is None:
            return False, f"Event #{event_id} not found"
        
        # Update event
        self.events[event_index].update(new_data)
        
        # Try to replay
        try:
            new_state = self.reduce(self.events)
            
            # Validate final state
            if self.strict_mode and new_state["gold_cp"] < 0:
                # Rollback
                self.load_events()  # Reload from disk
                return False, f"冲突: 金币不足 ({new_state['gold_cp']} CP)"
            
            for item, qty in new_state["inventory"].items():
                if self.strict_mode and qty < 0:
                    self.load_events()
                    return False, f"冲突: 物品 [{item}] 数量不足 ({qty})"
            
            # Success: save and invalidate cache
            self._invalidate_cache()
            self._auto_save()
            return True, "事件已修改，状态已重算"
            
        except Exception as e:
            # Rollback
            self.load_events()
            return False, f"重算失败: {str(e)}"

    def delete_event(self, event_id: int) -> Tuple[bool, str]:
        """
        Delete a historical event and replay.
        
        Args:
            event_id: ID of event to delete
            
        Returns:
            (success: bool, message: str)
        """
        # Find event
        event_index = None
        for i, evt in enumerate(self.events):
            if evt.get("event_id") == event_id:
                event_index = i
                break
        
        if event_index is None:
            return False, f"Event #{event_id} not found"
        
        # Remove event (create backup of list in case we need to rollback)
        original_events = self.events.copy()
        del self.events[event_index]
        
        # Try to replay
        try:
            new_state = self.reduce(self.events)
            
            # Validate final state
            if self.strict_mode and new_state["gold_cp"] < 0:
                self.events = original_events
                return False, f"删除失败: 金币不足 (会导致: {new_state['gold_cp']} CP)"
            
            for item, qty in new_state["inventory"].items():
                if self.strict_mode and qty < 0:
                    self.events = original_events
                    return False, f"删除失败: 物品 [{item}] 数量不足 (会导致: {qty})"
            
            # Success
            self._invalidate_cache()
            self._auto_save()
            return True, f"事件 #{event_id} 已删除"
            
        except Exception as e:
            self.events = original_events
            return False, f"删除失败: {str(e)}"

    def delete_events(self, event_ids: List[int]) -> Tuple[bool, List[str]]:
        """
        Batch delete events (V1.2 Requirement).
        
        Args:
            event_ids: List of event IDs to delete
            
        Returns:
            (success: bool, logs: list of messages)
        """
        # Create backup
        original_events = self.events.copy()
        
        # Filter out events to delete
        # Use set for faster lookups
        ids_to_delete = set(event_ids)
        self.events = [e for e in self.events if e.get("event_id") not in ids_to_delete]
        
        count = len(original_events) - len(self.events)
        if count == 0:
            return True, ["No events deleted (IDs not found)"]
            
        # Try to replay
        try:
            new_state = self.reduce(self.events)
            
            # Validate final state
            if self.strict_mode and new_state["gold_cp"] < 0:
                self.events = original_events
                return False, [f"Batch delete failed: Insufficient Gold ({new_state['gold_cp']} CP)"]
            
            for item, qty in new_state["inventory"].items():
                if self.strict_mode and qty < 0:
                    self.events = original_events
                    return False, [f"Batch delete failed: Insufficient {item} ({qty})"]
            
            # Success
            self._invalidate_cache()
            self._auto_save()
            return True, [f"Successfully deleted {count} events"]
            
        except Exception as e:
            self.events = original_events
            return False, [f"Batch delete failed: {str(e)}"]
    
    # Legacy compatibility methods (for V1.0 app.py)
    def process_transaction(self, tx: Dict) -> Tuple[bool, str]:
        """Legacy single transaction method (redirects to add_event)"""
        return self.add_event(tx)
