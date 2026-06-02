# 《盗梦空间》(Dream_Stealing) 项目文档

> 一款基于 Python + Pygame 的像素风格**不对称竞技塔防游戏**，支持人类/猎梦者双阵营对抗。

---

## 目录

- [一、项目概述](#一项目概述)
- [二、技术栈与运行](#二技术栈与运行)
- [三、项目结构](#三项目结构)
- [四、核心架构](#四核心架构)
- [五、游戏状态机](#五游戏状态机)
- [六、地图系统](#六地图系统)
- [七、实体与建筑系统](#七实体与建筑系统)
- [八、战斗与 AI 系统](#八战斗与-ai-系统)
- [九、渲染系统](#九渲染系统)
- [十、输入与摄像机](#十输入与摄像机)
- [十一、UI 系统](#十一ui-系统)
- [十二、配置与平衡数据](#十二配置与平衡数据)
- [十三、附属工具脚本](#十三附属工具脚本)
- [十四、关键设计亮点](#十四关键设计亮点)
- [十五、已知特性与说明](#十五已知特性与说明)
- [十六、潜在改进方向](#十六潜在改进方向)

---

## 一、项目概述

### 1.1 项目定位

**《盗梦空间》** 是一款 **2D 90° 顶视** 像素风格的**不对称竞技塔防游戏**（Asymmetric Tower Defense）。游戏灵感来源于经典电影《盗梦空间》的多层梦境设定，玩家将选择"人类"或"猎梦者"两个截然不同的阵营，体验完全不同的游戏目标、视角和操作方式。

### 1.2 核心玩法

| 阵营 | 目标 | 操作 | 胜利条件 |
|------|------|------|----------|
| **人类模式** (`MODE_HUMAN`) | 建造防御、击退猎梦者 | WASD 控制一名玩家人类，其余 5 人为 AI 盟友 | 击杀猎梦者 |
| **猎梦者模式** (`MODE_HUNTER`) | 攻破人类防御、消灭所有人类 | WASD 控制猎梦者，6 个人类全部为 AI | 击杀所有人类 |

### 1.3 项目特点

- **双阵营对抗**：完全不同的操作视角、策略体系和胜利条件
- **像素美术**：所有纹理均通过 Python 代码程序化生成，**零外部图片资源**
- **AI 对战**：人类和猎梦者均可由 AI 操控，实现完整单机对战
- **深度策略**：4 种建筑 × 多级升级 + 经济管理 + 路径选择
- **代码规模**：约 **2800 行** Python 代码，**12 个核心模块**

---

## 二、技术栈与运行

### 2.1 技术栈

| 类别 | 选型 |
|------|------|
| 编程语言 | Python 3.12 |
| 游戏框架 | Pygame 2.6 |
| PPT 工具 | python-pptx（仅 [build_ppt.py](build_ppt.py) 使用） |
| 操作系统 | Windows（开发与运行环境） |

### 2.2 运行方式

```bash
# 启动游戏主程序
python main.py
```

### 2.3 操作键位

| 按键 | 功能 |
|------|------|
| `W` / `A` / `S` / `D` 或方向键 | 移动角色（4 格/秒） |
| 鼠标左键 | 点击建造 / 升级 / 切换视角 |
| `ESC` | 返回主菜单 |
| `P` | 暂停 / 继续 |
| 鼠标拖拽 | 移动摄像机视野 |

---

## 三、项目结构

### 3.1 目录树

```
Dream_Stealing/
├── main.py              # 游戏入口、主循环、状态机
├── core/                # 核心配置与状态
│   ├── __init__.py
│   ├── config.py        # 全局配置（地图/颜色/数据表）
│   └── game_state.py    # 游戏状态容器
├── entities/            # 实体数据类
│   ├── __init__.py
│   └── entities.py      # Human / DreamHunter / Bullet / Building
├── world/               # 世界/地图数据
│   ├── __init__.py
│   └── map_data.py      # 9 房间地图生成 + A* 寻路
├── systems/             # 核心系统（业务逻辑）
│   ├── __init__.py
│   └── systems.py       # 经济/战斗/AI/移动/胜负
├── graphics/            # 表现层（2D 90° 顶视渲染）
│   ├── __init__.py
│   ├── renderer.py      # 程序化纹理 + 顶视绘制
│   └── effects.py       # 飘字特效（伤害/金币/回血）
├── ui/                  # 用户界面
│   ├── __init__.py
│   ├── ui_menu.py       # 主菜单
│   ├── ui_hud.py        # HUD + 弹出菜单 + 暂停菜单
│   ├── ui_camera.py     # 摄像机系统（viewport 跟随）
│   └── input_router.py  # 输入事件路由
├── backup_*/            # 历史版本快照（pre_art_fix / pre_pause_fix / pre_optimization / pre_iso）
├── __pycache__/         # Python 编译缓存
└── README.md            # 项目文档
```

> **渲染视角**：本项目采用**2D 90° 垂直顶视（top-down）** 风格，所有建筑、人物、泉水均以俯瞰方式绘制为像素色块/精灵，没有 3D 透视与等距投影。

### 3.2 模块依赖图

```
                        ┌──────────────┐
                        │ core.config  │  ← 全局常量
                        └──────┬───────┘
              ┌────────────────┼────────────────┐
              │                │                │
        ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
        │  world/   │   │ entities/ │   │  ui/      │  ← 底层模块
        │  map_data │   │  entities │   │ (ui_menu/ │
        └─────┬─────┘   └─────┬─────┘   │  ui_hud/  │
              │                │        │  camera/  │
              └────┬───────────┼────────│  input)   │
                   │           │        └─────┬─────┘
              ┌────▼─────┐  ┌──▼────────┐     │
              │  core/   │  │ systems/  │  ← 中间业务层
              │game_state│  └────┬──────┘     │
              └────┬─────┘       │            │
                   │             │            │
                   └──────┬──────┘            │
                          │                   │
                   ┌──────▼───────────────────▼──┐
                   │   main.py + graphics/     │  ← 入口 + 主循环
                   │   (renderer / effects)    │     表现层
                   └────────────────────────────┘
```

**设计原则**：
- **单向依赖**：`core.config` ← 业务模块 ← `main`，无循环引用
- **数据/逻辑分离**：`entities/`（纯数据） + `systems/`（纯逻辑）
- **表现层独立**：`ui/` 和 `graphics/` 接收 `GameState` 引用进行绘制
- **2D 顶视渲染**：始终保持正交俯瞰，**不引入 3D/等距/伪 3D**

### 3.3 文件清单

| 文件 | 行数 | 核心职责 |
|------|------|----------|
| [main.py](main.py) | ~410 | 游戏入口、主循环（60 FPS）、状态机驱动、事件分发 |
| [core/config.py](core/config.py) | ~108 | 全局常量：屏幕尺寸、颜色、Tile 类型、升级数据表 |
| [core/game_state.py](core/game_state.py) | ~220 | 全局状态容器、初始化、查询接口 |
| [entities/entities.py](entities/entities.py) | ~265 | 数据类：`Human` / `DreamHunter` / `Bullet` / `Building` |
| [world/map_data.py](world/map_data.py) | ~330 | 9 房间地图生成、走廊/墙壁构建、A* 寻路 |
| [systems/systems.py](systems/systems.py) | ~583 | 核心系统：经济/战斗/AI/移动/胜负判定 |
| [graphics/renderer.py](graphics/renderer.py) | ~380 | 程序化像素纹理生成、地图/实体/建筑绘制（2D 顶视） |
| [graphics/effects.py](graphics/effects.py) | ~62 | 飘字特效（伤害/金币/回血） |
| [ui/ui_menu.py](ui/ui_menu.py) | ~102 | 主菜单 + 双模式选择按钮 |
| [ui/ui_hud.py](ui/ui_hud.py) | ~356 | 顶部 HUD、建造/升级弹出菜单、暂停菜单 |
| [ui/ui_camera.py](ui/ui_camera.py) | ~84 | 摄像机：跟随/视口/坐标转换 |
| [ui/input_router.py](ui/input_router.py) | ~59 | 输入事件路由（HUD 点击 / 拖拽镜头 / 点击） |

---

## 四、核心架构

### 4.1 主循环结构

[main.py:50-218](main.py) 实现了**经典的主循环三段式**：

```python
while running:
    dt = clock.tick(60) / 1000.0  # 固定步长 60 FPS
    if dt > 0.1: dt = 0.1  # 防止卡顿后瞬移

    # ① 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.VIDEORESIZE: ...
        elif event.type == pygame.KEYDOWN: ...
        cam_event, cam_data = input_router.handle_event(event, game_state)
        # ...分发到具体处理

    # ② 逻辑更新
    if not game_state.paused:
        if game_state.phase == PHASE_SAFE:
            _update_safe_phase(game_state, dt)
        elif game_state.phase == PHASE_PLAYING:
            _update_playing_phase(game_state, dt)
            update_economy(game_state, 1.0)
            _spawn_gold_effects(game_state)

    camera.update(dt)
    update_effects(game_state, dt)

    # ③ 渲染
    if game_state.phase == PHASE_MENU:
        render_menu(...)
    elif game_state.phase in (PHASE_SAFE, PHASE_PLAYING):
        render_game(...)
    elif game_state.is_game_over():
        _render_game_over(...)

    pygame.display.flip()
```

**关键设计**：
- **dt 钳制**：最大 0.1 秒，避免切换窗口后回放卡顿造成"瞬移"
- **状态分支**：根据 `phase` 选择不同的更新/渲染逻辑
- **暂停机制**：`paused=True` 时跳过更新但不跳过渲染

### 4.2 关键数据流

```
[玩家输入] → [InputRouter] → [(event_type, data)]
                                    ↓
                            [main.py 事件分发]
                                    ↓
                ┌───────────────┼───────────────┐
                ↓               ↓               ↓
          [GameState]      [Camera]      [UI/HUD]
                ↓               ↓               ↓
              [更新]         [跟随]          [绘制]
                ↓               ↓
            [Entities]      [Renderer]
                ↓               ↓
            [Systems]       [Effects]
```

---

## 五、游戏状态机

### 5.1 阶段定义

```python
PHASE_MENU    = 0  # 主菜单
PHASE_INIT    = 1  # 地图/实体初始化（瞬时）
PHASE_SAFE    = 2  # 安全期（25 秒，玩家布局阶段）
PHASE_PLAYING = 3  # 正式对抗
PHASE_VICTORY = 4  # 胜利结算
PHASE_DEFEAT  = 5  # 失败结算
```

### 5.2 模式定义

```python
MODE_HUMAN  = 0  # 玩家控制一个人类
MODE_HUNTER = 1  # 玩家控制猎梦者
```

### 5.3 状态转换图

```
                  ┌─ ESC ─┐
                  ↓      │
  ┌──────────┐  INIT   ┌──┴──────┐
  │PHASE_MENU├───────→│PHASE_SAFE│ ←─ 25秒倒计时
  └────┬─────┘ 选模式  └────┬─────┘
       ↑                    ↓ safe_timer=0
       │              ┌─────▼──────┐
       │              │PHASE_PLAYING│
       │              └─────┬───────┘
       ↑                    ↓
   ┌───┴────┐    ┌──────────┴──────────┐
   │VICTORY │←───│ 胜负判定              │
   │ DEFEAT │    │ check_win_lose()     │
   └────────┘    └─────────────────────┘
```

### 5.4 胜负判定逻辑

[systems.py:467-495](systems.py) 根据模式分支：

| 模式 | 胜利条件 | 失败条件 |
|------|----------|----------|
| `MODE_HUMAN` | 猎梦者 HP ≤ 0 | 玩家人类死亡 |
| `MODE_HUNTER` | 全部人类死亡 | 猎梦者 HP ≤ 0 |

---

## 六、地图系统

### 6.1 地图规格

- **网格尺寸**：33 列 × 26 行
- **每格像素**：32 × 32
- **总分辨率**：1056 × 832

### 6.2 横向布局

```
[ 左组6宽 | 墙1 | 走廊2宽 | 墙1 | 中左4宽 | 墙1 | 中心6宽 | 墙1 | 走廊2宽 | 墙1 | 右组6宽 ]
   col1-6      7    8-9      10   11-14    15   16-21     22    23-24     25   26-31
```

### 6.3 走廊网络

- **纵向走廊**：cols 8-9, 23-24（贯穿整个地图）
- **横向走廊**：rows 7-8, 16-17（横穿整个地图）
- 形成**十字交通网**，连接所有房间

### 6.4 9 个房间模板

| ID | 位置 (col, row) | 尺寸 (w×h) | 门位置 | 门方向 |
|----|----------------|------------|--------|--------|
| 0  | (1, 2)  | 5×4  | (5, 3)  | right |
| 1  | (26, 2) | 5×4  | (26, 3) | left  |
| 2  | (16, 2) | 6×3  | (19, 4) | down  |
| 3  | (1, 11) | 5×4  | (5, 13) | right |
| 4  | (26, 11)| 5×4  | (26, 13)| left  |
| 5  | (11, 10)| 4×3  | (13, 12)| right |
| 6  | (16, 10)| 4×3  | (18, 12)| right |
| 7  | (1, 19) | 6×4  | (5, 19) | up    |
| 8  | (26, 19)| 6×4  | (27, 19)| up    |

### 6.5 墙壁生成算法

[map_data.py:139-153](map_data.py) 实现了**优雅的避让算法**：

1. **预标记不可放墙区**：房间内部 + 门 + 门前两格 + 走廊
2. **房间外圈放墙**：每个房间上/下边（含四角）+ 左/右边
3. **走廊保留**：确保门前两格和走廊不被墙堵住
4. **外围边界**：地图最外圈补上边界墙

### 6.6 A* 寻路系统

[map_data.py:220-253](map_data.py) 实现 A* 寻路：

- **启发式**：曼哈顿距离 `abs(a[0]-b[0]) + abs(a[1]-b[1])`
- **数据结构**：`heapq` 优先队列
- **实体类型通行规则**：

| 实体类型 | 走廊 | 泉水 | 房间 | 门（完好） | 门（破） | 床 |
|----------|------|------|------|-----------|---------|-----|
| `hunter` | ✓ | ✓ | 仅破门 | ✗ | ✓ | ✗ |
| `human_wandering` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `human_bed` | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

- **门 HP 动态影响可达性**：门破前房间对猎梦者不可达

### 6.7 泉水与出生点

- **泉水**：[world/map_data.py:280-313](world/map_data.py) 在地图边缘（top/bottom/left/right 四选一）随机生成 2×2 区域
- **出生点**：`MAP_COLS // 2, 7`（地图上方中央）

---

## 七、实体与建筑系统

### 7.1 实体类层次

```
┌─────────────┐
│  Human      │  人类玩家 / AI
├─────────────┤
│ DreamHunter │  猎梦者（带升级系统）
├─────────────┤
│  Bullet     │  炮塔子弹（追踪型）
├─────────────┤
│  Building   │  建筑（门/床/炮塔/维修台）
└─────────────┘
```

### 7.2 Human 类

**属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | int | 唯一标识（0-5） |
| `is_player` | bool | 是否为玩家 |
| `color` | tuple | RGB 颜色 |
| `gold` | int | 当前金币 |
| `state` | int | 状态：`WANDERING(0)` / `BED(1)` / `DEAD(2)` |
| `room_id` | int/None | 所属房间 ID |
| `grid_col/row` | int | 逻辑网格位置 |
| `px/py` | float | 渲染像素位置（用于平滑插值） |
| `speed` | float | 移动速度（px/秒） |
| `move_path` | list | A* 寻路路径 |
| `move_timer` | float | 移动节流计时器 |
| `decision_timer` | float | AI 决策计时器（仅 AI） |
| `is_under_attack` | bool | 当前帧是否被攻击（用于头像描边） |

**状态机**：

```
WANDERING (游荡) ───[到达床格]───→ BED (上床)
     ↓
   [被秒杀]
     ↓
  DEAD (死亡)
```

### 7.3 DreamHunter 类（5 级成长）

| 等级 | HP  | 攻击 | 攻速(次/秒) | 移速(格/秒) | 泉水回血(HP/秒) |
|------|-----|------|------------|------------|----------------|
| Lv1  | 500  | 12 | 0.8 | 3.5 | 60  |
| Lv2  | 800  | 18 | 1.0 | 3.5 | 80  |
| Lv3  | 1200 | 28 | 1.2 | 3.5 | 100 |
| Lv4  | 1800 | 42 | 1.5 | 3.5 | 130 |
| Lv5  | 2600 | 62 | 1.8 | 4.0 | 170 |

**升级机制**（[entities.py:106-117](entities.py)）：

- 累计伤害达到阈值 `[0, 350, 1200, 3500, 8000]` 自动升级
- 升级时**回满 HP**、**解除逃跑状态**、**更新移速**

**逃跑机制**：
- `flee_threshold = max_hp × 0.2`
- HP ≤ 阈值时 `fleeing = True`，寻路回泉水
- 满血后自动取消

### 7.4 Building 类（4 种类型）

| 类型 | 标识 | 功能 | 可升级 |
|------|------|------|--------|
| 门 | `BLDG_DOOR (0)` | 阻挡猎梦者，有 HP | ✓ (Lv1-5) |
| 床 | `BLDG_BED (1)` | 产出金币 | ✓ (Lv1-5) |
| 炮塔 | `BLDG_TURRET (2)` | 自动攻击 | ✓ (Lv1-4) |
| 维修台 | `BLDG_REPAIR (3)` | 自动回血门 | ✓ (Lv1-5) |

**升级数据表**：

| 建筑 | 等级 | 费用 | 属性 |
|------|------|------|------|
| **门** | Lv1→5 | 0→50→130→300→650 | HP: 350→600→1000→1700→2800 |
| **床** | Lv1→5 | 0→35→90→230→550 | 金币: 1→2→4→8→16/秒 |
| **炮塔** | Lv1→4 | 55→45→110→260 | DPS: 8→14→24→40 / 射程: 5→6→7→8 |
| **维修台** | Lv1→5 | 35→40→100→250→550 | 回血: 80→140→220→340→520 HP/秒 |

### 7.5 Bullet 类

- **移动方式**：追踪目标（猎梦者）位置，按速度插值
- **碰撞检测**：距离 < 8 像素即命中
- **销毁时机**：命中目标或达到目标位置

---

## 八、战斗与 AI 系统

### 8.1 战斗主流程

`update_combat()`（[systems.py:26-201](systems.py)）每帧执行 6 个子任务：

```
1. 猎梦者攻击门 (相邻门 HP 扣减，累计伤害触发升级)
   ↓
2. 炮塔自动攻击 (射程内 + 可达性检测 → 发射子弹)
   ↓
3. 触碰秒杀 (走廊游荡 / 破门房间内)
   ↓
4. 泉水回血 (在泉水格按 regen_rate × dt 治疗)
   ↓
5. 子弹追踪 (按 360 px/秒 移动，到达目标扣 HP)
   ↓
6. 维修台回血 (累积器模式，避免 dt 整数丢失)
```

### 8.2 战斗细节

**猎梦者攻击门**（[systems.py:57-78](systems.py)）：

- 检测四方向相邻门
- 攻击冷却：`1.0 / atk_speed` 秒
- 攻击效果：门扣 HP + 累计伤害 + 标记 `is_under_attack`

**炮塔攻击**（[systems/systems.py:81-122](systems/systems.py)）：

- 检测射程 `dist ≤ turret_range`
- **可达性约束**：猎梦者须在走廊/泉水 或 门已破的房间内
- 子弹飞行速度：`BULLET_SPEED = 360 px/秒`

**秒杀规则**：

| 人类状态 | 位置 | 猎梦者接触结果 |
|----------|------|----------------|
| `WANDERING` | 走廊 | 立即秒杀 |
| `BED` | 门未破的房间 | 不触发（门挡住） |
| `BED` | 门已破的房间 | 立即秒杀 |

**维修台回血**：

- 使用**小数累积器** `_repair_accum`（每帧累加 `repair_hps * dt`，达到 1 才实际修复）
- 每秒汇总飘字 `_spawn_heal_number`

### 8.3 AI 人类决策系统

**触发条件**：每 3-5 秒（`AI_DECISION_MIN/MAX`）决策一次

**决策优先级**：

```
1. 升级床（最高优先级）
   ↓
2. 升级门（门等级 < 床等级时）
   ↓
3. 建造炮塔（房间空位 + 金币 ≥ 55）
   ↓
4. 建造维修台（房间空位 + 金币 ≥ 35 + 至少 1 个炮塔）
   ↓
5. 升级炮塔（炮塔等级 < 床等级时）
```

**实现**：见 [systems/systems.py:259-318](systems/systems.py) `_ai_human_decide()`

### 8.4 AI 猎梦者决策系统

**状态机**：

```
            ┌─────────────┐
            │  正常攻击    │
            └──────┬──────┘
                   │ HP ≤ 20% × max_hp
                   ↓
            ┌─────────────┐
            │  残血逃跑    │
            └──────┬──────┘
                   │ at_fountain && is_full_hp
                   ↓
            ┌─────────────┐
            │  正常攻击    │
            └─────────────┘
```

**目标选择策略**（[systems.py:321-430](systems.py)）：

1. 优先攻击**有活人入住**且**门未破**的房间
2. 选**门等级最低**的目标（容易破）
3. 门破后进入房间追击**最近可通行格**靠近人类
4. 兜底：所有门完好但都无人时 → 追击走廊游荡者

**破门追击**：

- 门破后 `_find_hunt_target_in_room` 找房间内距人类最近的可通行格
- 寻路到该位置（adjacent 即触发秒杀）

### 8.5 AI 开局寻路

**2 秒延时机制**：

- 主循环中 `if game_state.game_time > 2.0: update_ai(...)`
- **设计意图**：开局金币（HUMAN_INIT_GOLD = 25）不足以建造任何建筑（炮塔 55、维修台 35、门 50、床 35），AI 立即决策也无处花钱；同时避免开局瞬间大量寻路计算造成卡顿
- 2 秒后金币累计达到 ~27，仍不足，但累计达 ~35 时（安全期早期）即可触发建造

**房间分配**（[game_state.py:128-158](game_state.py)）：

- `_assign_ai_rooms()` 在 INIT 阶段为 AI 人类分配房间
- 使用 `reserved_room_ids` 防止多人抢同一房
- 玩家在 MODE_HUMAN 下**需要自己走房间点头像切换**才能上床

---

## 九、渲染系统

### 9.0 视角策略

游戏采用 **2D 90° 垂直顶视（top-down）** 视角：
- 摄像机俯视整个 33×26 网格地图
- 不做 3D 透视，**不**做等距菱形投影
- 角色/建筑始终以"在头顶看下去"的方式呈现为像素精灵
- 子弹为屏幕上的 2D 圆点，不带 Z 序

### 9.1 渲染管线

"**Viewport → Scale**" 流程（[graphics/renderer.py:220-273](graphics/renderer.py)）：

```
世界坐标 (33×26×32=1056×832 px)
   ↓
viewport (固定 416×416 px, 13×13 格)
   ↓
pygame.transform.scale
   ↓
屏幕游戏区 (按窗口尺寸自适应)
```

**实现细节**：

1. **动态计算 scale**：`scale = min(W/H, H/H)`，让 viewport 填满屏幕
2. **分层绘制**：地图 → 建筑 → 实体 → 子弹
3. **HUD 不缩放**：始终在屏幕顶部 56px
4. **弹出菜单/特效**：直接在屏幕坐标上绘制

### 9.2 程序化纹理生成

**无任何图片资源**，所有纹理通过 `pygame.draw.*` API 实时绘制。

| 元素 | 实现 | 颜色 |
|------|------|------|
| **地板** | 8 像素网格 + 蓝绿棋盘阴影 | `TEAL` / `DARK_TEAL` |
| **墙壁** | 3 行错位砖块 | `BROWN` / `DARK_BROWN` |
| **门** | 横栅栏 + 铆钉 + 雕花（Lv3+） | `IRON` |
| **床** | 枕头 + 褶皱被子 | 多色 |
| **炮塔** | 底座 + 炮管（Lv2+ 双管） | 金属色 |
| **维修台** | 工作台 + 十字标志 | 蓝灰色 |
| **人类** | 圆头 + 身体（躺平为椭圆） | 玩家色 / AI 色 |
| **猎梦者** | 暗紫椭圆 + 红眼 | 紫色 |
| **泉水** | 3 圈涟漪 | 深蓝 |

**等级视觉变化**：
- 门：Lv3+ 铆钉，Lv4+ 雕花
- 床：尺寸变大（0.6 + level × 0.12），Lv3+ 金边
- 炮塔：底座变大、炮管变粗（4 + level），Lv3+ 金色

### 9.3 渲染顺序

```python
# viewport 内绘制
_render_map(viewport, game_state, left, top)       # 地图层
_render_buildings(viewport, game_state, left, top) # 建筑层
_render_entities(viewport, game_state, left, top)  # 实体层
_render_bullets(viewport, game_state, left, top)   # 子弹层

# 缩放并绘制到屏幕
screen.blit(scaled, (game_area_x, game_area_y))

# 屏幕坐标系绘制
render_hud(screen, ...)                  # HUD
render_popup_menu(screen, ...)           # 弹出菜单
render_effects(screen, ...)              # 飘字特效
```

---

## 十、输入与摄像机

### 10.1 InputRouter 事件路由

[input_router.py](input_router.py) 将底层 Pygame 事件**语义化**：

| 输入 | 返回 `(event_type, data)` |
|------|---------------------------|
| HUD 区域点击 | `('hud_click', pos)` |
| 拖拽开始 | `('drag_start', pos)` |
| 拖拽中 | `('dragging', pos)` |
| 拖拽结束（5px 容差内） | `('click', pos)` |
| 拖拽结束（>5px） | `('drag_end', pos)` |
| `SPACE` 键 | `('space', None)` |

**设计价值**：让 [main.py](main.py) 事件分支可读性大幅提升。

### 10.2 Camera 系统

**关键参数**（[ui/ui_camera.py:7-9](ui/ui_camera.py)）：

```python
VIEW_RADIUS = 6        # 视野半径（格）
VIEW_TILES = 13        # 13×13 格
VIEWPORT_SIZE = 416    # 像素
```

**核心 API**：

| 方法 | 功能 |
|------|------|
| `set_target(entity)` | 设置跟随目标 |
| `snap_to_entity(entity)` | 瞬移视口中心到实体 |
| `update(dt)` | 平滑跟随（`lerp(t=8*dt)`） |
| `_clamp()` | 限制视口不超出地图边界 |
| `screen_to_grid(x, y, ...)` | 屏幕坐标 → 世界网格坐标 |
| `viewport_map_rect` | viewport 在地图上的覆盖范围 |

**拖拽逻辑**（[ui/input_router.py:38-47](ui/input_router.py)）：

- 拖动 > 5px 时 `follow_player = False`
- 反向移动摄像机中心（`cx = drag_start_cx - dx / scale`）

---

## 十一、UI 系统

### 11.1 UI 模块分布

| 文件 | 职责 |
|------|------|
| [ui_menu.py](ui_menu.py) | 主菜单 + 双模式按钮 |
| [ui_hud.py](ui_hud.py) | 顶部 HUD + 建造/升级/暂停菜单 |
| [ui_camera.py](ui_camera.py) | 摄像机（已属 UI 体系） |

### 11.2 主菜单

- 标题："DREAM LOBBY" + "盗 梦 空 间"
- 两个按钮：**人类模式**（蓝） / **猎梦者模式**（红）
- 像素阴影 + 双层描边效果

### 11.3 HUD 顶部状态栏

- **左上**：暂停按钮（两条竖线图标）
- **左侧**：金币（人类模式）/ 伤害 + 等级（猎梦者模式）
- **中间**：安全期倒计时 / 游戏时间 + 猎梦者 HP
- **右侧**：6 个人类头像（按 ID 排序，红色边框 = 正在被攻击） + 猎梦者头像

### 11.4 弹出菜单

- **建造菜单**：点击房间空格子 → 弹出（炮塔/维修台选项）
- **升级菜单**：点击已有建筑 → 弹出（升级到 X 级 + 费用）
- **暂停菜单**：屏幕中央半透明遮罩 + 暂停/退出按钮

### 11.5 飘字特效

- **伤害飘字**（红）：猎梦者攻击/炮塔命中时
- **金币飘字**（黄）：床每秒产出
- **回血飘字**（绿）：维修台每秒汇总

所有飘字 1 秒后消失，带**透明度渐隐**和**向上漂移**动画。

---

## 十二、配置与平衡数据

### 12.1 全局常量（[core/config.py](core/config.py)）

**屏幕参数**：

```python
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TILE_SIZE = 32
HUD_HEIGHT = 56
```

**颜色调色板**：15 种预定义颜色（BLACK, WHITE, RED, GREEN, BLUE, YELLOW, PURPLE, DARK_PURPLE, ORANGE, GRAY, DARK_GRAY, LIGHT_GRAY, BROWN, DARK_BROWN, TEAL, DARK_TEAL, BEIGE, DARK_BEIGE, IRON）

**Tile 类型**：`EMPTY/WALL/ROOM/DOOR/BED/FOUNTAIN`（0-5）

**建筑类型**：`BLDG_DOOR/BED/TURRET/REPAIR`（0-3）

### 12.2 通用参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `HUMAN_INIT_GOLD` | 25 | 人类初始金币 |
| `SAFE_TIME` | 25 | 安全期秒数 |
| `AI_DECISION_MIN/MAX` | 3.0 / 5.0 | AI 决策间隔（秒） |
| `HUNTER_FLEE_HP_RATIO` | 0.2 | 逃跑 HP 比例 |
| `BULLET_SPEED` | 360 | 子弹速度（px/秒） |
| `HUMAN_SPEED` | 4.0 | 人类移速（格/秒） |
| `HUNTER_SPEED` | [3.5, 3.5, 3.5, 3.5, 4.0] | 猎梦者各等级移速 |

### 12.3 数据驱动设计

- **40+ 可调参数**集中于 [config.py](config.py)
- 所有升级数据均通过索引访问（`level=0` 对应 Lv1）
- 易于调整游戏平衡性

---

## 十三、附属工具脚本

> 当前版本已**移除** `build_ppt.py` / `analyze_ppt.py` 等 PPT 工具（重构时清理）。
> 后续如需重新接入，可在 `tools/` 子目录新增，例如 `tools/build_ppt.py`。

---

## 十四、关键设计亮点

### 14.1 房间预订防冲突

```python
self.reserved_room_ids = set()  # AI 分配 + 玩家上床都加进集合
```

避免两个 AI 寻路到同一张床。

### 14.2 双层坐标系（逻辑+渲染）

`grid_col/row` 用于寻路/碰撞；`px/py` 用于平滑插值动画，兼顾离散与连续。

### 14.3 累积器模式处理 dt

维修台、飘字均使用**小数累积器**，避免低帧率下整数运算丢失：

```python
acc = game_state._repair_accum.get(door_key, 0.0) + total_heal
if acc >= 1.0:
    heal_int = int(acc)
    door.repair(heal_int)
    acc -= heal_int
```

### 14.4 AI 与玩家共享同一规则

AI 寻路/攻击使用与玩家完全相同的 `find_path` / `move_along_path` / `_hunter_attack_door`，**保证规则一致性**。

### 14.5 状态机分支判定

胜负判定 `check_win_lose()` 在 [systems/systems.py:467](systems/systems.py) 根据 `mode` 分支，避免在多处重复判断。

### 14.6 关卡式 AI 决策冷却

```python
human.decision_timer = random.uniform(AI_DECISION_MIN, AI_DECISION_MAX)  # 3~5秒
```

防止所有 AI 同帧决策造成卡顿。

### 14.7 门 HP 动态影响寻路

`is_walkable_for()` 接收 `door_hp_map`，门破前房间对猎梦者不可达，门破后即可进入，**实现动态地图变化**。

### 14.8 视口渲染 + 屏幕坐标

先在固定 416×416 viewport 绘制世界 → 缩放到屏幕 → HUD/菜单/特效在屏幕坐标系直接绘制，**多坐标系协同**。

---

## 十五、已知特性与说明

### 15.1 炮塔数量

游戏设计上**没有严格的炮塔数量上限**。`ui_hud.py:181` 中的 `if len(turrets) < 4` 和 `systems.py:296` 中的 `len(turrets) < 3` 是 UI 菜单和 AI 决策的**软性触发条件**，玩家可以建造多个炮塔。

### 15.2 AI 启动延时

游戏开局时，`update_ai()` 需要等待 `game_time > 2.0` 秒才会触发：

- **金币因素**：初始 25 金币不足以建造任何建筑（最便宜 35 金币的维修台）
- **性能因素**：避免开局瞬间大量寻路计算造成卡顿

### 15.3 玩家上床方式

在 `MODE_HUMAN` 下，**玩家不会自动分配房间**。需要：

1. 使用 WASD 移动玩家角色
2. 走到某房间的床上（`_check_bed_occupy` 自动触发 `set_bed`）
3. 锁定后即可建造/升级

### 15.4 双层菜单状态

- `_pause_menu_open`：暂停菜单面板的显示状态（点击暂停按钮切换）
- `paused`：实际游戏暂停状态（按 P 键切换）

两套状态互不干扰，菜单面板可在游戏运行时打开。

### 15.5 缩放适配

游戏区按窗口尺寸**自适应缩放**（`scale = min(W, H) / 416`），但 HUD 不缩放，始终 56 px 高。

---

## 十六、潜在改进方向

| 类别 | 问题 | 建议 |
|------|------|------|
| **画风** | 当前为 90° 顶视像素风格 | 引入美术资源替换程序化绘制；可考虑半身像立绘 + 顶视场景 |
| **性能** | 渲染时每帧重新创建子 Surface（[graphics/renderer.py:10-14](graphics/renderer.py)） | 缓存常用纹理到字典 |
| **架构** | `GameState` 持有大量跨模块状态 | 拆分为 `WorldState` + `UIState` |
| **可扩展** | 9 房间硬编码在 `ROOM_DEFS` | 改为 JSON 配置 |
| **音效** | 无音频模块 | 添加 `audio.py`，支持背景音乐 + 战斗音效 |
| **存档** | 每次开局重新生成地图 | 增加 `save/load` 序列化 |
| **网络** | 仅支持单人 | 引入 Socket/WebSocket 实现联机对战 |
| **移动端** | 仅支持键鼠 | 适配触摸操作，发布 Android/iOS 版本 |
| **新建筑** | 仅 4 种基础建筑 | 增加陷阱/传送门/隐身装置等 |
| **模式** | 仅双阵营对抗 | 增加合作防守/无尽模式/自定义房间 |

---

## 附录：阅读顺序建议

如果你是想学习这个项目，推荐以下阅读顺序：

1. **[core/config.py](core/config.py)** → 5 分钟，建立数据维度
2. **[entities/entities.py](entities/entities.py)** → 15 分钟，掌握核心数据结构
3. **[world/map_data.py](world/map_data.py)** → 30 分钟，理解地图生成 + A* 寻路
4. **[core/game_state.py](core/game_state.py)** → 15 分钟，看清全局状态
5. **[systems/systems.py](systems/systems.py)** → 60 分钟，**最核心的逻辑**
6. **[main.py](main.py)** → 30 分钟，主循环串联一切
7. **[graphics/renderer.py](graphics/renderer.py)** → 20 分钟，程序化纹理 + 顶视渲染
8. **[ui/ui_menu.py](ui/ui_menu.py) / [ui/ui_hud.py](ui/ui_hud.py) / [ui/ui_camera.py](ui/ui_camera.py) / [ui/input_router.py](ui/input_router.py) / [graphics/effects.py](graphics/effects.py)** → 各 10 分钟，UI/输入/特效

---

**项目版本**：v1.1（2026 年 6 月，已回归 2D 顶视）  
**开发环境**：Windows + Python 3.12 + Pygame 2.6  
**代码许可**：项目内代码仅供学习参考
