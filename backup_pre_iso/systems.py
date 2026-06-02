"""
经济定时器、战斗检测、AI决策
"""
import random
import math
from core.config import *
from world.map_data import *
from entities.entities import *


# ─── 经济系统 ───

def update_economy(game_state, dt):
    """每秒产出金币(由main循环中累计timer触发)"""
    for human in game_state.humans:
        if human.state != HUMAN_BED or not human.alive:
            continue
        bed = game_state.get_bed_in_room(human.room_id)
        if bed is None:
            continue
        human.gold += bed.bed_gold_rate


# ─── 战斗系统 ───

def update_combat(game_state, dt):
    """更新所有战斗逻辑"""
    hunter = game_state.dream_hunter
    if hunter is None:
        return

    # 1. 猎梦者攻击门
    if hunter.attack_cooldown > 0:
        hunter.attack_cooldown -= dt
    else:
        _hunter_attack_door(game_state)

    # 2. 炮塔攻击猎梦者
    _turrets_attack(game_state, dt)

    # 3. 猎梦者触碰秒杀(走廊人类 / 破门后床上人类)
    _hunter_kill_check(game_state)

    # 4. 猎梦者回血(在泉水)
    if hunter.at_fountain:
        hunter.heal(int(hunter.regen_rate * dt))
        if hunter.is_full_hp:
            hunter.fleeing = False

    # 5. 更新子弹
    _update_bullets(game_state, dt)

    # 6. 维修台回血
    _update_repair(game_state, dt)


def _hunter_attack_door(game_state):
    """猎梦者攻击相邻的门"""
    hunter = game_state.dream_hunter
    hc, hr = hunter.pos

    # 检查四方向是否有门
    for nc, nr in get_neighbors(hc, hr):
        building = game_state.get_building_at(nc, nr)
        if building and building.type == BLDG_DOOR and building.current_hp > 0:
            # 攻击!
            building.take_damage(hunter.atk)
            hunter.add_damage(hunter.atk)
            hunter.attack_cooldown = 1.0 / hunter.atk_speed

            # 标记门所在房间的人被攻击
            room_human = game_state.get_human_in_room(building.room_id)
            if room_human:
                room_human.is_under_attack = True

            # 播放伤害特效标记
            _spawn_damage_number(game_state, nc, nr, hunter.atk)
            break


def _turrets_attack(game_state, dt):
    """所有炮塔攻击范围内的猎梦者"""
    hunter = game_state.dream_hunter
    if not hunter.alive:
        return

    for turret in game_state.buildings:
        if turret.type != BLDG_TURRET:
            continue
        # 冷却（在 Building.__init__ 中已初始化为 0.0）
        turret._cooldown -= dt
        if turret._cooldown > 0:
            continue

        # 检查猎梦者是否在射程内
        tc, tr = turret.pos
        hc, hr = hunter.pos
        dist = math.hypot(hc - tc, hr - tr)
        if dist <= turret.turret_range:
            # 检查猎梦者是否可被攻击(在走廊或在破门房间内)
            if _can_turret_hit_hunter(game_state, hunter, turret):
                turret._cooldown = 1.0 / turret.turret_atk_speed
                # 发射子弹
                tpx, tpy = turret.px_center
                bullet = Bullet(tpx, tpy, hunter, turret.turret_dps)
                game_state.bullets.append(bullet)


def _can_turret_hit_hunter(game_state, hunter, turret):
    """炮塔能否打到猎梦者: 猎梦者在走廊或在破门的房间内"""
    hc, hr = hunter.pos
    tile = game_state.grid[hr][hc]
    if tile == TILE_EMPTY or tile == TILE_FOUNTAIN:
        return True  # 走廊/泉水
    if tile == TILE_ROOM:
        # 检查该房间门是否已破
        room = get_room_at(game_state.rooms, hc, hr)
        if room and game_state.is_room_door_broken(room.id):
            return True
    return False


