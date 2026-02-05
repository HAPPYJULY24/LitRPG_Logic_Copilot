# LitRPG Logic Copilot V1.0 - 完整使用教程

## 🚀 第一步：启动应用

```bash
# 确保已安装依赖
pip install -r requirements.txt


# 启动应用
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`

### 🔑 首次配置
在左侧边栏输入你的 **Google Gemini API Key**。
（如果本地有 `.env` 文件则会自动加载）

---

## 📱 界面布局介绍

### 左侧边栏（状态显示）
```
┌─────────────────────────┐
│ 💰 Currency             │  ← 金币总额（自动拆分为 GP/SP/CP）
│   Total: 2 GP, 1 SP, 3 CP
├─────────────────────────┤
│ 📊 Base Stats           │  ← 基础属性（力量、等级等）
│   Strength: 50          │
│   Level: 10             │
├─────────────────────────┤
│ ⚡ Computed Stats       │  ← 计算属性（通过公式得出）
│   Attack: 110 (Computed)│  ← 公式: Attack = Strength * 2 + Level
│   Defense: 30 (Computed)│
├─────────────────────────┤
│ 🛡️ Active Buffs         │  ← 当前生效的增益
│   神圣祝福: Attack+20   │
│   (expires at Chapter 3)│
├─────────────────────────┤
│ 🎒 Inventory            │  ← 背包物品
│   铁剑 × 1              │
│   药水 × 5              │
└─────────────────────────┘
```

### 主界面（3 个标签页）

#### 📝 Tab 1: Story Input
- **输入框**: 粘贴你的小说文本
- **Process Logic 按钮**: 触发 AI 提取
- **交易日志**: 显示处理结果

#### 📜 Tab 2: Event History
- 查看所有历史事件（时间倒序）
- 格式: `#5 GAIN 铁剑 x1 - 击败哥布林`

#### ⚙️ Tab 3: Settings
- **Formula Engine**: 注册计算公式
- **System Info**: 显示系统状态

---

## 💡 基础使用示例

### 示例 1：获得战利品

**步骤**:
1. 切换到 "📝 Story Input" 标签
2. 在文本框输入：
   ```
   林风击败了哥布林首领，从尸体上搜刮到一把锈迹斑斑的铁剑和 50 个金币。
   ```
3. 点击 "🚀 Process Logic" 按钮
4. 等待 1-3 秒

**结果**:
```
✅ GAIN 铁剑 x1: Success
✅ GAIN 50 GP: Success
```

**侧边栏变化**:
- 💰 Currency: `50 GP, 0 SP, 0 CP`
- 🎒 Inventory: `铁剑 × 1`

---

### 示例 2：属性提升

**输入文本**:
```
林风突破瓶颈，力量+15，敏捷+10，等级提升到 25 级。
```

**结果**:
```
✅ GAIN Strength +15: Success
✅ GAIN Agility +10: Success
✅ SET Level = 25: Success
```

**侧边栏变化**:
- 📊 Base Stats:
  - `Strength: 15` (如果之前没有值)
  - `Agility: 10`
  - `Level: 25`

---

### 示例 3：Buff 管理

**输入文本**:
```
林风获得了神圣祝福，攻击力+20，持续 3 章。
```

**结果**:
```
✅ GAIN Buff 神圣祝福: Success
```

**侧边栏变化**:
- 🛡️ Active Buffs:
  ```
  神圣祝福: Attack+20
  (expires at Chapter 3)
  ```

**Buff 过期触发**:
- 输入章节标记：`"--- 第 2 章 ---"`
- 到达第 3 章时，Buff 自动消失

---

## ⚙️ Formula Engine 详细教程

### 什么是 Formula Engine？

Formula Engine（公式引擎）允许你定义**计算属性**，这些属性会根据基础属性自动重新计算。

**典型应用场景**:
- 攻击力 = 力量 × 2 + 等级
- 防御力 = 体质 × 1.5
- 暴击率 = 敏捷 / 100
- 生命上限 = max(体质 × 10, 等级 × 50)

---

### 如何使用 Formula Engine

#### 步骤 1：切换到 Settings 标签

