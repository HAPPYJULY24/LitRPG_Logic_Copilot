"""
WorldSchema - Dynamic Currency & Stat System Configuration (V1.2)
Replaces hardcoded D&D currency with configurable world schemas.

Supports:
- Classic Fantasy (GP/SP/CP)
- Time-based (Year/Day/Hour/Minute)
- Xianxia (Combat Power)
- Sci-Fi Credits
- Custom user-defined schemas
"""
from dataclasses import dataclass, asdict
from decimal import Decimal
from typing import Dict, Optional
import json
import os


@dataclass
class WorldSchema:
    """
    Defines currency/stat conversion system for a game world.
    
    Attributes:
        currency_name: Display name (e.g., "Gold", "Time", "Combat Power")
        base_unit: Base unit for storage (e.g., "CP", "Minute", "Power")
        conversions: Unit conversion rates {unit: multiplier_to_base}
        display_format: How to format values ("standard", "scientific", "time_mixed")
        
    Example:
        >>> schema = WorldSchema(
        ...     currency_name="Gold",
        ...     base_unit="CP",
        ...     conversions={"GP": Decimal("240"), "SP": Decimal("12"), "CP": Decimal("1")},
        ...     display_format="standard"
        ... )
    """
    currency_name: str
    base_unit: str
    conversions: Dict[str, Decimal]
    display_format: str = "standard"
    
    def __post_init__(self):
        """Ensure conversions are Decimal type"""
        # Convert string values to Decimal
        self.conversions = {
            unit: Decimal(str(rate)) if not isinstance(rate, Decimal) else rate
            for unit, rate in self.conversions.items()
        }
        
        # Validate base unit exists in conversions
        if self.base_unit not in self.conversions:
            raise ValueError(f"Base unit '{self.base_unit}' must be in conversions")
        
        # Validate base unit has rate of 1
        if self.conversions[self.base_unit] != Decimal("1"):
            raise ValueError(f"Base unit '{self.base_unit}' must have conversion rate of 1")
    
    def validate(self) -> bool:
        """
        Validate schema integrity.
        
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        # Check required fields
        if not self.currency_name:
            raise ValueError("currency_name cannot be empty")
        
        if not self.base_unit:
            raise ValueError("base_unit cannot be empty")
        
        if not self.conversions:
            raise ValueError("conversions cannot be empty")
        
        # Check display format
        valid_formats = ["standard", "scientific", "time_mixed", "decimal"]
        if self.display_format not in valid_formats:
            raise ValueError(f"display_format must be one of {valid_formats}")
        
        # Check all conversion rates are positive
        for unit, rate in self.conversions.items():
            if rate <= 0:
                raise ValueError(f"Conversion rate for '{unit}' must be positive, got {rate}")
        
        return True
    
    def save_to_file(self, path: str):
        """
        Save schema to JSON file.
        
        Args:
            path: File path to save to
            
        Example:
            >>> schema.save_to_file("config/world_schema.json")
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        
        # Convert to serializable format
        data = {
            "currency_name": self.currency_name,
            "base_unit": self.base_unit,
            "conversions": {unit: str(rate) for unit, rate in self.conversions.items()},
            "display_format": self.display_format
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, path: str) -> 'WorldSchema':
        """
        Load schema from JSON file.
        
        Args:
            path: File path to load from
            
        Returns:
            WorldSchema instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            
        Example:
            >>> schema = WorldSchema.load_from_file("config/world_schema.json")
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert string conversions back to Decimal
        conversions = {unit: Decimal(rate) for unit, rate in data['conversions'].items()}
        
        return cls(
            currency_name=data['currency_name'],
            base_unit=data['base_unit'],
            conversions=conversions,
            display_format=data.get('display_format', 'standard')
        )
    
    # ==================== Preset Factory Methods ====================
    
    @classmethod
    def classic_fantasy(cls) -> 'WorldSchema':
        """
        D&D 5e / Modern LitRPG style currency.
        
        1 Gold Piece (GP) = 10 Silver Pieces (SP) = 100 Copper Pieces (CP)
        
        Returns:
            WorldSchema for classic fantasy
            
        Example:
            >>> schema = WorldSchema.classic_fantasy()
            >>> # 10 GP = 1000 CP
        """
        return cls(
            currency_name="Gold",
            base_unit="CP",
            conversions={
                "GP": Decimal("100"),  # 1 GP = 100 CP
                "SP": Decimal("10"),   # 1 SP = 10 CP
                "CP": Decimal("1")     # Base unit
            },
            display_format="standard"
        )
    
    @classmethod
    def time_based(cls) -> 'WorldSchema':
        """
        Time as currency (e.g., lifespan, time loops).
        
        1 Year = 365 Days = 8760 Hours = 525600 Minutes
        
        Returns:
            WorldSchema for time-based currency
            
        Example:
            >>> schema = WorldSchema.time_based()
            >>> # "Gained 2 Hours" stored as 120 Minutes
        """
        return cls(
            currency_name="Time",
            base_unit="Minute",
            conversions={
                "Year": Decimal("525600"),    # 365 * 24 * 60
                "Month": Decimal("43800"),    # 30.5 * 24 * 60 (avg)
                "Week": Decimal("10080"),     # 7 * 24 * 60
                "Day": Decimal("1440"),       # 24 * 60
                "Hour": Decimal("60"),
                "Minute": Decimal("1")
            },
            display_format="time_mixed"
        )
    
    @classmethod
    def xianxia(cls) -> 'WorldSchema':
        """
        Xianxia/Cultivation Combat Power (linear scaling).
        
        No subdivisions, pure power level.
        
        Returns:
            WorldSchema for Xianxia combat power
            
        Example:
            >>> schema = WorldSchema.xianxia()
            >>> # Display: "1.5E6 Power"
        """
        return cls(
            currency_name="Combat Power",
            base_unit="Power",
            conversions={
                "Power": Decimal("1")  # Linear, no subdivisions
            },
            display_format="standard"
        )
    
    @classmethod
    def modern(cls) -> 'WorldSchema':
        """
        Modern currency (USD).
        
        1 Dollar ($) = 100 Cents (c)
        
        Returns:
            WorldSchema for modern currency
        """
        return cls(
            currency_name="Dollars",
            base_unit="Cent",
            conversions={
                "USD": Decimal("100"),     # $1 = 100 Cents
                "$": Decimal("100"),       # Alias
                "Cent": Decimal("1"),      # Base
                "c": Decimal("1")          # Alias
            },
            display_format="decimal"
        )
    
    @classmethod
    def scifi_credits(cls) -> 'WorldSchema':
        """
        Sci-Fi digital currency with metric prefixes.
        
        1 Megacredit = 1000 Kilocredits = 1,000,000 Credits
        
        Returns:
            WorldSchema for sci-fi credits
            
        Example:
            >>> schema = WorldSchema.scifi_credits()
            >>> # "10 KC" = 10,000 Credits
        """
        return cls(
            currency_name="Credits",
            base_unit="CR",
            conversions={
                "MCR": Decimal("1000000"),  # Megacredits
                "KCR": Decimal("1000"),     # Kilocredits
                "CR": Decimal("1")          # Credits (base)
            },
            display_format="standard"
        )
    
    @staticmethod
    def detect_schema_for_unit(unit: str) -> Optional[str]:
        """
        Detect which preset schema supports the given unit.
        
        Args:
            unit: The unit string (e.g., "$", "Year")
            
        Returns:
            Preset name ("modern", "time_based", etc.) or None
        """
        # Check Modern
        if unit in ["$", "USD", "Cent", "c"]:
            return "modern"
            
        # Check Sci-Fi
        if unit in ["CR", "KCR", "MCR", "Credit", "Credits"]:
            return "scifi_credits"
            
        # Check Time
        if unit in ["Year", "Month", "Week", "Day", "Hour", "Minute"]:
            return "time_based"
            
        # Check Xianxia
        if unit in ["Power", "Combat Power"]:
            return "xianxia"
            
        # Check Classic (as fallback match)
        if unit in ["GP", "SP", "CP", "Gold", "Silver", "Copper"]:
            return "classic_fantasy"
            
        return None

    @classmethod
    def custom(cls, name: str, base: str, units: Dict[str, str], format: str = "standard") -> 'WorldSchema':
        """
        Create custom schema from simple string values.
        
        Args:
            name: Currency name
            base: Base unit name
            units: Conversion rates as strings {unit: rate}
            format: Display format
            
        Returns:
            WorldSchema instance
            
        Example:
            >>> schema = WorldSchema.custom(
            ...     name="Mana",
            ...     base="MP",
            ...     units={"KMP": "1000", "MP": "1"},
            ...     format="standard"
            ... )
        """
        conversions = {unit: Decimal(rate) for unit, rate in units.items()}
        return cls(
            currency_name=name,
            base_unit=base,
            conversions=conversions,
            display_format=format
        )
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return (f"WorldSchema(currency='{self.currency_name}', "
                f"base='{self.base_unit}', "
                f"units={list(self.conversions.keys())}, "
                f"format='{self.display_format}')")


# ==================== Module-Level Functions ====================

def get_default_schema() -> WorldSchema:
    """
    Get default schema (Classic Fantasy for V1.1 backward compatibility).
    
    Returns:
        Default WorldSchema
    """
    return WorldSchema.classic_fantasy()


def load_or_default(path: Optional[str] = None) -> WorldSchema:
    """
    Load schema from file, or return default if not found.
    
    Args:
        path: Optional path to schema file
        
    Returns:
        Loaded schema or default (Classic Fantasy)
        
    Example:
        >>> schema = load_or_default("config/world_schema.json")
        >>> # If file exists, loads it; otherwise returns Classic Fantasy
    """
    if path and os.path.exists(path):
        try:
            return WorldSchema.load_from_file(path)
        except Exception as e:
            print(f"Warning: Failed to load schema from {path}: {e}")
            print("Falling back to Classic Fantasy preset")
            return get_default_schema()
    else:
        return get_default_schema()


# ==================== Self-Test ====================

if __name__ == "__main__":
    print("=== WorldSchema Self-Test ===\n")
    
    # Test 1: Classic Fantasy
    print("Test 1: Classic Fantasy Preset")
    fantasy = WorldSchema.classic_fantasy()
    print(f"  {fantasy}")
    assert fantasy.base_unit == "CP"
    assert fantasy.conversions["GP"] == Decimal("100")
    print("  ✅ PASS\n")
    
    # Test 2: Time-Based
    print("Test 2: Time-Based Preset")
    time_schema = WorldSchema.time_based()
    print(f"  {time_schema}")
    assert time_schema.base_unit == "Minute"
    assert time_schema.conversions["Hour"] == Decimal("60")
    assert time_schema.conversions["Day"] == Decimal("1440")
    print("  ✅ PASS\n")
    
    # Test 3: Save/Load Roundtrip
    print("Test 3: Save/Load Roundtrip")
    test_path = "test_schema.json"
    fantasy.save_to_file(test_path)
    loaded = WorldSchema.load_from_file(test_path)
    assert loaded.currency_name == fantasy.currency_name
    assert loaded.conversions == fantasy.conversions
    os.remove(test_path)
    print("  ✅ PASS\n")
    
    # Test 4: Custom Schema
    print("Test 4: Custom Schema")
    mana = WorldSchema.custom(
        name="Mana",
        base="MP",
        units={"KMP": "1000", "MP": "1"},
        format="standard"
    )
    print(f"  {mana}")
    assert mana.conversions["KMP"] == Decimal("1000")
    print("  ✅ PASS\n")
    
    # Test 5: Xianxia
    print("Test 5: Xianxia Preset")
    xianxia = WorldSchema.xianxia()
    print(f"  {xianxia}")
    assert xianxia.display_format == "scientific"
    print("  ✅ PASS\n")
    
    # Test 6: Validation
    print("Test 6: Validation")
    try:
        invalid = WorldSchema(
            currency_name="Test",
            base_unit="Invalid",  # Not in conversions
            conversions={"CP": Decimal("1")},
            display_format="standard"
        )
        print("  ❌ FAIL: Should have raised ValueError")
    except ValueError as e:
        print(f"  ✅ PASS: Caught validation error: {e}\n")
    
    print("All tests passed! ✨")
