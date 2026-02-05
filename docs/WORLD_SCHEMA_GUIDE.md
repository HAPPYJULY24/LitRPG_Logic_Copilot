# Logic Copilot POC V1.0 - World Schema Guide

## Overview
V1.2 introduces the **Dynamic World Schema** system, replacing the hardcoded D&D-style currency (1 GP = 240 CP) with a flexible configuration system. This allows you to use Logic Copilot for any setting: Sci-Fi, Cultivation (Xianxia), Time Loops, or Modern.

## Quick Start (Presets)

The system comes with built-in presets. You can specify a preset when initializing the `LedgerEngine`, or via a configuration file.

### 1. Classic Fantasy (Default)
Standard D&D-style economy. Used automatically if no other schema is defined.
- **Currency**: "Gold"
- **Base Unit**: "CP"
- **Conversions**:
  - `1 GP` = `240 CP`
  - `1 SP` = `12 CP`
  - `1 CP` = `1 CP`

### 2. Time-Based
Perfect for "Time is Money" settings or lifespan tracking.
- **Currency**: "Time"
- **Base Unit**: "Minute"
- **Conversions**:
  - `1 Year` = `525,600 Minutes`
  - `1 Day` = `1,440 Minutes`
  - `1 Hour` = `60 Minutes`
- **Display**: "1 Year, 3 Days, 2 Hours" (Mixed Time Format)

### 3. Xianxia / Cultivation
Linear power scaling with scientific notation support.
- **Currency**: "Combat Power"
- **Base Unit**: "Power"
- **Conversions**: Linear (1 Power = 1 Power)
- **Display**: Scientific (e.g., "1.5E6 Power" or "150.0K Power")

### 4. Sci-Fi Credits
Metric-style digital currency.
- **Currency**: "Credits"
- **Base Unit**: "CR"
- **Conversions**:
  - `1 MCR` (Megacredit) = `1,000,000 CR`
  - `1 KCR` (Kilocredit) = `1,000 CR`

---

## Custom Schemas

You can define your own schema by creating a JSON file (e.g., `config/world_schema.json`).

### File Format

```json
{
  "currency_name": "Mana",
  "base_unit": "MP",
  "conversions": {
    "GMP": "1000000000",
    "MMP": "1000000",
    "KMP": "1000",
    "MP": "1"
  },
  "display_format": "standard"
}
```

### Display Formats
| Format | Description | Example |
|--------|-------------|---------|
| `standard` | Breakdown from largest to smallest unit | "10 GP, 5 SP" |
| `scientific` | Scientific notation for large numbers | "1.52E9 Power" |
| `time_mixed` | Like standard, but hides zero values and limits to top 3 units | "1 Year, 2 Days" |

---

## Usage in Code

### Loading a Schema
```python
from logic.world_schema import WorldSchema
from logic.ledger_engine import LedgerEngine

# Option A: Load from file
ledger = LedgerEngine(world_schema_path="config/my_schema.json")

# Option B: Use a preset
schema = WorldSchema.scifi_credits()
ledger = LedgerEngine(world_schema=schema)
```

### Backward Compatibility
Existing save files from V1.0/V1.1 will continue to work. If no schema is provided, the system defaults to **Classic Fantasy** rules (1 GP = 240 CP) to ensure your existing gold values remain correct.
