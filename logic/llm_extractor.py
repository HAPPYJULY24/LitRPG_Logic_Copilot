"""
LLMExtractor V1.1 - AI 提取层 (The Neural Side)
负责将自然语言文本翻译为 JSON 交易指令

使用 Google Gemini API 进行自然语言处理（新版 google.genai SDK）

V1.1 新特性:
- 支持属性变化 (type: "stat")
- 支持 Buff 管理 (type: "buff")
- 支持货币单位 (unit: GP/SP/CP)
- 支持置信度标记 (confidence, is_fuzzy)
"""
import os
import json
import re
from google import genai
from typing import List, Dict, Tuple
from dotenv import load_dotenv


class LLMExtractor:
    """
    AI 提取层：负责文本 -> JSON 的翻译
    使用 Google Gemini API (新版 google.genai)
    """
    
    def __init__(self):
        # Try loading from Streamlit secrets (cloud) first, then .env (local)
        load_dotenv()
        
        # Priority 1: Streamlit secrets (cloud deployment)
        try:
            import streamlit as st
            api_key = st.secrets.get("GOOGLE_API_KEY")
        except (ImportError, FileNotFoundError, KeyError, AttributeError):
            # Priority 2: Environment variable (local development)
            api_key = os.getenv("GOOGLE_API_KEY")
        
        self.is_offline = False  # Default to online
        self.client = None
        self.model_name = "gemini-2.5-flash"

        if not api_key:
            # Offline Mode: Don't crash, just set flag
            self.is_offline = True
            print("⚠️ Logic Copilot is running in OFFLINE MODE (No API Key found).")
        else:
            try:
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"⚠️ API Client Init Failed: {e}. Switching to OFFLINE MODE.")
                self.is_offline = True

        # System Instruction 定义 (V1.2 Dynamic Units)
        self.system_instruction = """
You are a LitRPG Data Extractor V1.2. Extract game state changes from story text.
Output ONLY a raw JSON list.

JSON Schema V1.2:
[
  // Currency transactions (extract ANY unit found)
  {"action": "gain"|"lose", "type": "gold", "value": "string", "unit": "string", "reason": "string", "confidence": 0.0-1.0, "is_fuzzy": bool},
  
  // Item transactions
  {"action": "gain"|"lose", "type": "item", "name": "string", "qty": int, "reason": "string", "confidence": 0.0-1.0, "is_fuzzy": bool},
  
  // Stat changes
  {"action": "gain"|"lose"|"set", "type": "stat", "name": "string", "value": "string", "reason": "string", "confidence": 0.0-1.0, "is_fuzzy": bool},
  
  // Buff management
  {"action": "gain", "type": "buff", "name": "string", "effects": {"stat": "value"}, "expiry_type": "chapter"|"word_count"|"time"|"permanent", "expiry_value": int|string|null, "description": "string", "confidence": 0.0-1.0, "is_fuzzy": bool}
]

Field Rules:
- unit: Extract the EXACT unit used in text (e.g., "GP", "Gold", "$", "Credits", "Soul Stones"). If unclear, leave null.
- confidence: 0.0-1.0 (0.95+ for explicit game logs, 0.7 for narrative descriptions).
- is_fuzzy: true if vague ("about 50").
- For Stat Changes: "XP", "Level", "Health" are STATS, not currency.
- CRITICAL EXTRACTION RULES (V1.4):
  1. PASSIVES ARE BUFFS: If text mentions "Passive Acquired", "New Trait", "Perk", "Ability", or "Skill Mastery" (e.g., "Grease Resistance +10%"), output as {"type": "buff", "expiry_type": "permanent", "effects": {"StatName": "Value"}}.
  2. VALUE CLEANING: REMOVE leading '+' signs from values. (e.g., "+5%" -> "5%", "+10" -> "10"). AVOID double symbols like "++5".
  3. INDETERMINATE VALUES (V1.5): If a quantity/value is mentioned but unspecified (e.g., "gained some experience", "lost gold"), set "value" or "qty" to "TBD".

Examples:
Text: "Balance: $12.50"
Output: [{"action": "set", "type": "gold", "value": "12.50", "unit": "$", "reason": "Balance check", "confidence": 0.95, "is_fuzzy": false}]

Text: "Awarded 500 Credits."
Output: [{"action": "gain", "type": "gold", "value": "500", "unit": "Credits", "reason": "Reward", "confidence": 0.9, "is_fuzzy": false}]

Text: "Found 20 Gold Pieces and 5 Silver."
Output: [
  {"action": "gain", "type": "gold", "value": "20", "unit": "Gold", "reason": "Loot", "confidence": 0.95, "is_fuzzy": false},
  {"action": "gain", "type": "gold", "value": "5", "unit": "Silver", "reason": "Loot", "confidence": 0.95, "is_fuzzy": false}
]
"""

    def extract_transactions(self, text: str, default_unit: str = "CP", language: str = "zh") -> Tuple[List[Dict], Dict]:
        """
        Extract transactions from text.
        
        Args:
            text: User input
            default_unit: Fallback currency unit if none valid found (default: CP)
            language: Target language for output fields ('en' or 'zh')
            
        Returns:
            (transactions: List[Dict], usage_metadata: Dict)
        """
        if self.is_offline:
            print("⚠️ Offline Mode: Skipping AI extraction.")
            return [], {}
            
        # FAST EXIT (AC-17): Empty/Whitespace Check
        if not text or not text.strip():
            return [], {}

        try:
            # V1.3: Dynamic Language Injection
            lang_instruction = ""
            if language == "zh":
                lang_instruction = "IMPORTANT: All string values in the JSON output, especially the 'reason' and 'name' fields (if not found in schema), MUST be strictly in Simplified Chinese (简体中文). Do not mix English and Chinese."
            else:
                lang_instruction = "IMPORTANT: All string values in the JSON output, especially the 'reason' and 'name' fields (if not found in schema), MUST be strictly in English."

            # Pass default unit context AND language instruction
            full_prompt = f"{self.system_instruction}\n\n{lang_instruction}\n\nText: {text}\nOutput:"
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            
            # Extract Token Usage
            usage = {}
            if hasattr(response, 'usage_metadata'):
                # genai SDK likely returns an object, access attributes safe-ly
                try:
                    usage = {
                        "input_tokens": response.usage_metadata.prompt_token_count,
                        "output_tokens": response.usage_metadata.candidates_token_count,
                        "model": self.model_name
                    }
                except AttributeError:
                    # Fallback if attribute names differ in specific SDK version
                    usage = {"input_tokens": 0, "output_tokens": 0, "model": self.model_name}
            
            content = response.text
            json_str = self._clean_json_string(content)
            transactions = json.loads(json_str)
            
            if not isinstance(transactions, list):
                return [], usage
            
            validated = []
            for tx in transactions:
                # Default safety
                if "confidence" not in tx: tx["confidence"] = 0.8
                if "is_fuzzy" not in tx: tx["is_fuzzy"] = False
                
                # Dynamic Logic for Currency Unit
                if tx.get("type") == "gold":
                    # If unit is missing or None, use the System Default (passed from app)
                    if not tx.get("unit"):
                        tx["unit"] = default_unit
                
                validated.append(tx)
            
            return validated, usage
            
        except json.JSONDecodeError as e:
            print(f"JSON Parsing Error: {e}")
            # SECURITY FIX (V1.3): Do not log raw response to prevent log injection/leakage
            return [], {}
        except Exception as e:
            # Re-raise to allow app.py to handle connection/timeout errors gracefully
            raise e

    def _clean_json_string(self, text: str) -> str:
        """
        清洗 LLM 输出，移除可能的 Markdown 代码块标记
        
        Args:
            text: LLM 原始输出
            
        Returns:
            清洗后的 JSON 字符串
        """
        # 移除可能的 Markdown 代码块标记 ```json ... ```
        text = re.sub(r'^```json\s*', '', text.strip())
        text = re.sub(r'\s*```$', '', text.strip())
        
        # 尝试提取 JSON 数组
        match = re.search(r'\[.*\]', text, re.DOTALL)
        return match.group(0) if match else text


# Self-Test block
if __name__ == "__main__":
    print("🧪 测试 LLMExtractor V1.1...\n")
    
    extractor = LLMExtractor()
    
    if extractor.is_offline:
         print("⚠️ 处于离线模式，跳过 API 测试。")
    else:
        try:
            # 测试用例 1: 传统交易
            test_text_1 = "林风从宝箱里捡起一把生锈的铁剑，获得了50金币。"
            print(f"测试 1 (传统交易): {test_text_1}")
            result_1 = extractor.extract_transactions(test_text_1)
            print(f"结果: {json.dumps(result_1, ensure_ascii=False, indent=2)}\n")
            
            print("✅ 测试完成！")
            
        except ValueError as e:
            print(f"⚠️ 运行时错误: {e}")