def _hunter_kill_check(game_state):
    """猎梦者触碰人类=秒杀"""
    hunter = game_state.dream_hunter
    hc, hr = hunter.pos

    for human in game_state.humans:
        if not human.alive:
            continue
        # 检查是否同格或相邻
        if abs(human.grid_col - hc) <= 1 and abs(human.grid_row - hr) <= 1:
            if human.state == HUMAN_WANDERING:
                # 走廊上触碰秒杀
                human.kill()
            elif human.state == HUMAN_BED:
                # 检查门是否已破
                if human.room_id is not None:
                    if game_state.is_room_door_broken(human.room_id):
                        # 门破且猎梦者在房间内
                        room = get_room_at(game_state.rooms, hc, hr)
                        if room and room.id == human.room_id:
                            human.kill()


def _update_bullets(game_state, dt):
    """更新子弹位置, 处理命中"""
    for bullet in game_state.bullets[:]:
        hit = bullet.update(dt)
        if hit:
            bullet.target.take_damage(bullet.damage)
            game_state.bullets.remove(bullet)
        elif not bullet.alive:
            game_state.bullets.remove(bullet)


def _update_repair(game_state, dt):
    """维修台回血: 门血量不满时持续维修, 按等级计算回血量"""
    for human in game_state.humans:
        if not human.alive or human.state != HUMAN_BED or human.room_id is None:
            continue
        door = game_state.get_door_in_room(human.room_id)
        if door is None or door.current_hp <= 0:
            continue
        if door.current_hp >= door.max_hp:
            for d in (game_state._repair_accum, game_state._repair_disp_accum, game_state._repair_disp_timer):
                d.pop(door.uid, None)
            continue
        repairs = game_state.get_repairs_in_room(human.room_id)
        if not repairs:
            continue
        total_heal = 0.0
        for repair in repairs:
            total_heal += repair.repair_hps * dt
        door_key = door.uid  # 使用稳定 uid，避免 id() 复用
        # HP累积(不丢失小数)
        acc = game_state._repair_accum.get(door_key, 0.0) + total_heal
        if acc >= 1.0:
            heal_int = int(acc)
            door.repair(heal_int)
            door.being_repaired = True
            acc -= heal_int
        game_state._repair_accum[door_key] = acc
        # 每秒飘字汇总
        disp_acc = game_state._repair_disp_accum.get(door_key, 0.0) + total_heal
        disp_timer = game_state._repair_disp_timer.get(door_key, 0.0) + dt
        if disp_timer >= 1.0:
            if disp_acc >= 1.0:
                _spawn_heal_number(game_state, door.grid_col, door.grid_row, int(disp_acc))
            disp_acc = 0.0
            disp_timer -= 1.0
        game_state._repair_disp_accum[door_key] = disp_acc
        game_state._repair_disp_timer[door_key] = disp_timer


def _spawn_damage_number(game_state, col, row, damage):
    """记录伤害数字(由effects.py渲染)"""
    if not hasattr(game_state, 'damage_numbers'):
        game_state.damage_numbers = []
    game_state.damage_numbers.append({
        'col': col, 'row': row,
        'value': damage,
        'timer': 1.0,
        'color': RED,
    })


def _spawn_heal_number(game_state, col, row, amount):
    """记录回血数字(由effects.py渲染)"""
    if not hasattr(game_state, 'heal_numbers'):
        game_state.heal_numbers = []
    game_state.heal_numbers.append({
        'col': col, 'row': row,
        'value': f'+{amount}',
        'timer': 1.0,
        'color': GREEN,
    })


def spawn_gold_number(game_state, col, row, amount):
    """记录金币飘字"""
    if not hasattr(game_state, 'gold_numbers'):
        game_state.gold_numbers = []
    game_state.gold_numbers.append({
        'col': col, 'row': row,
        'value': f'+{amount}',
        'timer': 1.0,
        'color': YELLOW,
    })


# ─── AI 系统 ───

