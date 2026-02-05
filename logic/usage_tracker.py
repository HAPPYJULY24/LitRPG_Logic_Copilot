
from decimal import Decimal
from typing import Dict

class UsageTracker:
    """
    Tracks LLM API usage and estimates cost.
    Default Pricing: Gemini 1.5 Flash (as of early 2025)
    
    Pricing Source (Approximate):
    - Input: $0.075 / 1M tokens
    - Output: $0.30 / 1M tokens
    """
    
    # Pricing per 1 Million Tokens (USD)
    PRICING = {
        "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-1.5-pro":   {"input": 3.50,  "output": 10.50},  # Example Pro pricing
    }
    
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost_usd = Decimal("0.000000")
        self.saved_cost_usd = Decimal("0.000000") # Cost saved by cache
        
    def track_usage(self, metadata: Dict):
        """
        Record usage from an API call.
        metadata format: {"input_tokens": int, "output_tokens": int, "model": str}
        """
        if not metadata:
            return

        in_tokens = metadata.get("input_tokens", 0)
        out_tokens = metadata.get("output_tokens", 0)
        model = metadata.get("model", "gemini-2.5-flash")
        
        self.total_input_tokens += in_tokens
        self.total_output_tokens += out_tokens
        
        cost = self._calculate_cost(in_tokens, out_tokens, model)
        self.total_cost_usd += cost
        
    def track_saved(self, metadata: Dict):
        """
        Record projected cost saved by cache hit.
        """
        if not metadata:
            return
            
        in_tokens = metadata.get("input_tokens", 0)
        out_tokens = metadata.get("output_tokens", 0)
        model = metadata.get("model", "gemini-2.5-flash")
        
        cost = self._calculate_cost(in_tokens, out_tokens, model)
        self.saved_cost_usd += cost

    def _calculate_cost(self, in_tokens: int, out_tokens: int, model: str) -> Decimal:
        # Fallback to flash pricing if model unknown
        prices = self.PRICING.get(model, self.PRICING["gemini-2.5-flash"])
        
        cost_in = (Decimal(in_tokens) / Decimal(1_000_000)) * Decimal(str(prices["input"]))
        cost_out = (Decimal(out_tokens) / Decimal(1_000_000)) * Decimal(str(prices["output"]))
        
        return cost_in + cost_out

    def get_summary(self) -> Dict:
        return {
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "cost_usd": self.total_cost_usd,
            "saved_usd": self.saved_cost_usd
        }
