"""
TemporalState - Time-limited Buff and Status Effect Management
Handles buffs with expiry based on chapter count, word count, or real time
"""
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass, field


ExpiryType = Literal["chapter", "word_count", "time", "permanent"]


@dataclass
class Buff:
    """
    Represents a temporary status effect.
    
    Attributes:
        id: Unique identifier
        name: Display name (e.g., "祝福", "中毒")
        effects: Stat modifiers {stat_name: modifier_value}
        expiry_type: How the buff expires (chapter/word_count/time/permanent)
        expiry_value: When it expires (Chapter 5 / 1000 words / ISO timestamp)
        description: Optional flavor text
    """
    id: str
    name: str
    effects: Dict[str, Decimal]
    expiry_type: ExpiryType
    expiry_value: Optional[any] = None
    description: str = ""
    
    def __post_init__(self):
        """Validate and convert effect values to Decimal"""
        # Ensure all effect values are Decimal
        self.effects = {k: Decimal(str(v)) for k, v in self.effects.items()}


class TemporalState:
    """
    Manages time-limited buffs and status effects.
    
    CRITICAL: Buff expiry must be checked DURING event replay,
    not after, to maintain correct temporal context.
    """
    
    def __init__(self):
        """Initialize with empty buff list"""
        self.active_buffs: List[Buff] = []
        self._buff_id_counter = 0
    
    def add_buff(self, 
                 name: str,
                 effects: Dict[str, any],
                 expiry_type: ExpiryType,
                 expiry_value: Optional[any] = None,
                 description: str = "") -> str:
        """
        Add a new buff to active buffs.
        
        Args:
            name: Buff display name
            effects: Stat modifiers {stat: value}, e.g., {"Attack": 10, "Defense": 5}
            expiry_type: When buff expires ("chapter", "word_count", "time", "permanent")
            expiry_value: Expiry threshold (Chapter number / word count / ISO timestamp)
            description: Optional flavor text
            
        Returns:
            Unique buff ID
            
        Example:
            >>> temporal.add_buff(
            ...     name="神圣祝福",
            ...     effects={"Attack": 10, "Defense": 5},
            ...     expiry_type="chapter",
            ...     expiry_value=5  # Expires at start of Chapter 5
            ... )
            "buff_001"
        """
        # Validate expiry configuration
        if expiry_type != "permanent" and expiry_value is None:
            raise ValueError(f"expiry_value required for expiry_type='{expiry_type}'")
        
        # Generate unique ID
        self._buff_id_counter += 1
        buff_id = f"buff_{self._buff_id_counter:03d}"
        
        # Create buff
        buff = Buff(
            id=buff_id,
            name=name,
            effects=effects,
            expiry_type=expiry_type,
            expiry_value=expiry_value,
            description=description
        )
        
        self.active_buffs.append(buff)
        return buff_id
    
    def remove_buff(self, buff_id: str) -> bool:
        """
        Remove a buff by ID.
        
        Args:
            buff_id: Unique buff identifier
            
        Returns:
            True if buff was found and removed, False otherwise
        """
        for i, buff in enumerate(self.active_buffs):
            if buff.id == buff_id:
                del self.active_buffs[i]
                return True
        return False
    
    def check_expiry(self, 
                     current_chapter: int = 0,
                     word_count: int = 0,
                     timestamp: Optional[str] = None) -> List[str]:
        """
        Check and remove expired buffs based on current temporal context.
        
        CRITICAL: This must be called DURING event replay, not after,
        to ensure buffs expire at the correct moment.
        
        Args:
            current_chapter: Current chapter number
            word_count: Cumulative word count
            timestamp: Current time (ISO 8601 format)
            
        Returns:
            List of expired buff IDs
            
        Example:
            >>> temporal.add_buff("Poison", {"HP": -5}, "chapter", 3)
            >>> temporal.check_expiry(current_chapter=4)
            ['buff_001']  # Poison expired at Chapter 4
        """
        expired_ids = []
        buffs_to_keep = []
        
        for buff in self.active_buffs:
            is_expired = False
            
            if buff.expiry_type == "chapter":
                # Expires when chapter reaches threshold
                if current_chapter >= buff.expiry_value:
                    is_expired = True
                    
            elif buff.expiry_type == "word_count":
                # Expires when word count reaches threshold
                if word_count >= buff.expiry_value:
                    is_expired = True
                    
            elif buff.expiry_type == "time":
                # Expires when timestamp reaches threshold
                if timestamp:
                    try:
                        current_time = datetime.fromisoformat(timestamp)
                        expiry_time = datetime.fromisoformat(buff.expiry_value)
                        if current_time >= expiry_time:
                            is_expired = True
                    except Exception:
                        # Invalid timestamp format, keep buff
                        pass
                        
            elif buff.expiry_type == "permanent":
                # Never expires
                is_expired = False
            
            if is_expired:
                expired_ids.append(buff.id)
            else:
                buffs_to_keep.append(buff)
        
        # Update active buffs list
        self.active_buffs = buffs_to_keep
        
        return expired_ids
    
    def get_active_effects(self) -> Dict[str, Decimal]:
        """
        Aggregate all active buff effects into a single modifier dict.
        
        Returns:
            Dictionary of {stat_name: total_modifier}
            
        Example:
            >>> temporal.add_buff("Buff1", {"Attack": 10}, "permanent")
            >>> temporal.add_buff("Buff2", {"Attack": 5, "Defense": 3}, "permanent")
            >>> temporal.get_active_effects()
            {'Attack': Decimal('15'), 'Defense': Decimal('3')}
        """
        aggregated = {}
        
        for buff in self.active_buffs:
            for stat, value in buff.effects.items():
                if stat in aggregated:
                    aggregated[stat] += value
                else:
                    aggregated[stat] = value
        
        return aggregated
    
    def get_buffs_by_stat(self, stat_name: str) -> List[Buff]:
        """
        Get all buffs that affect a specific stat.
        
        Args:
            stat_name: Name of the stat
            
        Returns:
            List of buffs affecting this stat
        """
        return [buff for buff in self.active_buffs if stat_name in buff.effects]
    
    def get_buff_by_id(self, buff_id: str) -> Optional[Buff]:
        """
        Retrieve a buff by its ID.
        
        Args:
            buff_id: Unique buff identifier
            
        Returns:
            Buff object if found, None otherwise
        """
        for buff in self.active_buffs:
            if buff.id == buff_id:
                return buff
        return None
    
    def clear_all(self):
        """Remove all buffs (useful for game reset)"""
        self.active_buffs.clear()
        self._buff_id_counter = 0
    
    def to_dict(self) -> List[Dict]:
        """
        Serialize active buffs to JSON-compatible format.
        
        Returns:
            List of buff dictionaries
        """
        return [
            {
                "id": buff.id,
                "name": buff.name,
                "effects": {k: str(v) for k, v in buff.effects.items()},
                "expiry_type": buff.expiry_type,
                "expiry_value": buff.expiry_value,
                "description": buff.description
            }
            for buff in self.active_buffs
        ]
    
    def from_dict(self, data: List[Dict]):
        """
        Restore buffs from serialized format.
        
        Args:
            data: List of buff dictionaries
        """
        self.active_buffs.clear()
        
        for buff_dict in data:
            # Reconstruct effects with Decimal values
            effects = {k: Decimal(v) for k, v in buff_dict["effects"].items()}
            
            buff = Buff(
                id=buff_dict["id"],
                name=buff_dict["name"],
                effects=effects,
                expiry_type=buff_dict["expiry_type"],
                expiry_value=buff_dict.get("expiry_value"),
                description=buff_dict.get("description", "")
            )
            
            self.active_buffs.append(buff)
            
            # Update ID counter
            if buff.id.startswith("buff_"):
                try:
                    num = int(buff.id.split("_")[1])
                    self._buff_id_counter = max(self._buff_id_counter, num)
                except:
                    pass


