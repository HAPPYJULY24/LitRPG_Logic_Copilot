# LitRPG Logic Copilot POC V1.0 - Quick Reference Card

## 🚀 快速命令

### 启动应用
```bash
streamlit run app.py
```

### 运行测试
```bash
# 所有模块测试
python logic/unit_registry.py       # 5 tests
python logic/formula_engine.py      # 6 tests
python logic/temporal_state.py      # 6 tests
python tests/test_event_sourcing.py # 6 tests
```

### 数据迁移（V1.0 → V1.1）
```bash
python scripts/migrate_v1_to_v1_1.py
```

---

## 📝 文本输入示例

### 基础交易
```
✅ "获得了 50 金币和一把铁剑"
✅ "花费 30 金币购买了皮甲"
✅ "卖掉 2 张狼皮，获得 80 金币"
```

### V1.1 新特性

**多币种支持**
```
✅ "获得了 2 GP 15 SP 3 CP"
✅ "花费 1 Gold 购买药水"
```

**属性变化**
```
✅ "力量+10，敏捷+5"
✅ "等级提升到 25 级"
✅ "智力-3（中毒效果）"
```

**Buff 系统**
```
✅ "获得神圣祝福，攻击力+20，持续 3 章"
✅ "喝下药水，生命值上限+100，持续 1000 字"
✅ "装备神器，全属性+50（永久）"
```

**章节标记（触发 Buff 过期）**
```
✅ "--- 第二章 开始 ---"
✅ "Chapter 3"
```

---

## 🎮 UI 功能导航

### 侧边栏（左侧）
| 区域 | 功能 | 示例 |
|-----|------|------|
| 💰 Currency | 显示金币总额（自动拆分单位） | `2 GP, 1 SP, 3 CP` |
| 📊 Base Stats | 基础属性（力量、等级等） | `Strength: 50` |
| ⚡ Computed Stats | 计算属性（公式驱动） | `Attack: 110 (Computed)` |
| 🛡️ Active Buffs | 当前生效的增益 | `神圣祝福: Attack+20` |
| 🎒 Inventory | 背包物品列表 | `铁剑 × 1` |

### 主界面标签
| Tab | 功能 |
|-----|------|
| 📝 Story Input | 输入文本 + AI 提取 |
| 📜 Event History | 查看所有历史事件 |
| ⚙️ Settings | 公式引擎 + 系统信息 |

---

## ⚙️ 公式语法

### 基础运算符
```python
+    加法    Attack = Strength + Agility
-    减法    Net = Income - Cost
*    乘法    Attack = Strength * 2
/    除法    Rate = Agility / 100
```

### 内置函数
```python
abs(x)          绝对值
max(x, y, ...)  最大值
min(x, y, ...)  最小值
round(x)        四舍五入
int(x)          取整
```

### 示例公式
```python
# 物理攻击
Attack = Strength * 2 + Level

# 魔法攻击
MagicAttack = Intelligence * 1.5 + Level

# 防御力
Defense = Vitality * 1.2 + Level / 2

# 暴击率（%）
CritRate = Agility / 100

# 生命上限
MaxHP = max(Vitality * 10, Level * 50)
```

---

## 🛡️ 货币换算规则

```
1 Gold (GP) = 20 Silver (SP)
1 Silver (SP) = 12 Copper (CP)

因此：
1 GP = 240 CP
```

### 换算示例
```
输入：2 GP 15 SP 3 CP
计算：2×240 + 15×12 + 3 = 480 + 180 + 3 = 663 CP
显示：自动优化为 2 GP, 1 SP, 3 CP
     （因为 15 SP = 1 GP + 3 SP）
```

---

## 🔔 图标说明

### 交易日志图标
| 图标 | 含义 |
|-----|------|
| ✅ | 高置信度提取（>90%） |
| 🔍 | 模糊数值（需人工确认） |
| ⚠️ | 低置信度提取（<80%） |
| ➕ | 获得（gain） |
| ➖ | 失去（lose） |

### 状态图标
| 图标 | 含义 |
|-----|------|
| 💰 | 货币 |
| 📊 | 基础属性 |
| ⚡ | 计算属性 |
| 🛡️ | Buff/增益 |
| 🎒 | 背包 |

---

## 🚫 常见错误

### 错误 1: "金币不足"
```
原因：交易会导致金币变负
解决：先处理"获得金币"，再处理"花费金币"
```

### 错误 2: "公式无法计算"
```
原因：变量名不匹配或循环依赖
解决：检查公式中的变量名是否与属性名完全一致
```

### 错误 3: "LLM Init Failed"
```
原因：.env 文件缺失或 API Key 无效
解决：确保 .env 中有正确的 GOOGLE_API_KEY
```

---

## 📊 数据安全

### 自动备份
每次保存都会创建备份：
```
saves/save_slot_1_events.json         # 主存档
saves/save_slot_1_events.json.backup  # 自动备份
```

### 手动备份
```bash
# Windows
copy saves\save_slot_1_events.json backup_20260130.json

# Linux/Mac
cp saves/save_slot_1_events.json backup_20260130.json
```

### 回滚到备份
```bash
# Windows
copy saves\save_slot_1_events.json.backup saves\save_slot_1_events.json

# Linux/Mac
cp saves/save_slot_1_events.json.backup saves/save_slot_1_events.json
```

---

## 🔧 性能优化建议

### 推荐做法 ✅
- 每 500-1000 字处理一次
- 使用公式引擎自动计算
- 定期查看事件历史
- 分批次输入复杂文本

### 避免 ❌
- 单次输入超过 5000 字
- 过多的嵌套公式（>3 层）
- 频繁修改历史事件（影响性能）

---

## 📞 快速联系

**项目文档：**
- 用户指南：`docs/USER_GUIDE.md`
- 技术文档：`walkthrough.md`
- 实现计划：`implementation_plan.md`
- 任务清单：`task.md`

**测试命令：**
```bash
python -X utf8 tests/test_event_sourcing.py
```

---

## 🎯 键盘快捷键

### Streamlit 通用快捷键
| 快捷键 | 功能 |
|-------|------|
| `r` | 重新运行应用 |
| `c` | 清空缓存 |
| `Ctrl+Enter` | 运行代码块（Jupyter 模式） |

---

**版本：** POC V1.0  
**最后更新：** 2026-01-30
