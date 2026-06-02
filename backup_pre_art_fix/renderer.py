"""
程序化像素纹理生成 + 地图/实体/建筑绘制
"""
import pygame
import math
from config import *
from entities import *


def draw_pixel_texture(surface, x, y, w, h, draw_func):
    """在(x,y)处创建w×h的子surface并调用draw_func绘制"""
    sub = pygame.Surface((w, h), pygame.SRCALPHA)
    draw_func(sub, w, h)
    surface.blit(sub, (x, y))


# ═══════════════════════════════════════
#  纹理生成函数
# ═══════════════════════════════════════

def draw_floor_tile(surf, w, h):
    """蓝绿色复古地砖纹理(房间地板)"""
    surf.fill(TEAL)
    # 网格线
    for i in range(0, w, 8):
        pygame.draw.line(surf, DARK_TEAL, (i, 0), (i, h), 1)
    for i in range(0, h, 8):
        pygame.draw.line(surf, DARK_TEAL, (0, i), (w, i), 1)
    # 明暗阴影
    for i in range(0, w, 4):
        for j in range(0, h, 4):
            shade = 0 if (i // 4 + j // 4) % 2 == 0 else 1
            if shade:
                pygame.draw.rect(surf, (35, 118, 95, 80), (i, j, 4, 4))


def draw_wall_tile(surf, w, h):
    """深棕色像素砖块纹理"""
    surf.fill(BROWN)
    brick_h = h // 3
    for row_idx in range(3):
        offset = (row_idx % 2) * (w // 4)
        yr = row_idx * brick_h
        for col_idx in range(4):
            xr = col_idx * (w // 2) + offset
            if xr >= w:
                xr -= w
            # 砖块主体
            brick_rect = (xr + 1, yr + 1, w // 2 - 2, brick_h - 2)
            pygame.draw.rect(surf, DARK_BROWN, brick_rect)
            pygame.draw.rect(surf, BROWN, brick_rect, 1)


def draw_corridor_tile(surf, w, h):
    """米白色复古走廊地砖"""
    surf.fill(BEIGE)
    # 网格线
    for i in range(0, w, 8):
        pygame.draw.line(surf, DARK_BEIGE, (i, 0), (i, h), 1)
    for i in range(0, h, 8):
        pygame.draw.line(surf, DARK_BEIGE, (0, i), (w, i), 1)


def draw_door(surf, w, h, level):
    """像素铁门, 带横栅栏, 随等级变精致"""
    # 背景
    surf.fill(IRON)
    # 边框
    border_color = (50, 50, 55) if level < 3 else (40, 40, 45)
    pygame.draw.rect(surf, border_color, (0, 0, w, h), 2)
    # 横栅栏
    bar_count = 3 + level
    bar_thickness = 3 if level < 2 else 4
    for i in range(bar_count):
        y_bar = h * (i + 1) // (bar_count + 1)
        pygame.draw.rect(surf, (50, 50, 55), (2, y_bar - bar_thickness // 2, w - 4, bar_thickness))
    # 等级≥3: 加厚边框+装饰
    if level >= 3:
        pygame.draw.rect(surf, (60, 60, 65), (0, 0, w, h), 4)
        # 铆钉
        for cx, cy in [(6, 6), (w - 6, 6), (6, h - 6), (w - 6, h - 6)]:
            pygame.draw.circle(surf, (100, 100, 105), (cx, cy), 3)
    if level >= 4:
        # 雕花边框
        for cx, cy in [(w // 2, 4), (w // 2, h - 4), (4, h // 2), (w - 4, h // 2)]:
            pygame.draw.circle(surf, (120, 120, 125), (cx, cy), 2)


def draw_bed(surf, w, h, level):
    """像素床: 枕头+被子褶皱, 随等级变大"""
    surf.fill(TEAL)  # 底色=地板

    # 床的大小随等级变化
    scale = 0.6 + level * 0.12
    bw = int(w * scale)
    bh = int(h * scale)
    bx = (w - bw) // 2
    by = (h - bh) // 2

    # 床架
    frame_color = (139, 90, 43) if level < 2 else (160, 120, 60)
    pygame.draw.rect(surf, frame_color, (bx, by, bw, bh))
    pygame.draw.rect(surf, (100, 65, 30), (bx, by, bw, bh), 2)

    # 白色枕头
    pillow_w = bw // 3
    pillow_h = bh // 4
    pygame.draw.rect(surf, WHITE, (bx + 3, by + 3, pillow_w, pillow_h))
    pygame.draw.rect(surf, LIGHT_GRAY, (bx + 3, by + 3, pillow_w, pillow_h), 1)

    # 被子(带褶皱)
    blanket_color = (180, 180, 210) if level < 3 else (140, 100, 180)
    blanket_x = bx + 3
    blanket_y = by + pillow_h + 4
    blanket_w = bw - 6
    blanket_h = bh - pillow_h - 8
    pygame.draw.rect(surf, blanket_color, (blanket_x, blanket_y, blanket_w, blanket_h))
    # 褶皱线
    for i in range(3):
        fx = blanket_x + blanket_w * (i + 1) // 4
        pygame.draw.line(surf, (150, 150, 180), (fx, blanket_y + 2), (fx, blanket_y + blanket_h - 2), 1)

    # 等级4+: 金边床
    if level >= 3:
        pygame.draw.rect(surf, YELLOW, (bx - 1, by - 1, bw + 2, bh + 2), 1)


def draw_turret(surf, w, h, level):
    """炮塔: 底座+炮管, 随升级变粗"""
    surf.fill(TEAL)  # 底色
    cx, cy = w // 2, h // 2

    # 底座
    base_r = w // 3 + level
    base_color = (100, 100, 110) if level < 2 else (120, 120, 130)
    pygame.draw.circle(surf, base_color, (cx, cy + 2), base_r)
    pygame.draw.circle(surf, DARK_GRAY, (cx, cy + 2), base_r, 2)

    # 炮管(默认朝右上)
    barrel_color = (60, 60, 70) if level < 3 else (180, 150, 40)
    barrel_w = 4 + level
    barrel_len = w // 2 + level
    angle = -math.pi / 4
    ex = cx + int(barrel_len * math.cos(angle))
    ey = cy - int(barrel_len * math.sin(angle))
    pygame.draw.line(surf, barrel_color, (cx, cy), (ex, ey), barrel_w)

    # 等级3+: 双管
    if level >= 2:
        angle2 = -math.pi / 6
        ex2 = cx + int(barrel_len * math.cos(angle2) * 0.8)
        ey2 = cy - int(barrel_len * math.sin(angle2) * 0.8)
        pygame.draw.line(surf, barrel_color, (cx, cy), (ex2, ey2), barrel_w - 1)


def draw_repair_station(surf, w, h):
    """维修台"""
    surf.fill(TEAL)
    cx, cy = w // 2, h // 2
    # 工作台
    pygame.draw.rect(surf, (100, 140, 180), (cx - 8, cy - 4, 16, 12))
    pygame.draw.rect(surf, (60, 100, 140), (cx - 8, cy - 4, 16, 12), 2)
    # 扳手/工具图标
    pygame.draw.circle(surf, (180, 180, 200), (cx, cy - 6), 3)
    # 绿色十字
    pygame.draw.line(surf, GREEN, (cx, cy - 10), (cx, cy - 2), 2)
    pygame.draw.line(surf, GREEN, (cx - 4, cy - 6), (cx + 4, cy - 6), 2)


def draw_human_sprite(surf, w, h, color, is_bed=False):
    """像素小人"""
    surf.fill((0, 0, 0, 0))  # 透明
    cx, cy = w // 2, h // 2
    r = w // 3
    if is_bed:
        # 躺平: 小横条
        pygame.draw.ellipse(surf, color, (cx - r, cy - r // 2, r * 2, r))
    else:
        # 站立: 圆头+身体
        pygame.draw.circle(surf, color, (cx, cy - r // 2), r)
        pygame.draw.rect(surf, color, (cx - r // 2, cy, r, r))


def draw_hunter_sprite(surf, w, h, level):
    """像素猎梦者: 暗紫色人形+红眼"""
    surf.fill((0, 0, 0, 0))
    cx, cy = w // 2, h // 2
    body_r = w // 3 + level // 2
    # 身体
    body_color = (80 + level * 15, 10, 120 + level * 10)
    pygame.draw.ellipse(surf, body_color, (cx - body_r, cy - body_r, body_r * 2, body_r * 2))
    # 红色眼睛
    eye_r = max(2, body_r // 3)
    pygame.draw.circle(surf, RED, (cx - body_r // 2, cy - body_r // 3), eye_r)
    pygame.draw.circle(surf, RED, (cx + body_r // 2, cy - body_r // 3), eye_r)
    # 轮廓
    pygame.draw.ellipse(surf, DARK_PURPLE, (cx - body_r, cy - body_r, body_r * 2, body_r * 2), 2)


def draw_fountain_tile(surf, w, h):
    """泉水格"""
    surf.fill((30, 30, 60))
    # 涟漪
    for i in range(3):
        r_ = 4 + i * 4
        alpha = 100 - i * 25
        ripple_color = (60, 60, 180, alpha)
        pygame.draw.circle(surf, ripple_color[:3], (w // 2, h // 2), r_, 1)
    pygame.draw.circle(surf, (100, 100, 255), (w // 2, h // 2), 3)


# ═══════════════════════════════════════
#  主渲染函数 — viewport → scale 流程
#  屏幕显示 = 视野范围
# ═══════════════════════════════════════

from ui_camera import VIEWPORT_SIZE, VIEW_TILES


def render_game(screen, game_state, camera, font_small, font_medium):
    """渲染整个游戏画面: 先画到viewport, 再scale到屏幕"""
    screen.fill(BLACK)

    # ── 计算scale: viewport填满屏幕游戏区域 ──
    sw, sh = screen.get_width(), screen.get_height()
    game_area_w = sw
    game_area_h = sh - HUD_HEIGHT
    scale = min(game_area_w / VIEWPORT_SIZE, game_area_h / VIEWPORT_SIZE)
    camera.scale = scale
    scaled_w = int(VIEWPORT_SIZE * scale)
    scaled_h = int(VIEWPORT_SIZE * scale)
    game_area_x = (game_area_w - scaled_w) // 2
    game_area_y = HUD_HEIGHT + (game_area_h - scaled_h) // 2

    # ── 创建viewport ──
    viewport = pygame.Surface((VIEWPORT_SIZE, VIEWPORT_SIZE))

    # ── 获取viewport在地图上的覆盖范围 ──
    left, top, _, _ = camera.viewport_map_rect

    # 地图层
    _render_map(viewport, game_state, left, top)

    # 建筑层
    _render_buildings(viewport, game_state, left, top)

    # 实体层
    _render_entities(viewport, game_state, left, top)

    # 子弹
    _render_bullets(viewport, game_state, left, top)

    # ── 缩放viewport到屏幕 ──
    scaled = pygame.transform.scale(viewport, (scaled_w, scaled_h))
    screen.blit(scaled, (game_area_x, game_area_y))

    # ── HUD (不缩放, 始终在顶部) ──
    from ui_hud import render_hud
    render_hud(screen, game_state, font_small, font_medium)

    # ── 弹出菜单 ──
    from ui_hud import render_popup_menu
    render_popup_menu(screen, game_state, camera, font_small)

    # ── 特效 ──
    from effects import render_effects
    render_effects(screen, game_state, camera, font_small, left, top, scale, game_area_x, game_area_y)

    # 存储当前scale/offset用于screen_to_grid
    game_state._scale = scale
    game_state._game_area_x = game_area_x
    game_state._game_area_y = game_area_y


def _render_map(viewport, game_state, left, top):
    """绘制地图到viewport"""
    grid = game_state.grid
    c0 = max(0, int(left // TILE_SIZE))
    r0 = max(0, int(top // TILE_SIZE))
    c1 = min(MAP_COLS - 1, int((left + VIEWPORT_SIZE) // TILE_SIZE) + 1)
    r1 = min(MAP_ROWS - 1, int((top + VIEWPORT_SIZE) // TILE_SIZE) + 1)

    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            sx = c * TILE_SIZE - left
            sy = r * TILE_SIZE - top
            if sx + TILE_SIZE < 0 or sx > VIEWPORT_SIZE or sy + TILE_SIZE < 0 or sy > VIEWPORT_SIZE:
                continue
            tile = grid[r][c]
            if tile == TILE_WALL:
                draw_pixel_texture(viewport, int(sx), int(sy), TILE_SIZE, TILE_SIZE, draw_wall_tile)
            elif tile == TILE_ROOM:
                draw_pixel_texture(viewport, int(sx), int(sy), TILE_SIZE, TILE_SIZE, draw_floor_tile)
            elif tile == TILE_FOUNTAIN:
                draw_pixel_texture(viewport, int(sx), int(sy), TILE_SIZE, TILE_SIZE, draw_fountain_tile)
            elif tile in (TILE_EMPTY, TILE_DOOR, TILE_BED):
                draw_pixel_texture(viewport, int(sx), int(sy), TILE_SIZE, TILE_SIZE, draw_corridor_tile)


def _render_buildings(viewport, game_state, left, top):
    """绘制建筑到viewport"""
    for b in game_state.buildings:
        sx = b.grid_col * TILE_SIZE - left
        sy = b.grid_row * TILE_SIZE - top
        if sx + TILE_SIZE < 0 or sx > VIEWPORT_SIZE or sy + TILE_SIZE < 0 or sy > VIEWPORT_SIZE:
            continue

        if b.type == BLDG_DOOR:
            if b.current_hp > 0:
                draw_pixel_texture(viewport, int(sx), int(sy), TILE_SIZE, TILE_SIZE,
                                   lambda s, w, h: draw_door(s, w, h, b.level))
                hp_ratio = b.current_hp / b.max_hp if b.max_hp > 0 else 0
                bar_w = TILE_SIZE - 4
                bar_h = 4
                bar_x = int(sx) + 2
                bar_y = max(2, int(sy) - 7)
                pygame.draw.rect(viewport, BLACK, (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
                pygame.draw.rect(viewport, RED, (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(viewport, GREEN, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
                if b.being_repaired:
                    cx = int(sx) + TILE_SIZE // 2
                    cy = int(sy) + TILE_SIZE // 2
                    pygame.draw.circle(viewport, (180, 180, 200), (cx, cy - 6), 3)
                    pygame.draw.line(viewport, GREEN, (cx, cy - 10), (cx, cy - 2), 2)
                    pygame.draw.line(viewport, GREEN, (cx - 4, cy - 6), (cx + 4, cy - 6), 2)
            else:
                draw_pixel_texture(viewport, int(sx), int(sy), TILE_SIZE, TILE_SIZE, draw_corridor_tile)
                pygame.draw.rect(viewport, DARK_GRAY, (int(sx), int(sy), TILE_SIZE, TILE_SIZE), 1)

        elif b.type == BLDG_BED:
            draw_pixel_texture(viewport, int(sx), int(sy), TILE_SIZE, TILE_SIZE,
                               lambda s, w, h: draw_bed(s, w, h, b.level))
        elif b.type == BLDG_TURRET:
            draw_pixel_texture(viewport, int(sx), int(sy), TILE_SIZE, TILE_SIZE,
                               lambda s, w, h: draw_turret(s, w, h, b.level))
        elif b.type == BLDG_REPAIR:
            draw_pixel_texture(viewport, int(sx), int(sy), TILE_SIZE, TILE_SIZE,
                               lambda s, w, h: draw_repair_station(s, w, h))


def _render_entities(viewport, game_state, left, top):
    """绘制人类和猎梦者到viewport"""
    for human in game_state.humans:
        if not human.alive:
            continue
        sx = human.px - TILE_SIZE // 2 - left
        sy = human.py - TILE_SIZE // 2 - top
        if sx + TILE_SIZE < 0 or sx > VIEWPORT_SIZE or sy + TILE_SIZE < 0 or sy > VIEWPORT_SIZE:
            continue
        is_bed = (human.state == HUMAN_BED)
        draw_pixel_texture(viewport, int(sx), int(sy), TILE_SIZE, TILE_SIZE,
                           lambda s, w, h: draw_human_sprite(s, w, h, human.color, is_bed))
        if human.is_player:
            pygame.draw.rect(viewport, YELLOW, (int(sx), int(sy), TILE_SIZE, TILE_SIZE), 2)

    hunter = game_state.dream_hunter
    if hunter and hunter.alive:
        sx = hunter.px - TILE_SIZE // 2 - left
        sy = hunter.py - TILE_SIZE // 2 - top
        if not (sx + TILE_SIZE < 0 or sx > VIEWPORT_SIZE or sy + TILE_SIZE < 0 or sy > VIEWPORT_SIZE):
            draw_pixel_texture(viewport, int(sx), int(sy), TILE_SIZE, TILE_SIZE,
                               lambda s, w, h: draw_hunter_sprite(s, w, h, hunter.level))
            hp_ratio = hunter.current_hp / hunter.max_hp if hunter.max_hp > 0 else 0
            bar_w = TILE_SIZE
            bar_h = 5
            bar_x = int(sx)
            bar_y = int(sy) - 9
            pygame.draw.rect(viewport, BLACK, (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
            pygame.draw.rect(viewport, RED, (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(viewport, PURPLE, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))


def _render_bullets(viewport, game_state, left, top):
    """绘制子弹到viewport"""
    for bullet in game_state.bullets:
        sx = int(bullet.px - left)
        sy = int(bullet.py - top)
        if 0 <= sx <= VIEWPORT_SIZE and 0 <= sy <= VIEWPORT_SIZE:
            pygame.draw.circle(viewport, ORANGE, (sx, sy), 4)
            pygame.draw.circle(viewport, YELLOW, (sx, sy), 2)