def update_ai(game_state, dt):
    """更新所有AI决策"""
    # AI人类决策
    for human in game_state.humans:
        if not human.alive or human.is_player:
            continue
        if human.state != HUMAN_BED:
            continue
        human.decision_timer -= dt
        if human.decision_timer <= 0:
            _ai_human_decide(game_state, human)
            human.decision_timer = random.uniform(AI_DECISION_MIN, AI_DECISION_MAX)

    # AI猎梦者决策(仅人类模式)
    if (game_state.mode == MODE_HUMAN and game_state.dream_hunter
            and not game_state.dream_hunter.is_player):
        _ai_hunter_decide(game_state)


def _ai_human_decide(game_state, human):
    """AI人类决策: 优先升级床 > 门 > 建炮塔 > 建维修台 > 升级炮塔"""
    room_id = human.room_id
    if room_id is None:
        return

    bed = game_state.get_bed_in_room(room_id)
    door = game_state.get_door_in_room(room_id)
    turrets = game_state.get_turrets_in_room(room_id)
    repairs = game_state.get_repairs_in_room(room_id)
    room = get_room_by_id(game_state.rooms, room_id)
    if room is None:
        return

    # 房间空位(排除建筑和床)
    occupied = set()
    for b in game_state.get_buildings_in_room(room_id):
        occupied.add(b.pos)
    empty_tiles = [(c, r) for c, r in room.interior if (c, r) not in occupied]

    # 1. 升级床(优先)
    if bed and bed.can_upgrade():
        cost = bed.upgrade_cost()
        if human.gold >= cost:
            human.gold -= cost
            bed.upgrade()

    # 2. 升级门(门等级 < 床等级)
    if door and door.can_upgrade() and bed:
        if door.level < bed.level:
            cost = door.upgrade_cost()
            if human.gold >= cost:
                human.gold -= cost
                door.upgrade()

    # 3. 建造炮塔
    turret_cost = TURRET_UPGRADE_COST[0]
    if empty_tiles and len(turrets) < 3 and human.gold >= turret_cost:
        tc, tr = random.choice(empty_tiles)
        human.gold -= turret_cost
        turret = Building(BLDG_TURRET, tc, tr, room_id)
        game_state.buildings.append(turret)
        game_state.building_at[(tc, tr)] = turret
        empty_tiles.remove((tc, tr))

    # 4. 建造维修台
    if empty_tiles and len(repairs) < 2 and human.gold >= REPAIR_COST and turrets:
        rc_, rr_ = random.choice(empty_tiles)
        human.gold -= REPAIR_COST
        repair = Building(BLDG_REPAIR, rc_, rr_, room_id)
        game_state.buildings.append(repair)
        game_state.building_at[(rc_, rr_)] = repair

    # 5. 升级炮塔
    for turret in turrets:
        if turret.can_upgrade() and bed and turret.level < bed.level:
            cost = turret.upgrade_cost()
            if human.gold >= cost:
                human.gold -= cost
                turret.upgrade()


