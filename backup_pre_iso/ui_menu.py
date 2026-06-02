"""
像素风主菜单: 双模式选择
"""
import pygame
import math
from core.config import *


class MenuButton:
    def __init__(self, rect, text, color, hover_color):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.hovered = False

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, screen, font):
        bg = self.hover_color if self.hovered else self.color
        # 像素边框效果
        shadow_rect = self.rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(screen, (20, 20, 30), shadow_rect)
        pygame.draw.rect(screen, bg, self.rect)
        # 像素描边(双层)
        pygame.draw.rect(screen, WHITE, self.rect, 3)
        pygame.draw.rect(screen, BLACK, self.rect, 1)

        text_surf = font.render(self.text, True, WHITE)
        tx = self.rect.centerx - text_surf.get_width() // 2
        ty = self.rect.centery - text_surf.get_height() // 2
        screen.blit(text_surf, (tx, ty))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


def render_menu(screen, font_title, font_btn, buttons):
    """渲染主菜单"""
    sw, sh = screen.get_width(), screen.get_height()
    screen.fill((15, 15, 25))

    # 背景装饰 - 网格线
    for x in range(0, sw, 32):
        pygame.draw.line(screen, (25, 25, 40), (x, 0), (x, sh))
    for y in range(0, sh, 32):
        pygame.draw.line(screen, (25, 25, 40), (0, y), (sw, y))

    # 标题
    title_text = "DREAM LOBBY"
    title_surf = font_title.render(title_text, True, (180, 140, 255))
    tx = sw // 2 - title_surf.get_width() // 2
    ty = 120
    # 像素阴影
    shadow = font_title.render(title_text, True, (60, 30, 100))
    screen.blit(shadow, (tx + 4, ty + 4))
    screen.blit(title_surf, (tx, ty))

    # 副标题
    sub_text = "盗 梦 空 间"
    sub_surf = font_title.render(sub_text, True, (200, 180, 240))
    sx = sw // 2 - sub_surf.get_width() // 2
    screen.blit(sub_surf, (sx, ty + 60))

    # 按钮
    for btn in buttons:
        btn.draw(screen, font_btn)

    # 底部提示
    try:
        hint_font = pygame.font.SysFont('simhei', 18)
    except Exception:
        hint_font = pygame.font.Font(None, 18)
    hint = hint_font.render("选择你的角色...", True, LIGHT_GRAY)
    screen.blit(hint, (sw // 2 - hint.get_width() // 2, sh - 50))


def create_menu_buttons():
    """创建两个模式选择按钮"""
    btn_w = 300
    btn_h = 70
    cx = SCREEN_WIDTH // 2
    y1 = 320
    y2 = 420

    btn_human = MenuButton(
        (cx - btn_w // 2, y1, btn_w, btn_h),
        "人类模式",
        (40, 80, 180),
        (60, 120, 240),
    )
    btn_hunter = MenuButton(
        (cx - btn_w // 2, y2, btn_w, btn_h),
        "猎梦者模式",
        (160, 40, 40),
        (220, 60, 60),
    )
    return [btn_human, btn_hunter]
