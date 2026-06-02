"""
InputRouter — 输入事件路由: 判断点击类型, 返回语义化事件
拖拽镜头逻辑也在此处理(直接操作Camera)
"""
import pygame
from core.config import *


class InputRouter:
    def __init__(self, camera):
        self.camera = camera
        self.is_dragging = False
        self.drag_start = (0, 0)
        self.drag_start_cxcy = (0.0, 0.0)

    def handle_event(self, event, game_state):
        """返回 (event_type, data) 或 (None, None)"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if event.pos[1] < HUD_HEIGHT:
                    return 'hud_click', event.pos
                self.is_dragging = True
                self.drag_start = event.pos
                self.drag_start_cxcy = (self.camera.cx, self.camera.cy)
                return 'drag_start', event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                was_dragging = self.is_dragging
                self.is_dragging = False
                if was_dragging:
                    dx = event.pos[0] - self.drag_start[0]
                    dy = event.pos[1] - self.drag_start[1]
                    if abs(dx) < 5 and abs(dy) < 5:
                        return 'click', event.pos
                return 'drag_end', event.pos

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                dx = event.pos[0] - self.drag_start[0]
                dy = event.pos[1] - self.drag_start[1]
                if (abs(dx) > 5 or abs(dy) > 5) and self.camera.follow_player:
                    self.camera.follow_player = False
                self.camera.cx = self.drag_start_cxcy[0] - dx / self.camera.scale
                self.camera.cy = self.drag_start_cxcy[1] - dy / self.camera.scale
                self.camera._clamp()
                return 'dragging', event.pos

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if game_state.mode == MODE_HUMAN and game_state.player_human:
                    self.camera.snap_to_entity(game_state.player_human)
                    self.camera.set_target(game_state.player_human)
                elif game_state.mode == MODE_HUNTER:
                    self.camera.snap_to_entity(game_state.dream_hunter)
                    self.camera.set_target(game_state.dream_hunter)
                return 'space', None

        return None, None
