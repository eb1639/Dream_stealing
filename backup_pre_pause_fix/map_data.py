"""
地图网格定义、9个不规则房间模板、A*寻路
"""
import random
import heapq
from config import *


class RoomTemplate:
    """矩形房间模板"""
    def __init__(self, room_id, cells, door_col, door_row, door_dir='right'):
        self.id = room_id
        self.cells = set(cells)
        self.door_col = door_col
        self.door_row = door_row
        self.door_dir = door_dir

        self.min_col = min(c[0] for c in cells)
        self.max_col = max(c[0] for c in cells)
        self.min_row = min(c[1] for c in cells)
        self.max_row = max(c[1] for c in cells)
        self.w = self.max_col - self.min_col + 1
        self.h = self.max_row - self.min_row + 1

        self.door_exit = self._get_door_exit()
        self.door_approach = self._get_door_approach()
        self.interior = list(self.cells)

    def _get_door_exit(self):
        """门外第一格（紧邻门）"""
        if self.door_dir == 'right':
            return (self.door_col + 1, self.door_row)
        elif self.door_dir == 'left':
            return (self.door_col - 1, self.door_row)
        elif self.door_dir == 'up':
            return (self.door_col, self.door_row - 1)
        else:
            return (self.door_col, self.door_row + 1)

    def _get_door_approach(self):
        """门前两格（door_exit + 再往外一格），保证门前畅通"""
        e1 = self.door_exit
        if self.door_dir == 'right':
            return [e1, (e1[0] + 1, e1[1])]
        elif self.door_dir == 'left':
            return [e1, (e1[0] - 1, e1[1])]
        elif self.door_dir == 'up':
            return [e1, (e1[0], e1[1] - 1)]
        else:
            return [e1, (e1[0], e1[1] + 1)]

    def contains(self, col, row):
        return (col, row) in self.cells

    @property
    def bounds(self):
        return self.min_col, self.min_row, self.w, self.h

    @property
    def door_pos(self):
        return self.door_col, self.door_row


# ============================================================
# 9个矩形房间模板
# ============================================================
# 地图尺寸: 32x26
# 格式: (id, col, row, w, h, door_c, door_r)
# 地图宽度 33 (0-32), 高度 26
# 空间: 左(1-6) 墙(7) 走廊(8-9) 墙(10) 中左(11-14) 墙(15) 中心(16-21) 墙(22) 走廊(23-24) 墙(25) 右(26-31)
#       6宽      1      2宽      1      4宽       1      6宽        1       2宽      1      6宽

ROOM_DEFS = [
    # id, col, row, w,  h,  door_c, door_r
    (0,   1,   2,  5,   4,  5,     3),      # 左上 → door_exit(6,3), approach(7,3)
    (1,  26,   2,  5,   4,  26,    3),      # 右上 → door_exit(25,3), approach(24,3)
    (2,  16,   2,  6,   3,  19,    4),      # 中上 → door_exit(19,5), approach(19,6)
    (3,   1,  11,  5,   4,  5,    13),      # 左中 → door_exit(6,13), approach(7,13)
    (4,  26,  11,  5,   4,  26,   13),      # 右中 → door_exit(25,13), approach(24,13)
    (5,  11,  10,  4,   3,  13,   12),      # 中左 → door_exit(13,13), approach(13,14)
    (6,  16,  10,  4,   3,  18,   12),      # 中右 → door_exit(18,13), approach(18,14)
    (7,   1,  19,  6,   4,  5,    19),      # 左下 → door_exit(5,18), approach(5,17)
    (8,  26,  19,  6,   4,  27,   19),      # 右下 → door_exit(27,18), approach(27,17)
]


