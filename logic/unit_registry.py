"""
UnitRegistry - Dynamic Currency Conversion System (V1.2)
Now uses WorldSchema for configurable currency systems.

V1.2 Changes:
- Removed hardcoded D&D conversions
- Accepts WorldSchema parameter
- Supports multiple display formats (standard, scientific, time_mixed)
- Backward compatible (defaults to Classic Fantasy)
"""
from decimal import Decimal, getcontext
from typing import Dict, Union, Optional
from logic.world_schema import WorldSchema, get_default_schema

# Set high precision for large number support
getcontext().prec = 50


class UnitRegistry:
    """
    Manages currency conversions with arbitrary precision using WorldSchema.
    
    V1.2: Now schema-driven instead of hardcoded.
    
    Example:
        # Classic Fantasy (default)
        >>> registry = UnitRegistry()
        >>> registry.to_base("10", "GP")
        Decimal('2400')  # 10 GP = 2400 CP
        
        # Time-based
        >>> schema = WorldSchema.time_based()
        >>> registry = UnitRegistry(schema)
        >>> registry.to_base("2", "Hour")
        Decimal('120')  # 2 Hours = 120 Minutes
    """
    
    def __init__(self, schema: Optional[WorldSchema] = None):
        """
        Initialize with a world schema.
        
        Args:
            schema: WorldSchema instance (defaults to Classic Fantasy)
            
        Example:
            >>> registry = UnitRegistry()  # Classic Fantasy
            >>> registry = UnitRegistry(WorldSchema.time_based())
        """
        self.schema = schema or get_default_schema()
        self.schema.validate()  # Ensure schema is valid
        
        # Expose conversions for backward compatibility
        self.rules = self.schema.conversions
        self.base_unit = self.schema.base_unit
    
    def register_unit(self, unit_name: str, conversion_rate: Union[str, int, Decimal]):
        """
        Register a new currency unit (V1.2: Updates schema).
        
        Args:
            unit_name: Short code (e.g., "EP" for Electrum)
            conversion_rate: How many base units = 1 of this unit
                            (e.g., "50" means 1 EP = 50 CP)
        
        Example:
            >>> registry.register_unit("EP", "50")
        """
        self.schema.conversions[unit_name] = Decimal(str(conversion_rate))
        self.rules = self.schema.conversions  # Update reference
    
    def to_base(self, value: Union[str, int, Decimal], unit: str) -> Decimal:
        """
        Convert any unit to base unit.
        
        Args:
            value: Amount in source unit
            unit: Unit code (from schema)
            
        Returns:
            Decimal value in base unit
            
        Example:
            >>> registry.to_base("10", "GP")
            Decimal('2400')  # Classic Fantasy: 10 GP = 2400 CP
        """
        # CLEANUP: Remove commas first
        clean_value = str(value).replace(',', '')
        decimal_value = Decimal(clean_value)

        if unit not in self.schema.conversions:
            # AUTO-DISCOVERY FALLBACK (V1.3)
            # Instead of failing, we treat unknown units as 1:1 with base unit
            # This allows "Spirit Stones" or arbitrary units to flow through without crashing
            print(f"WARNING: Unknown unit '{unit}', treating as 1:1 base unit.")
            return decimal_value
        
        conversion_rate = self.schema.conversions[unit]
        return decimal_value * conversion_rate
    
    def from_base(self, base_value: Union[str, int, Decimal], target_unit: Optional[str] = None) -> Union[Decimal, Dict[str, Decimal]]:
        """
        Convert base unit to display format.
        """
        decimal_value = Decimal(str(base_value))
        
        # If specific unit requested
        if target_unit:
            if target_unit not in self.schema.conversions:
                # FALLBACK: Unknown unit = 1:1 conversion
                return decimal_value
            return decimal_value / self.schema.conversions[target_unit]
        
        # Breakdown logic
        result = {}
        remaining = decimal_value
        
        # Sort units by value (descending)
        sorted_units = sorted(self.schema.conversions.items(), key=lambda x: x[1], reverse=True)
        
        # V1.2.6 Optimization: Deduplicate conversion rates to prevent splitting (e.g. USD vs $)
        processed_rates = set()
        
        for unit, rate in sorted_units:
            if rate in processed_rates and unit != self.base_unit:
                # Skip duplicate alias (unless it's the base unit, ensuring consistency)
                continue
            
            # For exact matches (e.g. rate 1), ensure we use the base_unit if multiple exist
            if rate == Decimal("1") and unit != self.base_unit:
                 continue

            if unit == self.base_unit:
                result[unit] = remaining
                processed_rates.add(rate)
            else:
                count = remaining // rate
                # Only add if count > 0 or it's the largest unit (for display structure) - actually just store non-zero
                # But to maintain full breakdown we store it, loop below decides display.
                if count > 0:
                    result[unit] = count
                    remaining -= count * rate
                    processed_rates.add(rate)
        
        # Ensure base unit catches remaining if not processed? 
        # The logic above ensures base_unit (rate 1) is always hit last if implicit 1.
        # But if user has weird schema, safeguard:
        if remaining > 0 and self.base_unit not in result:
             result[self.base_unit] = remaining
             
        return result

    def format_display(self, base_value: Union[str, int, Decimal]) -> str:
        """
        Format base unit into human-readable string.
        """
        decimal_value = Decimal(str(base_value))
        
        if self.schema.display_format == "scientific":
            return self._format_scientific(decimal_value)
        elif self.schema.display_format == "time_mixed":
            return self._format_time_mixed(decimal_value)
        elif self.schema.display_format == "decimal":
            return self._format_decimal(decimal_value)
        else:  # standard
            return self._format_standard(decimal_value)
    
    def _format_decimal(self, base_value: Decimal) -> str:
        """Format as decimal (e.g., "$12.50"). Uses largest unit > 1."""
        # Find primary unit (largest value)
        # We prefer symbols if available (len=1)
        sorted_units = sorted(self.schema.conversions.items(), key=lambda x: x[1], reverse=True)
        
        major_unit = None
        major_rate = Decimal("1")
        
        # Heuristic: Find largest rate unit. If simplified alias exists ('$'), prefer it.
        candidates = []
        max_rate = Decimal("-1")
        
        for unit, rate in sorted_units:
            if rate > max_rate:
                max_rate = rate
                candidates = [unit]
            elif rate == max_rate:
                candidates.append(unit)
        
        # Pick best candidate (Symbol preferred)
        major_unit = candidates[0]
        for c in candidates:
            if len(c) == 1: # Prefer '$' over 'USD'
                major_unit = c
                break
        
        major_rate = self.schema.conversions[major_unit]
        val = float(base_value) / float(major_rate)
        
        # Formatting
        str_val = f"{val:,.2f}"
        if str_val.endswith(".00"):
            str_val = str_val[:-3] # integer look if cleaner? No User wants 12.40. Standard float formatting.
            pass
            
        # Prefix symbol if len=1
        if len(major_unit) == 1:
             return f"{major_unit}{val:,.2f}"
        else:
             return f"{val:,.2f} {major_unit}"

    def _format_standard(self, base_value: Decimal) -> str:
        """Format as standard breakdown (e.g., "11 GP, 50 CP"). Hides zeros."""
        breakdown = self.from_base(base_value)
        
        sorted_units = sorted(breakdown.items(), 
                            key=lambda x: self.schema.conversions[x[0]], 
                            reverse=True)
        
        parts = []
        for unit, value in sorted_units:
            if value > 0:
                parts.append(f"{int(value)} {unit}")
                
        if not parts:
            return f"0 {self.base_unit}"
            
        return ", ".join(parts)    
    def _format_scientific(self, base_value: Decimal) -> str:
        """Format as scientific notation (e.g., "1.5E6 Power")"""
        # Use Python's scientific notation
        if base_value >= 1000000 or base_value <= -1000000:
            # Format in scientific notation
            formatted = f"{float(base_value):.2E}"
        elif base_value >= 1000 or base_value <= -1000:
            # Use K notation
            formatted = f"{float(base_value / 1000):.1f}K"
        else:
            formatted = str(int(base_value))
        
        return f"{formatted} {self.base_unit}"
    
    def _format_time_mixed(self, base_value: Decimal) -> str:
        """Format as mixed time units (e.g., "2 Years, 15 Days, 3 Hours")"""
        breakdown = self.from_base(base_value)
        
        # Sort by unit value (Year first, Minute last)
        sorted_units = sorted(breakdown.items(), 
                            key=lambda x: self.schema.conversions[x[0]], 
                            reverse=True)
        
        # Only show non-zero values
        parts = [f"{int(value)} {unit}" for unit, value in sorted_units if value > 0]
        
        if not parts:
            return f"0 {self.base_unit}"
        
        # Limit to top 3 units for readability
        return ", ".join(parts[:3])
    
    def format_value(self, base_value: Union[str, int, Decimal], target_unit: Optional[str] = None) -> str:
        """
        Format value for display (V1.2: wrapper for format_display).
        
        Args:
            base_value: Amount in base unit
            target_unit: Optional specific unit to display in
            
        Returns:
            Formatted string
            
        Example:
            >>> registry.format_value("2400")
            "10 GP, 0 SP, 0 CP"
            
            >>> registry.format_value("2400", "GP")
            "10 GP"
        """
        if target_unit:
            converted = self.from_base(base_value, target_unit)
            return f"{int(converted)} {target_unit}"
        else:
            return self.format_display(base_value)