点击主界面顶部的 **"⚙️ Settings"** 标签

#### 步骤 2：注册公式

在 "Formula Engine" 区域：

```
Stat Name: [输入属性名]
Formula:   [输入公式表达式]
[Register Formula] 按钮
```

**示例 1：简单攻击力公式**
```
Stat Name: Attack
Formula:   Strength * 2 + Level

点击 "Register Formula"
```

**示例 2：防御力公式**
```
Stat Name: Defense
Formula:   Vitality * 1.5

点击 "Register Formula"
```

**示例 3：暴击率（百分比）**
```
Stat Name: CritRate
Formula:   Agility / 100

点击 "Register Formula"
```

#### 步骤 3：验证公式生效

注册公式后，侧边栏会立即显示计算结果：

```
⚡ Computed Stats
  Attack: 110 (Computed)    ← Strength(50) * 2 + Level(10) = 110
  Defense: 30 (Computed)    ← Vitality(20) * 1.5 = 30
  CritRate: 0.25 (Computed) ← Agility(25) / 100 = 0.25
```

#### 步骤 4：测试自动重算

**输入文本**:
```
力量+10
```

**结果**:
- 📊 Base Stats:
  - `Strength: 60` (50 → 60)
- ⚡ Computed Stats:
  - `Attack: 130` (自动重算：60 * 2 + 10 = 130) ✨

---

### 支持的公式语法

#### 基础运算符
```python
+    加法    Attack = Strength + Agility
-    减法    Net = Income - Cost
*    乘法    Attack = Strength * 2
/    除法    Rate = Agility / 100
```

#### 内置函数
```python
abs(x)          # 绝对值
max(x, y, ...)  # 最大值
min(x, y, ...)  # 最小值
round(x)        # 四舍五入
int(x)          # 取整
```

#### 高级示例

**物理攻击（组合计算）**
```
Stat Name: PhysicalAttack
Formula:   Strength * 2 + Level + Agility / 2
```

**魔法攻击（条件最大值）**
```
Stat Name: MagicAttack
Formula:   max(Intelligence * 1.5, Level * 3)
```

**生命上限（保底机制）**
```
Stat Name: MaxHP
Formula:   max(Vitality * 10, Level * 50)
```

**闪避率（带上限）**
```
Stat Name: DodgeRate
Formula:   min(Agility / 100, 0.75)
```
> 注意：结果最大为 0.75（75%）

**综合战力（多属性加权）**
```
Stat Name: CombatPower
Formula:   Strength * 3 + Vitality * 2 + Agility * 1.5 + Intelligence * 2
```

---

### 公式引擎特性

#### ✅ 依赖追踪

当基础属性变化时，所有依赖它的计算属性会**自动重算**：

```
流程示意:
力量 +10 → Attack 依赖 Strength → Attack 重算 → PhysicalAttack 依赖 Attack → PhysicalAttack 重算
```

#### ✅ 循环依赖检测

系统会自动检测并阻止循环依赖：

```
❌ 错误示例:
A = B + 10
B = A + 5

错误提示: "Circular dependency detected: A → B → A"
```

#### ✅ Decimal 类型安全

所有计算使用 `Decimal` 类型，避免浮点数精度丢失：

```python
# 传统浮点运算（可能有误差）
0.1 + 0.2 = 0.30000000000000004

# Decimal 运算（精确）
Decimal('0.1') + Decimal('0.2') = Decimal('0.3')
```

---

## 🎮 完整工作流示例

### 场景：创建一个战士角色并升级

#### 1. 设置初始属性（Story Input）
```
林风刚进入游戏，获得新手礼包：100 金币。
初始属性：力量 20，体质 15，敏捷 10，智力 5，等级 1。
```

**结果**:
- 💰 Currency: `100 GP`
- 📊 Base Stats:
  - Strength: 20
  - Vitality: 15
  - Agility: 10
  - Intelligence: 5
  - Level: 1

#### 2. 注册公式（Settings）

切换到 Settings 标签，注册以下公式：

```
Attack = Strength * 2 + Level
Defense = Vitality * 1.5
MaxHP = Vitality * 10 + Level * 5
CritRate = Agility / 100
```