def build_map():
    """
    构建网格：矩形房间 + 四边四角墙壁 + 门前两格无墙 + 2格宽走廊。
    先定义走廊区域，再放墙，避免走廊挖掘破坏墙壁。
    """
    grid = [[TILE_EMPTY for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
    rooms = []

    for room_id, col, row, w, h, door_c, door_r in ROOM_DEFS:
        cells = [(c, r) for r in range(row, row + h) for c in range(col, col + w)]
        if door_c == col:
            door_dir = 'left'
        elif door_c == col + w - 1:
            door_dir = 'right'
        elif door_r == row:
            door_dir = 'up'
        else:
            door_dir = 'down'
        room = RoomTemplate(room_id, cells, door_c, door_r, door_dir)
        rooms.append(room)

    # ── 收集"不可放墙"的格子 ──
    room_cells = set()
    door_cells = set()
    door_approach_cells = set()
    for room in rooms:
        for cx, cy in room.cells:
            room_cells.add((cx, cy))
        door_cells.add(room.door_pos)
        for ac, ar in room.door_approach:
            if 0 <= ac < MAP_COLS and 0 <= ar < MAP_ROWS:
                door_approach_cells.add((ac, ar))

    # 预定义2格宽走廊区域 (cols 8-9 左, cols 23-24 右; rows 7-8 顶部横, rows 16-17 中部横)
    corridor_cells = set()
    for r in range(1, MAP_ROWS - 1):
        corridor_cells.update([(8, r), (9, r), (23, r), (24, r)])
    for c in range(MAP_COLS):
        corridor_cells.update([(c, 7), (c, 8), (c, 16), (c, 17)])

    # 门前两格也视为走廊(已在上面的door_approach中)
    # 合并: 不可放墙 = 房间内部 + 门 + 走廊
    no_wall = room_cells | door_cells | door_approach_cells | corridor_cells

    # ── 标记房间和门 ──
    for cx, cy in room_cells:
        grid[cy][cx] = TILE_ROOM
    for cx, cy in door_cells:
        if 0 <= cx < MAP_COLS and 0 <= cy < MAP_ROWS:
            grid[cy][cx] = TILE_DOOR

    # ── 在每个房间完整外围放墙(四边+四角) ──
    for room in rooms:
        min_c, max_c = room.min_col, room.max_col
        min_r, max_r = room.min_row, room.max_row
        # 上边 + 下边 (含四角)
        for c in range(min_c - 1, max_c + 2):
            for r in (min_r - 1, max_r + 1):
                if 0 <= c < MAP_COLS and 0 <= r < MAP_ROWS:
                    if (c, r) not in no_wall:
                        grid[r][c] = TILE_WALL
        # 左边 + 右边 (不含角, 角已被上下边覆盖)
        for r in range(min_r, max_r + 1):
            for c in (min_c - 1, max_c + 1):
                if 0 <= c < MAP_COLS and 0 <= r < MAP_ROWS:
                    if (c, r) not in no_wall:
                        grid[r][c] = TILE_WALL

    # ── 确保门前两格与走廊均为空地 ──
    for cx, cy in door_approach_cells | corridor_cells:
        if 0 <= cx < MAP_COLS and 0 <= cy < MAP_ROWS:
            if grid[cy][cx] == TILE_WALL:
                grid[cy][cx] = TILE_EMPTY

    # ── 外墙边界 ──
    for c in range(MAP_COLS):
        if grid[0][c] == TILE_EMPTY:
            grid[0][c] = TILE_WALL
        if grid[MAP_ROWS - 1][c] == TILE_EMPTY:
            grid[MAP_ROWS - 1][c] = TILE_WALL
    for r in range(MAP_ROWS):
        if grid[r][0] == TILE_EMPTY:
            grid[r][0] = TILE_WALL
        if grid[r][MAP_COLS - 1] == TILE_EMPTY:
            grid[r][MAP_COLS - 1] = TILE_WALL

    return grid, rooms


def is_walkable_for(grid, col, row, entity_type, door_hp_map=None, rooms=None):
    """检查某格是否可通行"""
    if col < 0 or col >= MAP_COLS or row < 0 or row >= MAP_ROWS:
        return False
    tile = grid[row][col]

    if entity_type == 'hunter':
        if tile == TILE_EMPTY or tile == TILE_FOUNTAIN:
            return True
        if tile == TILE_ROOM:
            if rooms is not None:
                for room in rooms:
                    if room.contains(col, row):
                        if door_hp_map:
                            dc, dr = room.door_pos
                            hp = door_hp_map.get((dc, dr), 1)
                            return hp <= 0
                        return True
            return True
        if tile == TILE_DOOR:
            if door_hp_map:
                hp = door_hp_map.get((col, row), 1)
                return hp <= 0
            return False
        return False

    if entity_type == 'human_wandering':
        return tile in (TILE_EMPTY, TILE_DOOR, TILE_ROOM, TILE_BED)

    if entity_type == 'human_bed':
        return False

    return False


def get_neighbors(col, row):
    """四方向邻居"""
    return [(col, row-1), (col, row+1), (col-1, row), (col+1, row)]


def heuristic(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def astar(grid, start, goal, walkable_check, door_hp_map=None, rooms=None):
    """A*寻路"""
    if start == goal:
        return []

    frontier = []
    heapq.heappush(frontier, (0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}

    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal:
            break
        for nxt in get_neighbors(*current):
            if not is_walkable_for(grid, nxt[0], nxt[1], walkable_check, door_hp_map, rooms):
                continue
            new_cost = cost_so_far[current] + 1
            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                cost_so_far[nxt] = new_cost
                priority = new_cost + heuristic(goal, nxt)
                heapq.heappush(frontier, (priority, nxt))
                came_from[nxt] = current

    if goal not in came_from:
        return []

    path = []
    cur = goal
    while cur != start:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    return path


def find_path(grid, start, goal, entity_type, door_hp_map=None, rooms=None):
    return astar(grid, start, goal, entity_type, door_hp_map, rooms)


def get_room_by_id(rooms, room_id):
    for r in rooms:
        if r.id == room_id:
            return r
    return None


def get_room_at(rooms, col, row):
    """返回(col,row)所在的房间"""
    for room in rooms:
        if room.contains(col, row):
            return room
    return None


def get_door_adjacent_corridor(room, grid):
    """获取门邻接的走廊格子"""
    return room.door_exit


def get_fountain_positions(grid):
    """泉水位置"""
    edge = random.choice(['top', 'bottom', 'left', 'right'])
    positions = []
    attempts = 0
    while attempts < 200:
        attempts += 1
        if edge == 'top':
            c = random.randint(6, MAP_COLS-8)
            r = 1
        elif edge == 'bottom':
            c = random.randint(6, MAP_COLS-8)
            r = MAP_ROWS - 3
        elif edge == 'left':
            c = 1
            r = random.randint(6, MAP_ROWS-8)
        else:
            c = MAP_COLS - 3
            r = random.randint(6, MAP_ROWS-8)

        positions = [(c, r), (c+1, r), (c, r+1), (c+1, r+1)]
        ok = True
        for pc, pr in positions:
            if not (0 <= pc < MAP_COLS and 0 <= pr < MAP_ROWS):
                ok = False
                break
            if grid[pr][pc] != TILE_EMPTY:
                ok = False
                break
        if ok:
            break
    else:
        positions = [(15, 1), (16, 1), (15, 2), (16, 2)]
    return positions


def place_fountain(grid, positions):
    for c, r in positions:
        grid[r][c] = TILE_FOUNTAIN


def get_spawn_point():
    """人类出生点"""
    return MAP_COLS // 2, 7