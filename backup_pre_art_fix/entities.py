"""
人类、猎梦者、建筑数据类
"""
import math
from config import *


class Human:
    def __init__(self, human_id, is_player, color, grid_col, grid_row):
        self.id = human_id
        self.is_player = is_player
        self.color = color
        self.gold = HUMAN_INIT_GOLD
        self.state = HUMAN_WANDERING
        self.room_id = None

        # 网格位置
        self.grid_col = grid_col
        self.grid_row = grid_row
        # 像素位置(用于平滑移动)
        self.px = grid_col * TILE_SIZE + TILE_SIZE // 2
        self.py = grid_row * TILE_SIZE + TILE_SIZE // 2
        self.target_px = self.px
        self.target_py = self.py

        self.speed = HUMAN_SPEED * TILE_SIZE  # px/秒
        self.move_path = []  # 寻路路径
        self.move_timer = 0.0  # 移动间隔计时器
        self.decision_timer = 2.0  # AI决策计时器(初始短一些)
        self.is_under_attack = False

    @property
    def pos(self):
        return self.grid_col, self.grid_row

    @property
    def alive(self):
        return self.state != HUMAN_DEAD

    def kill(self):
        self.state = HUMAN_DEAD

    def set_bed(self, room_id, grid_col, grid_row):
        self.state = HUMAN_BED
        self.room_id = room_id
        self.grid_col = grid_col
        self.grid_row = grid_row
        self.px = grid_col * TILE_SIZE + TILE_SIZE // 2
        self.py = grid_row * TILE_SIZE + TILE_SIZE // 2


class DreamHunter:
    def __init__(self, is_player, grid_col, grid_row):
        self.is_player = is_player
        self.level = 0  # 索引0 = Lv1
        self.cumulative_damage = 0  # 累计造成伤害
        self.current_hp = HUNTER_MAX_HP[0]
        self.attack_cooldown = 0.0
        self.fleeing = False

        self.grid_col = grid_col
        self.grid_row = grid_row
        self.px = grid_col * TILE_SIZE + TILE_SIZE // 2
        self.py = grid_row * TILE_SIZE + TILE_SIZE // 2
        self.target_px = self.px
        self.target_py = self.py

        self.speed = HUNTER_SPEED[0] * TILE_SIZE
        self.move_path = []
        self.move_timer = 0.0
        self.target_room_id = None
        self.at_fountain = False

    @property
    def max_hp(self):
        return HUNTER_MAX_HP[self.level]

    @property
    def atk(self):
        return HUNTER_ATK[self.level]

    @property
    def atk_speed(self):
        return HUNTER_ATK_SPEED[self.level]

    @property
    def speed_val(self):
        return HUNTER_SPEED[self.level] * TILE_SIZE

    @property
    def regen_rate(self):
        return HUNTER_FOUNTAIN_REGEN[self.level]

    @property
    def pos(self):
        return self.grid_col, self.grid_row

    @property
    def alive(self):
        return self.current_hp > 0

    @property
    def flee_threshold(self):
        return int(self.max_hp * HUNTER_FLEE_HP_RATIO)

    def add_damage(self, amount):
        """造成伤害, 返回是否升级"""
        self.cumulative_damage += amount
        # 检查升级
        for i in range(self.level + 1, len(HUNTER_THRESHOLDS)):
            if self.cumulative_damage >= HUNTER_THRESHOLDS[i]:
                self.level = i
                self.current_hp = self.max_hp  # 升级回满血
                self.speed = HUNTER_SPEED[self.level] * TILE_SIZE
                self.fleeing = False
                return True
        return False

    def take_damage(self, amount):
        self.current_hp -= amount
        if self.current_hp < 0:
            self.current_hp = 0

    def heal(self, amount):
        self.current_hp = min(self.current_hp + amount, self.max_hp)

    @property
    def is_full_hp(self):
        return self.current_hp >= self.max_hp