**侧边栏立即显示**:
- ⚡ Computed Stats:
  - Attack: 41 (20 * 2 + 1)
  - Defense: 22.5 (15 * 1.5)
  - MaxHP: 155 (15 * 10 + 1 * 5)
  - CritRate: 0.1 (10 / 100)

#### 3. 升级（Story Input）
```
林风击败了 10 只哥布林，获得 50 金币。
力量+5，体质+3，等级提升到 5 级。
```

**自动重算**:
- 📊 Base Stats:
  - Strength: 25 (20 → 25)
  - Vitality: 18 (15 → 18)
  - Level: 5 (1 → 5)
- ⚡ Computed Stats:
  - Attack: 55 (25 * 2 + 5) ← 自动重算
  - Defense: 27 (18 * 1.5) ← 自动重算
  - MaxHP: 205 (18 * 10 + 5 * 5) ← 自动重算

#### 4. 获得 Buff（Story Input）
```
林风喝下狂暴药水，攻击力+30，持续 3 章。
```

**Buff 生效**:
- 🛡️ Active Buffs:
  ```
  狂暴药水: Attack+30
  (expires at Chapter 3)
  ```
- ⚡ Computed Stats:
  - Attack: 55 (基础) + 30 (Buff) = 85 (实际)

#### 5. 查看历史（Event History）

切换到 Event History 标签：

```
#15 GAIN 狂暴药水 Buff - 喝下药水
#14 SET Level = 5 - 击败哥布林
#13 GAIN Vitality +3 - 击败哥布林
#12 GAIN Strength +5 - 击败哥布林
#11 GAIN 50 GP - 击败哥布林
...
```

---

## 🔧 常见问题

### Q1: 公式不起作用？

**检查清单**:
1. ✅ 变量名是否完全匹配？（区分大小写）
   - ❌ `strength` 或 `STR`
   - ✅ `Strength`
2. ✅ 基础属性是否已设置？
   - 在输入文本中提到："力量+10"
3. ✅ 公式语法是否正确？
   - 使用 `*` 而不是 `×`
   - 使用 `/` 而不是 `÷`

### Q2: AI 提取不准确？

**改善方法**:
1. 使用更明确的描述
   - ❌ "获得了一些金币"
   - ✅ "获得了 50 个金币"
2. 分批次输入（每次 1-3 个交易）
3. 检查置信度图标：
   - ✅ 高置信度（>90%）
   - 🔍 模糊数值（需人工确认）
   - ⚠️ 低置信度（<80%）

### Q3: 如何重置所有数据？

点击侧边栏底部的 **"🔴 Reset State"** 按钮。

---

## 📚 进阶技巧

### 技巧 1：动态战力评估

注册一个综合战力公式：

```
Stat Name: CombatPower
Formula:   Attack * 10 + Defense * 5 + MaxHP / 10
```

每次属性变化时，战力会自动更新。

### 技巧 2：百分比计算

```
Stat Name: HPPercent
Formula:   CurrentHP / MaxHP
```

配合文本输入："当前生命值 80"，即可实时显示血量百分比。

### 技巧 3：装备影响

```
# 未装备时
Attack = Strength * 2

# 装备铁剑后（输入 "装备铁剑，攻击力+15"）
Attack = Strength * 2 + 15 (Buff)
```

---

## 🎉 总结

LitRPG Logic Copilot 的核心流程：

```
1. 输入小说文本 
   ↓
2. AI 提取交易数据 
   ↓
3. Event Sourcing 引擎处理 
   ↓
4. 更新基础属性 
   ↓
5. Formula Engine 自动重算 
   ↓
6. 侧边栏显示最新状态
```

**Formula Engine 的价值**：
- ✅ 避免手动计算错误
- ✅ 自动追踪派生属性
- ✅ 支持复杂的游戏规则
- ✅ 随时调整公式，立即生效

**快速上手步骤**：
1. 启动应用：`streamlit run app.py`
2. 输入初始属性文本
3. 注册核心公式（Attack, Defense, MaxHP）
4. 开始写小说，随时粘贴文本处理

**祝你创作愉快！** ⚔️✨
