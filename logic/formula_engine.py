"""
FormulaEngine - Computed Attributes with Dependency Tracking
Safely evaluates formulas like "Attack = Strength * 2 + Level" using simpleeval
"""
from decimal import Decimal
from typing import Dict, Set, Optional
from simpleeval import simple_eval, DEFAULT_FUNCTIONS, DEFAULT_NAMES, DEFAULT_OPERATORS
import re
import ast
import operator


class FormulaEngine:
    """
    Manages computed attributes with automatic dependency tracking.
    
    CRITICAL: All values are Decimal to avoid float/Decimal type mixing errors.
    
    Example:
        engine = FormulaEngine()
        engine.register_formula("Attack", "Strength * 2 + Level")
        
        # When Strength changes, Attack is automatically marked dirty
        engine.mark_dirty("Strength")
        
        # Recalculate with current stats
        attack = engine.recalculate("Attack", {"Strength": 50, "Level": 10})
        # Returns Decimal('110')
    """
    
    def __init__(self):
        """Initialize formula engine with Decimal-safe evaluation context"""
        self.formulas: Dict[str, str] = {}  # {field_name: expression}
        self.dirty_flags: Dict[str, bool] = {}  # {field_name: is_dirty}
        self.dependencies: Dict[str, Set[str]] = {}  # {field: set of fields it depends on}
        
        # CRITICAL: Custom evaluation functions that return Decimal
        # This prevents TypeError when mixing Decimal with int/float
        self.eval_functions = DEFAULT_FUNCTIONS.copy()
        
        # V1.3 SECURITY FIX: Safe Power Function (DoS Prevention)
        def safe_pow(x, y):
            """Limit exponentiation to prevent CPU exhaustion (DoS)"""
            base = Decimal(str(x))
            exp = Decimal(str(y))
            if exp > 100:
                raise ValueError(f"Exponent {exp} exceeds safety limit (100)")
            return base ** exp

        self.eval_functions.update({
            'abs': lambda x: abs(Decimal(str(x))),
            'max': lambda *args: max(Decimal(str(x)) for x in args),
            'min': lambda *args: min(Decimal(str(x)) for x in args),
            'int': lambda x: Decimal(str(int(x))),
            'round': lambda x, n=0: Decimal(str(x)).quantize(Decimal(10) ** -n),
            'pow': safe_pow,  # Override default pow function
        })
        
        # V1.3 SECURITY FIX: Override Operator Mappings for '**'
        # simpleeval uses operators map for 'a ** b', NOT the function 'pow'
        self.eval_operators = DEFAULT_OPERATORS.copy()
        
        # V1.4 TYPE SAFETY FIX: Override all arithmetic operators to force Decimal
        # This prevents "Decimal vs Float" errors when users input "0.5"
        def safe_op_wrapper(op_func):
            def wrapper(a, b):
                return op_func(Decimal(str(a)), Decimal(str(b)))
            return wrapper
            
        # V1.6 HARDENING: Zero-Safe Division
        # V1.6 HARDENING: Zero-Safe Division (Modified for V1.0 Release Error Feedback)
        def safe_div(a, b):
            try:
                dec_a = Decimal(str(a))
                dec_b = Decimal(str(b))
                
                if dec_b == 0:
                    raise ZeroDivisionError("Division by zero")
                    
                return dec_a / dec_b
            except ZeroDivisionError:
                raise
            except Exception:
                return Decimal("0")

        self.eval_operators[ast.Pow] = safe_pow
        self.eval_operators[ast.Add] = safe_op_wrapper(operator.add)
        self.eval_operators[ast.Sub] = safe_op_wrapper(operator.sub)
        self.eval_operators[ast.Mult] = safe_op_wrapper(operator.mul)
        self.eval_operators[ast.Div] = safe_div # Use safe_div for /
        self.eval_operators[ast.FloorDiv] = safe_div # Use safe_div for //
        self.eval_operators[ast.Mod] = safe_op_wrapper(operator.mod)
        
        # Comparison operators too
        self.eval_operators[ast.Eq] = safe_op_wrapper(operator.eq)
        self.eval_operators[ast.NotEq] = safe_op_wrapper(operator.ne)
        self.eval_operators[ast.Lt] = safe_op_wrapper(operator.lt)
        self.eval_operators[ast.LtE] = safe_op_wrapper(operator.le)
        self.eval_operators[ast.Gt] = safe_op_wrapper(operator.gt)
        self.eval_operators[ast.GtE] = safe_op_wrapper(operator.ge)
        
        # No custom names needed (variables come from context)
        self.eval_names = DEFAULT_NAMES.copy()
    
    def register_formula(self, field_name: str, expression: str):
        """
        Register a computed field with its formula.
        
        Args:
            field_name: Name of the computed stat (e.g., "Attack")
            expression: Mathematical expression (e.g., "Strength * 2 + Level")
            
        Raises:
            ValueError: If formula contains circular dependencies
        """
        self.formulas[field_name] = expression
        self.dirty_flags[field_name] = True
        
        # Extract dependencies (variables used in expression)
        self.dependencies[field_name] = self._extract_dependencies(expression)
        
        # Check for circular dependencies
        try:
            self._detect_cycles(field_name)
        except ValueError as e:
            # Rollback registration
            del self.formulas[field_name]
            del self.dirty_flags[field_name]
            del self.dependencies[field_name]
            raise e
    
    def _extract_dependencies(self, expression: str) -> Set[str]:
        """
        Extract variable names from formula expression.
        
        Args:
            expression: Formula string
            
        Returns:
            Set of variable names used in the formula
            
        Example:
            >>> _extract_dependencies("Strength * 2 + Level")
            {'Strength', 'Level'}
        """
        # Match valid Python identifiers (variable names)
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        matches = re.findall(pattern, expression)
        
        # Filter out function names and keywords
        keywords = {'abs', 'max', 'min', 'int', 'round', 'True', 'False', 'None', 'if', 'else', 'and', 'or', 'not', 'in', 'is'}
        dependencies = {m for m in matches if m not in keywords}
        
        return dependencies
    
    def _detect_cycles(self, start_field: str, visited: Optional[Set[str]] = None, path: Optional[list] = None):
        """
        Detect circular dependencies in formula graph.
        
        Args:
            start_field: Field to check from
            visited: Set of already visited fields (for recursion)
            path: Current dependency path (for error message)
            
        Raises:
            ValueError: If circular dependency detected
        """
        if visited is None:
            visited = set()
        if path is None:
            path = []
        
        if start_field in visited:
            # Found a cycle
            cycle_path = ' → '.join(path + [start_field])
            raise ValueError(f"Circular dependency detected: {cycle_path}")
        
        if start_field not in self.dependencies:
            # Base field (not a computed field)
            return
        
        visited.add(start_field)
        path.append(start_field)
        
        # Check all dependencies recursively
        for dep_field in self.dependencies[start_field]:
            self._detect_cycles(dep_field, visited.copy(), path.copy())
    
    def mark_dirty(self, base_field: str):
        """
        Mark all formulas that depend on this field as dirty.
        
        Args:
            base_field: Name of the base stat that changed
            
        Example:
            # When Strength changes from 50 → 60
            engine.mark_dirty("Strength")
            # -> Attack is now marked dirty and needs recalculation
        """
        for formula_name, deps in self.dependencies.items():
            if base_field in deps:
                self.dirty_flags[formula_name] = True
    
    def recalculate(self, field_name: str, context: Dict[str, any]) -> Decimal:
        """
        Safely evaluate a formula with current stat values.
        
        CRITICAL: All context values are converted to Decimal to avoid type mixing.
        
        Args:
            field_name: Name of the computed stat
            context: Dictionary of current base stats (e.g., {"Strength": 50, "Level": 10})
            
        Returns:
            Computed value as Decimal
            
        Raises:
            ValueError: If formula not registered
            KeyError: If required stat missing from context
            
        Example:
            >>> engine.register_formula("Attack", "Strength * 2 + Level")
            >>> engine.recalculate("Attack", {"Strength": 50, "Level": 10})
            Decimal('110')
        """
        if field_name not in self.formulas:
            raise ValueError(f"Unknown formula: {field_name}. Registered formulas: {list(self.formulas.keys())}")
        
        expression = self.formulas[field_name]
        
        # CRITICAL: Convert all context values to Decimal
        # This prevents "TypeError: unsupported operand type(s)" when mixing types
        decimal_context = {}
        for key, value in context.items():
            try:
                decimal_context[key] = Decimal(str(value))
            except Exception as e:
                raise ValueError(f"Cannot convert {key}={value} to Decimal: {e}")
        
        # Check for missing dependencies
        missing_deps = self.dependencies[field_name] - set(decimal_context.keys())
        if missing_deps:
            raise KeyError(f"Missing required stats for {field_name}: {missing_deps}")
        
        # Evaluate with type-safe functions
        try:
            result = simple_eval(
                expression,
                names=decimal_context,
                functions=self.eval_functions,
                operators=self.eval_operators  # V1.3: Use safe operators
            )
            
            # CRITICAL: Force result to Decimal (simpleeval may return int/float)
            final_result = Decimal(str(result))
            
            # Mark as clean after successful calculation
            self.dirty_flags[field_name] = False
            
            return final_result
            
        except Exception as e:
            raise ValueError(f"Error evaluating formula '{field_name} = {expression}': {e}")
    
    def recalculate_all_dirty(self, context: Dict[str, any]) -> Dict[str, Decimal]:
        """
        Recalculate all formulas marked as dirty.
        
        Args:
            context: Current base stats
            
        Returns:
            Dictionary of {field_name: calculated_value} for dirty fields
        """
        results = {}
        for field_name in self.formulas.keys():
            if self.dirty_flags.get(field_name, True):
                results[field_name] = self.recalculate(field_name, context)
        return results
    
    def get_all_computed_stats(self, context: Dict[str, any]) -> Dict[str, Decimal]:
        """
        Calculate all registered formulas regardless of dirty status.
        
        Args:
            context: Current base stats
            \r\n        Returns:
            Dictionary of {field_name: calculated_value}
        """
        results = {}
        for field_name in self.formulas.keys():
            results[field_name] = self.recalculate(field_name, context)
        return results
    
    def clear_all_formulas(self):
        """
        Remove all registered formulas (V1.1.2).
        
        Useful for test cleanup to prevent formula contamination
        between test scenarios.
        
        Example:
            >>> engine.register_formula("Attack", "Strength * 2")
            >>> engine.clear_all_formulas()
            >>> len(engine.formulas)
            0
        """
        self.formulas.clear()
        self.dirty_flags.clear()
        self.dependencies.clear()