class Bullet:
    def __init__(self, px, py, target_hunter, damage):
        self.px = float(px)
        self.py = float(py)
        self.target = target_hunter
        self.damage = damage
        self.speed = BULLET_SPEED
        self.alive = True

    def update(self, dt):
        """移动子弹, 到达目标时返回True"""
        tx = self.target.px
        ty = self.target.py
        dx = tx - self.px
        dy = ty - self.py
        dist = math.hypot(dx, dy)
        if dist < 8:
            self.alive = False
            return True  # 命中
        move = self.speed * dt
        if move >= dist:
            self.px = tx
            self.py = ty
            self.alive = False
            return True
        self.px += dx / dist * move
        self.py += dy / dist * move
        return False


class Building:
    """房间内的建筑: 门/床/炮塔/维修台"""
    _next_uid = 1  # 类级自增 ID，避免 id() 复用隐患

    def __init__(self, btype, grid_col, grid_row, room_id):
        self.uid = Building._next_uid  # 唯一稳定标识
        Building._next_uid += 1
        self.type = btype
        self.grid_col = grid_col
        self.grid_row = grid_row
        self.room_id = room_id
        self.level = 0  # 索引0 = Lv1

        # 门专属
        self.current_hp = DOOR_MAX_HP[0] if btype == BLDG_DOOR else 0
        self.being_repaired = False  # 当前帧是否被维修中

        # 炮塔专属（避免懒初始化）
        if btype == BLDG_TURRET:
            self._cooldown = 0.0

    @property
    def pos(self):
        return self.grid_col, self.grid_row

    @property
    def px_center(self):
        return self.grid_col * TILE_SIZE + TILE_SIZE // 2, self.grid_row * TILE_SIZE + TILE_SIZE // 2

    @property
    def max_hp(self):
        if self.type == BLDG_DOOR:
            return DOOR_MAX_HP[self.level]
        return 0

    @property
    def alive(self):
        if self.type == BLDG_DOOR:
            return self.current_hp > 0
        return True

    def upgrade_cost(self):
        if self.type == BLDG_DOOR:
            if self.level + 1 >= len(DOOR_UPGRADE_COST):
                return None
            return DOOR_UPGRADE_COST[self.level + 1]
        elif self.type == BLDG_BED:
            if self.level + 1 >= len(BED_UPGRADE_COST):
                return None
            return BED_UPGRADE_COST[self.level + 1]
        elif self.type == BLDG_TURRET:
            if self.level + 1 >= len(TURRET_UPGRADE_COST):
                return None
            return TURRET_UPGRADE_COST[self.level + 1]
        elif self.type == BLDG_REPAIR:
            if self.level + 1 >= len(REPAIR_UPGRADE_COST):
                return None
            return REPAIR_UPGRADE_COST[self.level + 1]
        return None

    def can_upgrade(self):
        return self.upgrade_cost() is not None

    def upgrade(self):
        """执行升级, 返回新等级"""
        if not self.can_upgrade():
            return self.level
        self.level += 1
        if self.type == BLDG_DOOR:
            self.current_hp = self.max_hp  # 升级回满血
        return self.level

    @property
    def bed_gold_rate(self):
        if self.type == BLDG_BED:
            return BED_GOLD_PER_SEC[self.level]
        return 0

    @property
    def turret_dps(self):
        if self.type == BLDG_TURRET:
            return TURRET_DPS[self.level]
        return 0

    @property
    def turret_range(self):
        if self.type == BLDG_TURRET:
            return TURRET_RANGE[self.level]
        return 0

    @property
    def turret_atk_speed(self):
        if self.type == BLDG_TURRET:
            return TURRET_ATK_SPEED[self.level]
        return 0

    @property
    def repair_hps(self):
        if self.type == BLDG_REPAIR:
            return REPAIR_HPS[self.level]
        return 0

    def take_damage(self, amount):
        if self.type == BLDG_DOOR:
            self.current_hp -= amount
            if self.current_hp < 0:
                self.current_hp = 0

    def repair(self, amount):
        if self.type == BLDG_DOOR and self.current_hp > 0:
            self.current_hp = min(self.current_hp + amount, self.max_hp)