if __name__ == "__main__":
    # Unit tests
    print("=== UnitRegistry V1.2 Unit Tests ===\n")
    
    # Test 1: Classic Fantasy (Backward Compatibility)
    print("Test 1: Classic Fantasy (Default)")
    registry = UnitRegistry()
    cp_value = registry.to_base("10", "GP")
    print(f"  10 GP -> {cp_value} CP")
    assert cp_value == Decimal("1000"), f"Expected 1000, got {cp_value}"
    print("  PASS\n")
    
    # Test 2: Time-Based Schema
    print("Test 2: Time-Based Schema")
    time_registry = UnitRegistry(WorldSchema.time_based())
    minutes = time_registry.to_base("2", "Hour")
    print(f"  2 Hours -> {minutes} Minutes")
    assert minutes == Decimal("120"), f"Expected 120, got {minutes}"
    formatted = time_registry.format_display(minutes)
    print(f"  Formatted: {formatted}")
    print("  PASS\n")
    
    # Test 3: Xianxia Schema with Scientific Format
    print("Test 3: Xianxia Schema (Scientific)")
    xianxia_registry = UnitRegistry(WorldSchema.xianxia())
    power = Decimal("1500000")
    formatted = xianxia_registry.format_display(power)
    print(f"  1500000 Power -> {formatted}")
    assert "E" in formatted.upper() or "K" in formatted.upper()
    print("  PASS\n")
    
    # Test 4: Mixed Input Parsing
    print("Test 4: Mixed Input Parsing")
    mixed_total = registry.parse_mixed_input("2 GP 15 SP 3 CP")
    print(f"  '2 GP 15 SP 3 CP' -> {mixed_total} CP")
    expected = Decimal("2") * Decimal("240") + Decimal("15") * Decimal("12") + Decimal("3")
    assert mixed_total == expected, f"Expected {expected}, got {mixed_total}"
    print("  PASS\n")
    
    # Test 5: Sci-Fi Credits
    print("Test 5: Sci-Fi Credits")
    scifi_registry = UnitRegistry(WorldSchema.scifi_credits())
    credits = scifi_registry.to_base("10", "KCR")
    print(f"  10 KCR -> {credits} CR")
    assert credits == Decimal("10000"), f"Expected 10000, got {credits}"
    print("  PASS\n")
    
    print("All tests passed!")