def _ai_hunter_decide(game_state):
    """AI猎梦者决策: 选最低等级门攻击, 残血回泉水, 破门后追击人类"""
    hunter = game_state.dream_hunter
    if hunter is None or not hunter.alive:
        return

    # 残血逃跑
    if hunter.current_hp <= hunter.flee_threshold:
        hunter.fleeing = True

    # 在泉水回血中
    if hunter.fleeing:
        if hunter.at_fountain and hunter.is_full_hp:
            hunter.fleeing = False
            hunter.target_room_id = None
        elif not hunter.at_fountain:
            _hunter_move_to_fountain(game_state)
        return

    door_hp_map = {(b.grid_col, b.grid_row): b.current_hp
                   for b in game_state.buildings if b.type == BLDG_DOOR}

    # ── 门已破, 进入房间追击人类 ──
    if hunter.target_room_id is not None:
        door = game_state.get_door_in_room(hunter.target_room_id)
        room_human = game_state.get_human_in_room(hunter.target_room_id)
        if door is not None and door.current_hp <= 0 and room_human is not None:
            # 寻找人类附近可通行的房间格子
            target_pos = _find_hunt_target_in_room(game_state, hunter.target_room_id, room_human)
            if target_pos is not None:
                # 已在目标位置附近(相邻即可触发kill_check)
                if abs(hunter.grid_col - room_human.grid_col) <= 1 and abs(hunter.grid_row - room_human.grid_row) <= 1:
                    hunter.move_path = []
                    return
                # 已有路径则继续走
                if hunter.move_path:
                    return
                path = find_path(game_state.grid, hunter.pos, target_pos, 'hunter',
                                 door_hp_map, game_state.rooms)
                if path:
                    hunter.move_path = path
                return

    # ── 检查当前目标门是否仍然有效 ──
    need_new_target = True
    current_target_door = None
    if hunter.target_room_id is not None:
        door = game_state.get_door_in_room(hunter.target_room_id)
        if door is not None and door.current_hp > 0:
            need_new_target = False
            current_target_door = door

    # 选择新目标: 优先攻击有活人入住的房间, 选门等级最低的
    if need_new_target:
        # 筛选有活人入住的房间
        occupied_ids = set()
        for h in game_state.humans:
            if h.alive and h.state == HUMAN_BED and h.room_id is not None:
                occupied_ids.add(h.room_id)

        unbroken = [b for b in game_state.buildings
                    if b.type == BLDG_DOOR and b.current_hp > 0
                    and b.room_id in occupied_ids]
        if not unbroken:
            # 无已入住房间(极少情况), 追击走廊游荡人类
            wandering = [h for h in game_state.humans
                        if h.alive and h.state == HUMAN_WANDERING]
            if wandering:
                target_human = min(wandering,
                    key=lambda h: heuristic(hunter.pos, h.pos))
                path = find_path(game_state.grid, hunter.pos,
                               target_human.pos, 'hunter',
                               door_hp_map, game_state.rooms)
                if path:
                    hunter.move_path = path
                hunter.target_room_id = None
            else:
                hunter.move_path = []
                hunter.target_room_id = None
            return

        min_level = min(b.level for b in unbroken)
        candidates = [b for b in unbroken if b.level == min_level]
        current_target_door = random.choice(candidates)
        hunter.target_room_id = current_target_door.room_id
        hunter.move_path = []

    # ── 寻路到门前(走廊侧) ──
    if current_target_door is None:
        return
    room = get_room_by_id(game_state.rooms, current_target_door.room_id)
    if room is None:
        return
    corridor_pos = get_door_adjacent_corridor(room, game_state.grid)

    # 已经在攻击位置
    if hunter.pos == corridor_pos or hunter.pos == current_target_door.pos:
        hunter.move_path = []
        return

    if hunter.move_path:
        return

    path = find_path(game_state.grid, hunter.pos, corridor_pos, 'hunter',
                     door_hp_map, game_state.rooms)
    if path:
        hunter.move_path = path
    else:
        hunter.target_room_id = None
        hunter.move_path = []


def _find_hunt_target_in_room(game_state, room_id, room_human):
    """在已破门房间内找猎梦者可通行的格子(靠近人类)"""
    room = get_room_by_id(game_state.rooms, room_id)
    if room is None:
        return None
    hc, hr = room_human.pos
    # 遍历房间内部, 找离人类最近的可通行格
    best = None
    best_dist = 999
    for c, r in room.interior:
        if is_walkable_for(game_state.grid, c, r, 'hunter', None, game_state.rooms):
            d = abs(c - hc) + abs(r - hr)
            if d < best_dist:
                best_dist = d
                best = (c, r)
    return best


def _hunter_move_to_fountain(game_state):
    """猎梦者寻路回泉水"""
    hunter = game_state.dream_hunter
    if hunter.at_fountain:
        return
    target = game_state.fountain_positions[0]  # 泉水第一格
    door_hp_map = {(b.grid_col, b.grid_row): b.current_hp
                   for b in game_state.buildings if b.type == BLDG_DOOR}
    path = find_path(game_state.grid, hunter.pos, target, 'hunter',
                     door_hp_map, game_state.rooms)
    if path:
        hunter.move_path = path


