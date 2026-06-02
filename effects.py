"""
金币飘字、伤害数字特效
"""
from config import *


def update_effects(game_state, dt):
    """更新所有特效计时器"""
    if hasattr(game_state, 'damage_numbers'):
        for dn in game_state.damage_numbers[:]:
            dn['timer'] -= dt
            if dn['timer'] <= 0:
                game_state.damage_numbers.remove(dn)

    if hasattr(game_state, 'gold_numbers'):
        for gn in game_state.gold_numbers[:]:
            gn['timer'] -= dt
            if gn['timer'] <= 0:
                game_state.gold_numbers.remove(gn)

    if hasattr(game_state, 'heal_numbers'):
        for hn in game_state.heal_numbers[:]:
            hn['timer'] -= dt
            if hn['timer'] <= 0:
                game_state.heal_numbers.remove(hn)


def render_effects(screen, game_state, camera, font, left, top, scale, gax, gay):
    """渲染所有特效(屏幕坐标=viewport坐标×scale+偏移)"""
    if hasattr(game_state, 'damage_numbers'):
        for dn in game_state.damage_numbers:
            vx = dn['col'] * TILE_SIZE + TILE_SIZE // 2 - left
            vy = dn['row'] * TILE_SIZE - top - 28 - (1.0 - dn['timer']) * 25
            sx = vx * scale + gax
            sy = vy * scale + gay
            alpha = int(255 * dn['timer'])
            text = font.render(str(dn['value']), True, dn['color'])
            text.set_alpha(alpha)
            screen.blit(text, (sx - text.get_width() // 2 - 10, sy))

    if hasattr(game_state, 'gold_numbers'):
        for gn in game_state.gold_numbers:
            vx = gn['col'] * TILE_SIZE + TILE_SIZE // 2 - left
            vy = gn['row'] * TILE_SIZE - top - 18 - (1.0 - gn['timer']) * 20
            sx = vx * scale + gax
            sy = vy * scale + gay
            alpha = int(255 * gn['timer'])
            text = font.render(gn['value'], True, gn['color'])
            text.set_alpha(alpha)
            screen.blit(text, (sx - text.get_width() // 2, sy))

    if hasattr(game_state, 'heal_numbers'):
        for hn in game_state.heal_numbers:
            vx = hn['col'] * TILE_SIZE + TILE_SIZE // 2 - left
            vy = hn['row'] * TILE_SIZE - top - 28 - (1.0 - hn['timer']) * 20
            sx = vx * scale + gax
            sy = vy * scale + gay
            alpha = int(255 * hn['timer'])
            text = font.render(str(hn['value']), True, hn['color'])
            text.set_alpha(alpha)
            screen.blit(text, (sx - text.get_width() // 2 + 10, sy))
