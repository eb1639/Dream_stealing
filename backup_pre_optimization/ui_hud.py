"""
顶部状态栏 + 弹出建造/升级菜单
"""
import pygame
from config import *
from entities import *
from map_data import *


# ─── HUD渲染 ───

def render_hud(screen, game_state, font_small, font_medium):
    """绘制顶部状态栏"""
    sw = screen.get_width()
    # 背景
    hud_rect = pygame.Rect(0, 0, sw, HUD_HEIGHT)
    pygame.draw.rect(screen, (30, 30, 40), hud_rect)
    pygame.draw.line(screen, GRAY, (0, HUD_HEIGHT), (sw, HUD_HEIGHT), 2)

    # 左上角暂停按钮
    pause_btn_size = 28
    pause_btn_margin = 8
    pause_btn_rect = pygame.Rect(pause_btn_margin, (HUD_HEIGHT - pause_btn_size) // 2,
                                  pause_btn_size, pause_btn_size)
    mx, my = pygame.mouse.get_pos()
    hover = pause_btn_rect.collidepoint(mx, my)
    btn_bg = (60, 60, 75) if hover else (45, 45, 55)
    pygame.draw.rect(screen, btn_bg, pause_btn_rect)
    pygame.draw.rect(screen, GRAY, pause_btn_rect, 1)
    # 暂停图标: 两条竖线
    bar_w = 4
    bar_h = 14
    bar_gap = 6
    cx = pause_btn_rect.centerx
    cy = pause_btn_rect.centery
    pygame.draw.rect(screen, WHITE, (cx - bar_gap - bar_w, cy - bar_h // 2, bar_w, bar_h))
    pygame.draw.rect(screen, WHITE, (cx + bar_gap, cy - bar_h // 2, bar_w, bar_h))
    game_state._pause_btn_rect = pause_btn_rect

    # 左侧: 金币(暂停按钮右侧)
    if game_state.mode == MODE_HUMAN and game_state.player_human:
        gold_text = f"金币: {game_state.player_human.gold}"
    elif game_state.mode == MODE_HUNTER and game_state.dream_hunter:
        gold_text = f"伤害: {game_state.dream_hunter.cumulative_damage}  等级{game_state.dream_hunter.level + 1}"
    else:
        gold_text = "金币: 0"
    gold_surf = font_medium.render(gold_text, True, YELLOW)
    gold_x = pause_btn_margin + pause_btn_size + 10
    screen.blit(gold_surf, (gold_x, 8))

    # 中间: 计时器
    if game_state.phase == PHASE_SAFE:
        time_text = f"安全: {int(game_state.safe_timer)}秒"
        time_color = GREEN
    else:
        time_text = f"时间: {int(game_state.game_time)}秒"
        time_color = WHITE
    time_surf = font_medium.render(time_text, True, time_color)
    screen.blit(time_surf, (sw // 2 - time_surf.get_width() // 2, 8))

    # 猎梦者HP
    if game_state.dream_hunter:
        hp_text = f"猎梦者 HP: {game_state.dream_hunter.current_hp}/{game_state.dream_hunter.max_hp}"
        hp_surf = font_small.render(hp_text, True, RED)
        screen.blit(hp_surf, (sw // 2 - hp_surf.get_width() // 2, 32))

    # 右侧: 人类头像(同排, 右对齐)
    avatar_start_x = sw - 20
    ava_y = 4
    ava_w, ava_h = 40, 40
    ava_gap = 6
    game_state.avatar_rects = {}

    for human in game_state.humans:
        ax = avatar_start_x - (human.id + 1) * (ava_w + ava_gap)
        avatar_rect = pygame.Rect(ax, ava_y, ava_w, ava_h)
        if human.is_player:
            color = PLAYER_COLOR
        elif human.alive:
            color = human.color
        else:
            color = DARK_GRAY

        border_color = RED if (human.alive and human.is_under_attack) else GRAY
        if not human.alive:
            border_color = DARK_GRAY
        pygame.draw.rect(screen, border_color, avatar_rect, 2)
        pygame.draw.rect(screen, color, (ax + 3, ava_y + 3, 34, 34))

        if not human.alive:
            pygame.draw.line(screen, RED, (ax, ava_y), (ax + ava_w, ava_y + ava_h), 2)
            pygame.draw.line(screen, RED, (ax + ava_w, ava_y), (ax, ava_y + ava_h), 2)
        elif human.state == HUMAN_BED:
            label = font_small.render("睡", True, WHITE)
            screen.blit(label, (ax + 6, ava_y + 22))
        else:
            label = font_small.render("跑", True, WHITE)
            screen.blit(label, (ax + 6, ava_y + 22))

        game_state.avatar_rects[human.id] = avatar_rect

    # 猎梦者头像(紧挨人类头像左侧)
    total_human_w = 6 * (ava_w + ava_gap)
    hunter_ax = avatar_start_x - total_human_w - ava_w - ava_gap
    if game_state.dream_hunter:
        hunter_avatar_rect = pygame.Rect(hunter_ax, ava_y, ava_w, ava_h)
        pygame.draw.rect(screen, PURPLE, hunter_avatar_rect, 2)
        pygame.draw.rect(screen, DARK_PURPLE, (hunter_ax + 3, ava_y + 3, 34, 34))
        hl = font_small.render("猎", True, WHITE)
        screen.blit(hl, (hunter_ax + 5, ava_y + 22))
        game_state.hunter_avatar_rect = hunter_avatar_rect
    else:
        game_state.hunter_avatar_rect = None


# ─── 弹出菜单 ───

def render_popup_menu(screen, game_state, camera, font):
    """绘制弹出菜单"""
    if not hasattr(game_state, 'popup_menu') or game_state.popup_menu is None:
        return

    menu = game_state.popup_menu
    # menu: {'screen_x': int, 'screen_y': int, 'options': [(label, cost, callback_key)], 'type': str}
    px = menu['screen_x']
    py = menu['screen_y']

    # 绘制选项
    sw, sh = screen.get_width(), screen.get_height()
    option_h = 30
    total_h = len(menu['options']) * option_h + 8
    # 动态计算面板宽度: 取最长文本宽度 + 内边距
    min_w = 180
    max_text_w = min_w
    for label, cost, _ in menu['options']:
        text_str = f"{label}  ${cost}"
        tw, _ = font.size(text_str)
        max_text_w = max(max_text_w, tw + 28)
    panel_w = max(min_w, max_text_w)

    # 确保菜单在屏幕内
    if px + panel_w > sw:
        px = sw - panel_w - 5
    if py + total_h > sh:
        py = sh - total_h - 5
    if px < 5:
        px = 5
    if py < HUD_HEIGHT + 5:
        py = HUD_HEIGHT + 5

    # 背景面板
    panel_rect = pygame.Rect(px, py, panel_w, total_h)
    pygame.draw.rect(screen, (40, 40, 50), panel_rect)
    pygame.draw.rect(screen, GRAY, panel_rect, 2)

    # 选项
    mouse_x, mouse_y = pygame.mouse.get_pos()
    for i, (label, cost, _) in enumerate(menu['options']):
        opt_rect = pygame.Rect(px + 4, py + 4 + i * option_h, panel_w - 8, option_h - 2)
        hover = opt_rect.collidepoint(mouse_x, mouse_y)
        bg = (60, 60, 70) if hover else (50, 50, 60)
        pygame.draw.rect(screen, bg, opt_rect)
        text = font.render(f"{label}  ${cost}", True, WHITE if not hover else YELLOW)
        screen.blit(text, (opt_rect.x + 6, opt_rect.y + 6))

    # 存储菜单位置用于点击检测
    menu['rendered_rects'] = []
    for i, (label, cost, _) in enumerate(menu['options']):
        opt_rect = pygame.Rect(px + 4, py + 4 + i * option_h, panel_w - 8, option_h - 2)
        menu['rendered_rects'].append((opt_rect, i))


def show_build_menu(game_state, col, row, screen_x, screen_y):
    """显示空格子的建造菜单"""
    options = []
    # 检查房间空位是否已有太多炮塔/维修台
    room = get_room_at(game_state.rooms, col, row)
    if room:
        turrets = game_state.get_turrets_in_room(room.id)
        repairs = game_state.get_repairs_in_room(room.id)
        if len(turrets) < 4:
            options.append(("建造炮塔", TURRET_UPGRADE_COST[0], 'build_turret'))
        if len(repairs) < 3:
            options.append(("建造维修台", REPAIR_COST, 'build_repair'))

    if options:
        game_state.popup_menu = {
            'screen_x': screen_x,
            'screen_y': screen_y,
            'options': options,
            'type': 'build',
            'col': col,
            'row': row,
        }
    else:
        game_state.popup_menu = None


def show_upgrade_menu(game_state, building, screen_x, screen_y):
    """显示建筑升级菜单"""
    options = []
    if building.can_upgrade():
        cost = building.upgrade_cost()
        btype_names = {BLDG_DOOR: '门', BLDG_BED: '床', BLDG_TURRET: '炮塔', BLDG_REPAIR: '维修台'}
        name = btype_names.get(building.type, '未知')
        label = f"升级{name}至{building.level + 2}级"
        options.append((label, cost, 'upgrade'))

    if options:
        game_state.popup_menu = {
            'screen_x': screen_x,
            'screen_y': screen_y,
            'options': options,
            'type': 'upgrade',
            'building': building,
        }
    else:
        game_state.popup_menu = None


def handle_popup_click(game_state, mouse_x, mouse_y):
    """处理弹出菜单点击, 返回是否消费了点击"""
    if not hasattr(game_state, 'popup_menu') or game_state.popup_menu is None:
        return False

    menu = game_state.popup_menu
    if 'rendered_rects' not in menu:
        return False

    for rect, idx in menu['rendered_rects']:
        if rect.collidepoint(mouse_x, mouse_y):
            option = menu['options'][idx]
            _, _, callback_key = option

            if callback_key == 'build_turret':
                _do_build(game_state, BLDG_TURRET, menu['col'], menu['row'])
            elif callback_key == 'build_repair':
                _do_build(game_state, BLDG_REPAIR, menu['col'], menu['row'])
            elif callback_key == 'upgrade':
                _do_upgrade(game_state, menu['building'])

            game_state.popup_menu = None
            return True

    # 点击菜单外: 关闭
    game_state.popup_menu = None
    return True


def _do_build(game_state, btype, col, row):
    """执行建造"""
    cost = TURRET_UPGRADE_COST[0] if btype == BLDG_TURRET else REPAIR_COST
    human = game_state.player_human
    if human is None or human.gold < cost:
        return

    human.gold -= cost
    building = Building(btype, col, row, human.room_id)
    game_state.buildings.append(building)
    game_state.building_at[(col, row)] = building


def _do_upgrade(game_state, building):
    """执行升级"""
    cost = building.upgrade_cost()
    if cost is None:
        return

    human = game_state.player_human
    if human is None or human.gold < cost:
        return

    human.gold -= cost
    building.upgrade()


# ─── 暂停弹窗菜单 ───

def handle_pause_btn_click(game_state, mouse_pos):
    """检查是否点击了暂停按钮"""
    if hasattr(game_state, '_pause_btn_rect'):
        if game_state._pause_btn_rect.collidepoint(mouse_pos):
            game_state._pause_menu_open = not getattr(game_state, '_pause_menu_open', False)
            return True
    return False


def render_pause_menu(screen, game_state, font_medium, font_btn):
    """在屏幕中央渲染暂停菜单"""
    if not getattr(game_state, '_pause_menu_open', False):
        return

    sw, sh = screen.get_width(), screen.get_height()

    # 半透明遮罩
    overlay = pygame.Surface((sw, sh))
    overlay.set_alpha(160)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    # 菜单面板
    panel_w, panel_h = 280, 180
    panel_x = sw // 2 - panel_w // 2
    panel_y = sh // 2 - panel_h // 2
    panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    pygame.draw.rect(screen, (35, 35, 50), panel_rect)
    pygame.draw.rect(screen, GRAY, panel_rect, 3)

    mouse_x, mouse_y = pygame.mouse.get_pos()

    # 标题
    title = font_btn.render("游戏菜单", True, WHITE)
    screen.blit(title, (panel_x + panel_w // 2 - title.get_width() // 2, panel_y + 15))

    # 按钮
    btn_w, btn_h = 200, 42
    btn_x = panel_x + (panel_w - btn_w) // 2
    pause_btn_rect = pygame.Rect(btn_x, panel_y + 55, btn_w, btn_h)
    exit_btn_rect = pygame.Rect(btn_x, panel_y + 110, btn_w, btn_h)

    for rect, label, base_color, hover_color in [
        (pause_btn_rect, "暂停游戏", (50, 80, 160), (70, 110, 210)),
        (exit_btn_rect, "退出游戏", (160, 50, 50), (210, 70, 70)),
    ]:
        hover = rect.collidepoint(mouse_x, mouse_y)
        bg = hover_color if hover else base_color
        pygame.draw.rect(screen, bg, rect)
        pygame.draw.rect(screen, WHITE, rect, 2)
        text = font_medium.render(label, True, WHITE)
        screen.blit(text, (rect.centerx - text.get_width() // 2,
                          rect.centery - text.get_height() // 2))

    game_state._pause_menu_rects = {
        'pause': pause_btn_rect,
        'exit': exit_btn_rect,
    }


def handle_pause_menu_click(game_state, mouse_pos):
    """处理暂停菜单按钮点击, 返回是否需要继续处理事件"""
    rects = getattr(game_state, '_pause_menu_rects', None)
    if rects is None:
        return False
    if rects['pause'].collidepoint(mouse_pos):
        game_state.paused = True
        game_state._pause_menu_open = False
        return True
    if rects['exit'].collidepoint(mouse_pos):
        game_state.phase = PHASE_MENU
        game_state.paused = False
        game_state._pause_menu_open = False
        game_state.popup_menu = None
        return True
    # 点击菜单外: 关闭菜单
    game_state._pause_menu_open = False
    return True
