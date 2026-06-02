"""
GameState — 全局游戏状态数据容器
"""
import random
from config import *
from map_data import *
from entities import *


class GameState:
    def __init__(self):
        self.phase = PHASE_MENU
        self.mode = MODE_HUMAN
        self.safe_timer = SAFE_TIME
        self.game_time = 0.0
        self.victory = False
        self.paused = False

        # 地图
        self.grid = None
        self.rooms = []
        self.fountain_positions = []

        # 实体
        self.humans = []          # list[Human]
        self.player_human = None  # Human or None
        self.dream_hunter = None  # DreamHunter
        self.bullets = []         # list[Bullet]

        # 建筑索引: {(room_id, btype): Building} 或按房间查找
        self.buildings = []       # list[Building] 所有建筑
        # 快捷查找: {(col, row): Building}
        self.building_at = {}

        # AI房间预订(防止多人抢同一房, 与room_id解耦)
        self.reserved_room_ids = set()

        # 飘字特效（每局重置）
        self.damage_numbers = []
        self.gold_numbers = []
        self.heal_numbers = []

        # 维修台累积器（用 building uid 作 key，避免 id() 复用隐患）
        self._repair_accum = {}
        self._repair_disp_accum = {}
        self._repair_disp_timer = {}

        # UI 临时缓存（由 renderer / ui_hud 写入，main 读取）
        self.popup_menu = None
        self.avatar_rects = {}
        self.hunter_avatar_rect = None
        self._pause_btn_rect = None
        self._pause_menu_rects = None
        self._pause_menu_open = False

        # 渲染缓存（由 renderer 写入，input_router 读取）
        self._scale = 1.0
        self._game_area_x = 0
        self._game_area_y = HUD_HEIGHT

    # ─── 初始化 ───

    def init_game(self, mode):
        self.phase = PHASE_INIT
        self.mode = mode
        self.safe_timer = SAFE_TIME
        self.game_time = 0.0
        self.victory = False
        self.paused = False
        self.bullets = []
        self.buildings = []
        self.building_at = {}
        self.player_human = None
        self.reserved_room_ids = set()

        # 重置飘字特效（防止上一局残留）
        self.damage_numbers = []
        self.gold_numbers = []
        self.heal_numbers = []

        # 重置维修台累积器（防止上一局 door uid 残留）
        self._repair_accum = {}
        self._repair_disp_accum = {}
        self._repair_disp_timer = {}

        # 重置 UI 临时缓存（防止旧菜单/旧按钮区域残留）
        self.popup_menu = None
        self.avatar_rects = {}
        self.hunter_avatar_rect = None
        self._pause_btn_rect = None
        self._pause_menu_rects = None
        self._pause_menu_open = False

        # 生成地图
        self.grid, self.rooms = build_map()

        # 泉水
        fountain = get_fountain_positions(self.grid)
        self.fountain_positions = fountain
        place_fountain(self.grid, fountain)

        # 创建人类
        self.humans = []
        spawn_col, spawn_row = get_spawn_point()
        colors = [PLAYER_COLOR] + AI_HUMAN_COLORS
        for i in range(6):
            is_player = (i == 0) if mode == MODE_HUMAN else False
            offset_c = random.randint(-2, 2)
            offset_r = random.randint(-2, 2)
            hc = spawn_col + offset_c
            hr = spawn_row + offset_r
            # 确保出生在走廊
            if not (0 <= hc < MAP_COLS and 0 <= hr < MAP_ROWS):
                hc, hr = spawn_col, spawn_row
            if self.grid[hr][hc] != TILE_EMPTY:
                hc, hr = spawn_col, spawn_row
            human = Human(i, is_player, colors[i], hc, hr)
            self.humans.append(human)
            if is_player:
                self.player_human = human

        # 创建猎梦者
        f_center = fountain[0]  # 泉水第一格
        hunter = DreamHunter(mode == MODE_HUNTER, f_center[0], f_center[1])
        self.dream_hunter = hunter

        # 猎梦者初始位于泉水
        hunter.at_fountain = True

        # 初始化房间建筑(门和床)
        for room in self.rooms:
            # 门
            dc, dr = room.door_pos
            door = Building(BLDG_DOOR, dc, dr, room.id)
            self.buildings.append(door)
            self.building_at[(dc, dr)] = door

            # 床: 房间内部随机空位(排除门相邻)
            interior = list(room.cells)
            random.shuffle(interior)
            bed_placed = False
            for bc, br in interior:
                # 不放在门格和门相邻格
                if (bc, br) == (dc, dr):
                    continue
                if abs(bc - dc) + abs(br - dr) <= 1:
                    continue
                bed_placed = True
                bed = Building(BLDG_BED, bc, br, room.id)
                self.buildings.append(bed)
                self.building_at[(bc, br)] = bed
                self.grid[br][bc] = TILE_BED
                break
            if not bed_placed:
                # 保底: 随便放一个位置
                for bc, br in interior:
                    if (bc, br) != (dc, dr):
                        bed = Building(BLDG_BED, bc, br, room.id)
                        self.buildings.append(bed)
                        self.building_at[(bc, br)] = bed
                        self.grid[br][bc] = TILE_BED
                        break

        # AI人类分配目标房间
        self._assign_ai_rooms()

        self.phase = PHASE_SAFE

    def _assign_ai_rooms(self):
        """AI人类随机分配未占用的房间, 使用reserved_room_ids防止抢房"""
        available = [r for r in self.rooms if r.id not in self.reserved_room_ids]
        random.shuffle(available)
        for human in self.humans:
            if human.is_player and self.mode == MODE_HUMAN:
                continue
            if not available:
                break
            # 尝试分配直到找到可达的房间
            assigned = False
            for _ in range(len(available)):
                room = available.pop(0)
                bed = self.get_bed_in_room(room.id)
                if bed:
                    bc, br = bed.pos
                    path = find_path(self.grid, human.pos, (bc, br), 'human_wandering')
                    if path:
                        human.move_path = path
                        human.room_id = room.id
                        self.reserved_room_ids.add(room.id)
                        assigned = True
                        break
                    else:
                        # 不可达, 放回池中给其他人
                        available.append(room)
                else:
                    available.append(room)
            if not assigned:
                # 该AI未分配到房间, 后续_assign_room_to_ai兜底
                pass

    # ─── 查询 ───

    def get_bed_in_room(self, room_id):
        for b in self.buildings:
            if b.type == BLDG_BED and b.room_id == room_id:
                return b
        return None

    def get_door_in_room(self, room_id):
        for b in self.buildings:
            if b.type == BLDG_DOOR and b.room_id == room_id:
                return b
        return None

    def get_buildings_in_room(self, room_id):
        return [b for b in self.buildings if b.room_id == room_id]

    def get_turrets_in_room(self, room_id):
        return [b for b in self.buildings if b.type == BLDG_TURRET and b.room_id == room_id]

    def get_repairs_in_room(self, room_id):
        return [b for b in self.buildings if b.type == BLDG_REPAIR and b.room_id == room_id]

    def get_human_in_room(self, room_id):
        for h in self.humans:
            if h.room_id == room_id and h.alive and h.state == HUMAN_BED:
                return h
        return None

    def get_building_at(self, col, row):
        return self.building_at.get((col, row))

    def get_human_by_id(self, human_id):
        for h in self.humans:
            if h.id == human_id:
                return h
        return None

    def living_humans(self):
        return [h for h in self.humans if h.alive]

    def get_alive_ai_humans(self):
        return [h for h in self.humans if h.alive and not h.is_player]

    def get_unbroken_doors(self):
        return [b for b in self.buildings if b.type == BLDG_DOOR and b.current_hp > 0]

    def get_broken_doors(self):
        return [b for b in self.buildings if b.type == BLDG_DOOR and b.current_hp <= 0]

    def is_game_over(self):
        return self.phase in (PHASE_VICTORY, PHASE_DEFEAT)

    def is_room_door_broken(self, room_id):
        door = self.get_door_in_room(room_id)
        return door is not None and door.current_hp <= 0

    def get_room_of_door(self, door_building):
        return get_room_by_id(self.rooms, door_building.room_id)

    def any_human_alive(self):
        return any(h.alive for h in self.humans)