if __name__ == "__main__":
    # Unit tests
    print("=== TemporalState Unit Tests ===\n")
    
    temporal = TemporalState()
    
    # Test 1: Add permanent buff
    print("Test 1: Add Permanent Buff")
    buff_id = temporal.add_buff(
        name="力量光环",
        effects={"Strength": 10, "Attack": 5},
        expiry_type="permanent"
    )
    print(f"  Added buff: {buff_id}")
    effects = temporal.get_active_effects()
    print(f"  Active effects: {effects}")
    assert effects["Strength"] == Decimal("10"), "Strength should be +10"
    print("  ✅ PASS\n")
    
    # Test 2: Chapter-based expiry
    print("Test 2: Chapter-based Expiry")
    poison_id = temporal.add_buff(
        name="中毒",
        effects={"HP": -5},
        expiry_type="chapter",
        expiry_value=3
    )
    print(f"  Added poison (expires at Chapter 3): {poison_id}")
    
    # Should still be active at Chapter 2
    expired = temporal.check_expiry(current_chapter=2)
    print(f"  Chapter 2 - Expired buffs: {expired}")
    assert len(expired) == 0, "Poison should still be active"
    
    # Should expire at Chapter 3
    expired = temporal.check_expiry(current_chapter=3)
    print(f"  Chapter 3 - Expired buffs: {expired}")
    assert poison_id in expired, "Poison should have expired"
    print("  ✅ PASS\n")
    
    # Test 3: Word count expiry
    print("Test 3: Word Count Expiry")
    temporal.clear_all()
    
    buff_id = temporal.add_buff(
        name="灵感迸发",
        effects={"Intelligence": 20},
        expiry_type="word_count",
        expiry_value=1000
    )
    print(f"  Added buff (expires at 1000 words): {buff_id}")
    
    expired = temporal.check_expiry(word_count=500)
    assert len(expired) == 0, "Should still be active at 500 words"
    
    expired = temporal.check_expiry(word_count=1000)
    assert len(expired) == 1, "Should expire at 1000 words"
    print("  ✅ PASS\n")
    
    # Test 4: Buff aggregation
    print("Test 4: Buff Aggregation")
    temporal.clear_all()
    
    temporal.add_buff("Buff1", {"Attack": 10}, "permanent")
    temporal.add_buff("Buff2", {"Attack": 5, "Defense": 3}, "permanent")
    
    effects = temporal.get_active_effects()
    print(f"  Aggregated effects: {effects}")
    assert effects["Attack"] == Decimal("15"), "Attack should be +15"
    assert effects["Defense"] == Decimal("3"), "Defense should be +3"
    print("  ✅ PASS\n")
    
    # Test 5: Serialization
    print("Test 5: Serialization")
    serialized = temporal.to_dict()
    print(f"  Serialized: {serialized}")
    
    temporal2 = TemporalState()
    temporal2.from_dict(serialized)
    effects2 = temporal2.get_active_effects()
    print(f"  Restored effects: {effects2}")
    assert effects2 == effects, "Restored state should match original"
    print("  ✅ PASS\n")
    
    # Test 6: Time-based expiry (CRITICAL for replay context)
    print("Test 6: Time-based Expiry During Replay")
    temporal.clear_all()
    
    temporal.add_buff(
        name="临时祝福",
        effects={"Luck": 50},
        expiry_type="chapter",
        expiry_value=4
    )
    
    # Simulate replay context
    print("  Simulating event replay:")
    for chapter in range(1, 6):
        expired = temporal.check_expiry(current_chapter=chapter)
        active_count = len(temporal.active_buffs)
        print(f"    Chapter {chapter}: {active_count} active buff(s), expired: {expired}")
    
    assert len(temporal.active_buffs) == 0, "Buff should be expired by Chapter 5"
    print("  ✅ PASS\n")
    
    print("All tests passed! ✨")
