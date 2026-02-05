"""
RuleEngine V1.1.2 - Global Rule Modifier System
处理全局规则覆盖,例如"所有金币收益减半"或章节级别 debuff

NEW in V1.1.2: Addresses P0-2 failure from extreme testing
"""
from decimal import Decimal
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass


OperationType = Literal["multiply", "add", "set"]
TargetType = Literal["gold", "item", "stat", "buff", "any"]


@dataclass
class Rule:
    """
    Represents a global modifier rule.
    
    Attributes:
        id: Unique identifier
        target_type: What type of events this rule affects
        operation: How to modify the value (multiply/add/set)
        modifier: The modifier value (Decimal)
        condition: Optional:Optional condition expression (future enhancement)
                     Example: "chapter > 3"
        description: Human-readable description
    """
    id: str
    target_type: TargetType
    operation: OperationType
    modifier: Decimal
    condition: Optional[str] = None
    description: str = ""
    
    def __post_init__(self):
        """Ensure modifier is Decimal"""
        if not isinstance(self.modifier, Decimal):
            self.modifier = Decimal(str(self.modifier))


class RuleEngine:
    """
    Manages global rules that modify events before they're applied to state.
    
    Example Usage:
        >>> rule_engine = RuleEngine()
        >>> rule_engine.add_rule(
        ...     target_type="gold",
        ...     operation="multiply",
        ...     modifier="0.5",
        ...     description="通货膨胀: 所有金币收益减半"
        ... )
        'rule_001'
        
        >>> event = {"action": "gain", "type": "gold", "value": "100", "unit": "GP"}
        >>> modified = rule_engine.apply_rules(event)
        >>> modified["value"]
        '50.0'
    """
    
    def __init__(self):
        """Initialize with empty rule list"""
        self.active_rules: List[Rule] = []
        self._rule_id_counter = 0
    
    def add_rule(self,
                 target_type: TargetType,
                 operation: OperationType,
                 modifier: any,
                 condition: Optional[str] = None,
                 description: str = "") -> str:
        """
        Add a new global rule.
        
        Args:
            target_type: Type of events to affect ("gold", "item", "stat", "buff", "any")
            operation: How to modify ("multiply", "add", "set")
            modifier: Modifier value (will be converted to Decimal)
            condition: Optional condition (NOT implemented yet)
            description: Human-readable description
            
        Returns:
            Unique rule ID
            
        Example:
            >>> # All gold gains halved
            >>> engine.add_rule("gold", "multiply", "0.5", description="通货膨胀")
            
            >>> # All Strength gains +10
            >>> engine.add_rule("stat", "add", "10", description="力量祝福")
        """
        self._rule_id_counter += 1
        rule_id = f"rule_{self._rule_id_counter:03d}"
        
        rule = Rule(
            id=rule_id,
            target_type=target_type,
            operation=operation,
            modifier=Decimal(str(modifier)),
            condition=condition,
            description=description
        )
        
        self.active_rules.append(rule)
        return rule_id
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a rule by ID.
        
        Args:
            rule_id: Unique rule identifier
            
        Returns:
            True if removed, False if not found
        """
        for i, rule in enumerate(self.active_rules):
            if rule.id == rule_id:
                del self.active_rules[i]
                return True
        return False
    
    def clear_all_rules(self):
        """Remove all rules"""
        self.active_rules.clear()
        self._rule_id_counter = 0
    
    def list_active_rules(self) -> List[Dict]:
        """
        Get all active rules as dictionaries.
        
        Returns:
            List of rule dictionaries
        """
        return [{
            "id": rule.id,
            "target_type": rule.target_type,
            "operation": rule.operation,
            "modifier": str(rule.modifier),
            "condition": rule.condition,
            "description": rule.description
        } for rule in self.active_rules]
    
    def apply_rules(self, event: Dict, context: Optional[Dict] = None) -> Dict:
        """
        Apply all matching rules to an event.
        
        CRITICAL: This modifies the event BEFORE it's added to the ledger,
        allowing dynamic global modifiers.
        
        Args:
            event: Event dictionary to modify
            context: Optional context for conditional rules (chapter, word_count, etc.)
            
        Returns:
            Modified event dictionary
            
        Example:
            >>> rule_engine.add_rule("gold", "multiply", "0.5")
            >>> event = {"type": "gold", "value": "100"}
            >>> modified = rule_engine.apply_rules(event)
            >>> modified["value"]
            '50.0'
        """
        # Create a copy to avoid modifying original
        import copy
        modified_event = copy.deepcopy(event)
        
        # Find matching rules
        event_type = modified_event.get("type", "")
        matching_rules = [
            rule for rule in self.active_rules
            if rule.target_type == event_type or rule.target_type == "any"
        ]
        
        # Apply each matching rule
        for rule in matching_rules:
            # Check condition (if specified)
            if rule.condition:
                # TODO: Implement condition evaluation using simpleeval
                # For now, skip conditional rules
                continue
            
            # Apply modifier based on operation
            if "value" in modified_event:
                current_value = Decimal(str(modified_event["value"]))
                
                if rule.operation == "multiply":
                    new_value = current_value * rule.modifier
                elif rule.operation == "add":
                    new_value = current_value + rule.modifier
                elif rule.operation == "set":
                    new_value = rule.modifier
                else:
                    # Unknown operation, skip
                    continue
                
                modified_event["value"] = str(new_value)
                
                # Add metadata to track rule application
                if "applied_rules" not in modified_event:
                    modified_event["applied_rules"] = []
                modified_event["applied_rules"].append({
                    "rule_id": rule.id,
                    "description": rule.description,
                    "original_value": str(current_value),
                    "modified_value": str(new_value)
                })
        
        return modified_event
    
    def to_dict(self) -> List[Dict]:
        """
        Serialize rules to JSON-compatible format.
        
        Returns:
            List of rule dictionaries
        """
        return self.list_active_rules()
    
    def from_dict(self, data: List[Dict]):
        """
        Restore rules from serialized format.
        
        Args:
            data: List of rule dictionaries
        """
        self.clear_all_rules()
        
        for rule_dict in data:
            rule = Rule(
                id=rule_dict["id"],
                target_type=rule_dict["target_type"],
                operation=rule_dict["operation"],
                modifier=Decimal(rule_dict["modifier"]),
                condition=rule_dict.get("condition"),
                description=rule_dict.get("description", "")
            )
            
            self.active_rules.append(rule)
            
            # Update ID counter
            if rule.id.startswith("rule_"):
                try:
                    num = int(rule.id.split("_")[1])
                    self._rule_id_counter = max(self._rule_id_counter, num)
                except:
                    pass


if __name__ == "__main__":
    # Unit tests
    print("=" * 60)
    print("RuleEngine V1.1.2 - Unit Tests")
    print("=" * 60)
    
    engine = RuleEngine()
    
    # Test 1: Gold halving
    print("\nTest 1: Global Gold Halving")
    rule_id = engine.add_rule(
        target_type="gold",
        operation="multiply",
        modifier="0.5",
        description="通货膨胀: 金币收益减半"
    )
    print(f"  Added rule: {rule_id}")
    
    event = {"action": "gain", "type": "gold", "value": "100", "unit": "GP"}
    modified = engine.apply_rules(event)
    print(f"  Original: {event['value']} GP")
    print(f"  Modified: {modified['value']} GP")
    assert modified["value"] == "50.0", f"Expected 50.0, got {modified['value']}"
    print("  ✅ PASS\n")
    
    # Test 2: Stat addition
    print("Test 2: Global Strength Bonus")
    engine.clear_all_rules()
    engine.add_rule(
        target_type="stat",
        operation="add",
        modifier="10",
        description="力量祝福"
    )
    
    stat_event = {"action": "gain", "type": "stat", "name": "Strength", "value": "5"}
    modified_stat = engine.apply_rules(stat_event)
    print(f"  Original: +{stat_event['value']} Strength")
    print(f"  Modified: +{modified_stat['value']} Strength")
    assert modified_stat["value"] == "15", f"Expected 15, got {modified_stat['value']}"
    print("  ✅ PASS\n")
    
    # Test 3: Multiple rules
    print("Test 3: Multiple Rules")
    engine.clear_all_rules()
    engine.add_rule("gold", "multiply", "0.5", description="减半")
    engine.add_rule("gold", "add", "-10", description="税收")
    
    gold_event = {"type": "gold", "value": "100"}
    result = engine.apply_rules(gold_event)
    # 100 * 0.5 = 50, then 50 - 10 = 40
    print(f"  Original: {gold_event['value']}")
    print(f"  After rules: {result['value']}")
    print(f"  Applied rules: {result.get('applied_rules', [])}")
    assert result["value"] == "40", f"Expected 40, got {result['value']}"
    print("  ✅ PASS\n")
    
    # Test 4: Serialization
    print("Test 4: Serialization")
    serialized = engine.to_dict()
    print(f"  Serialized: {serialized}")
    
    engine2 = RuleEngine()
    engine2.from_dict(serialized)
    assert len(engine2.active_rules) == 2, "Should have 2 rules"
    print("  ✅ PASS\n")
    
    print("All tests passed! ✨")