if __name__ == "__main__":
    # Unit tests
    print("=== FormulaEngine Unit Tests ===\n")
    
    engine = FormulaEngine()
    
    # Test 1: Basic formula evaluation
    print("Test 1: Basic Formula Evaluation")
    engine.register_formula("Attack", "Strength * 2 + Level")
    stats = {"Strength": Decimal("50"), "Level": Decimal("10")}
    attack = engine.recalculate("Attack", stats)
    print(f"  Attack = Strength * 2 + Level")
    print(f"  With Strength=50, Level=10 → {attack}")
    assert attack == Decimal("110"), f"Expected 110, got {attack}"
    print("  ✅ PASS\n")
    
    # Test 2: Decimal/Float type mixing (CRITICAL)
    print("Test 2: Division Formula (Type Safety Test)")
    engine.register_formula("AvgDamage", "Attack / Level")
    avg = engine.recalculate("AvgDamage", {"Attack": Decimal("100"), "Level": Decimal("5")})
    print(f"  AvgDamage = Attack / Level")
    print(f"  With Attack=100, Level=5 → {avg}")
    assert avg == Decimal("20"), f"Expected 20, got {avg}"
    print("  ✅ PASS (No TypeError!)\n")
    
    # Test 3: Dependency tracking
    print("Test 3: Dependency Tracking")
    engine.mark_dirty("Strength")
    print(f"  After marking 'Strength' dirty:")
    print(f"    Attack dirty? {engine.dirty_flags['Attack']}")
    assert engine.dirty_flags['Attack'] == True, "Attack should be marked dirty"
    print("  ✅ PASS\n")
    
    # Test 4: Circular dependency detection
    print("Test 4: Circular Dependency Detection")
    try:
        engine.register_formula("A", "B * 2")
        engine.register_formula("B", "A / 2")
        print("  ❌ FAIL: Should have detected cycle")
        assert False
    except ValueError as e:
        print(f"  Caught: {e}")
        print("  ✅ PASS\n")
    
    # Test 5: Complex formula with functions
    print("Test 5: Complex Formula with Functions")
    engine.register_formula("MaxHP", "max(Strength * 10, Level * 50)")
    hp = engine.recalculate("MaxHP", {"Strength": Decimal("8"), "Level": Decimal("3")})
    print(f"  MaxHP = max(Strength * 10, Level * 50)")
    print(f"  With Strength=8, Level=3 → {hp}")
    assert hp == Decimal("150"), f"Expected 150, got {hp}"
    print("  ✅ PASS\n")
    
    # Test 6: Large number precision
    print("Test 6: Large Number Precision (10^20)")
    huge_str = Decimal("10") ** 20
    engine.register_formula("Power", "Strength * 2")
    power = engine.recalculate("Power", {"Strength": huge_str})
    expected = huge_str * 2
    print(f"  With Strength=10^20 → Power={power}")
    assert power == expected, "Precision loss detected"
    print("  ✅ PASS\n")
    
    print("All tests passed! ✨")