# ─── 胜负判定 ───

def check_win_lose(game_state):
    """仅在PLAYING阶段判定"""
    if game_state.phase != PHASE_PLAYING:
        return

    if game_state.mode == MODE_HUMAN:
        # 玩家死亡 → 失败
        player = game_state.player_human
        if player and not player.alive:
            game_state.phase = PHASE_DEFEAT
            game_state.victory = False
            return
        # 猎梦者死亡 → 胜利
        if not game_state.dream_hunter.alive:
            game_state.phase = PHASE_VICTORY
            game_state.victory = True
            return

    elif game_state.mode == MODE_HUNTER:
        # 所有人类死亡 → 胜利
        if not game_state.any_human_alive():
            game_state.phase = PHASE_VICTORY
            game_state.victory = True
            return
        # 猎梦者死亡 → 失败
        if not game_state.dream_hunter.alive:
            game_state.phase = PHASE_DEFEAT
            game_state.victory = False
            return


# ─── 实体移动更新 ───

def update_movement(game_state, dt):
    """更新所有可移动实体的位置"""
    # 人类移动
    for human in game_state.humans:
        if not human.alive:
            continue
        if human.state != HUMAN_WANDERING:
            continue
        if not human.move_path:
            continue
        move_along_path(human, human.speed, dt)

    # 猎梦者移动
    hunter = game_state.dream_hunter
    if hunter and hunter.alive and hunter.move_path:
        move_along_path(hunter, hunter.speed_val, dt)

    # 检查AI人类是否到达床(兜底: 处理PLAYING阶段仍在移动的AI)
    for human in game_state.humans:
        if not human.alive or human.is_player:
            continue
        if human.state != HUMAN_WANDERING:
            continue
        bc, br = human.pos
        building = game_state.get_building_at(bc, br)
        if building and building.type == BLDG_BED:
            room_human = game_state.get_human_in_room(building.room_id)
            if room_human is None:
                human.set_bed(building.room_id, bc, br)
                game_state.reserved_room_ids.add(building.room_id)


def move_along_path(entity, speed, dt):
    """沿路径平滑移动实体"""
    if not entity.move_path:
        return
    # 计算目标像素位置
    target_col, target_row = entity.move_path[0]
    target_px = target_col * TILE_SIZE + TILE_SIZE // 2
    target_py = target_row * TILE_SIZE + TILE_SIZE // 2
    entity.target_px = target_px
    entity.target_py = target_py

    # 当前像素位置
    dx = target_px - entity.px
    dy = target_py - entity.py
    dist = math.hypot(dx, dy)

    if dist < 2:
        # 到达该节点
        entity.px = target_px
        entity.py = target_py
        entity.grid_col = target_col
        entity.grid_row = target_row
        entity.move_path.pop(0)
    else:
        move = speed * dt
        if move >= dist:
            entity.px = target_px
            entity.py = target_py
            entity.grid_col = target_col
            entity.grid_row = target_row
            entity.move_path.pop(0)
        else:
            entity.px += dx / dist * move
            entity.py += dy / dist * move


# ─── 玩家输入移动 ───

def move_entity_by_input(entity, dx, dy, grid, door_hp_map=None,
                         entity_type='human_wandering', rooms=None):
    """尝试将实体向(dx,dy)方向移动一格"""
    new_col = entity.grid_col + dx
    new_row = entity.grid_row + dy
    if is_walkable_for(grid, new_col, new_row, entity_type, door_hp_map, rooms):
        entity.grid_col = new_col
        entity.grid_row = new_row
        entity.px = new_col * TILE_SIZE + TILE_SIZE // 2
        entity.py = new_row * TILE_SIZE + TILE_SIZE // 2
        entity.move_path = []
        return True
    return False
