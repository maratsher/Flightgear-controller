from __future__ import annotations

import imgui

from .zoom_image_window import ZoomImageWindow


class TrackerImageWindow(ZoomImageWindow):
    DEFAULT_BBOX_COLOR = (0.0, 0.0, 1.0)
    TRACKING_BBOX_COLOR = (1.0, 0.0, 0.0)

    def __init__(self, on_roi_selected: callable, x=0, y=0):
        super().__init__(x=x, y=y)

        self._selected_bbox = None
        self._is_roi_select = False

        self._bbox_color = self.DEFAULT_BBOX_COLOR

        self._on_roi_selected = on_roi_selected

    @property
    def selected_roi(self):
        if self._selected_bbox is None:
            return None

        x = self._selected_bbox[0]
        y = self._selected_bbox[1]
        w = self._selected_bbox[2] - x
        h = self._selected_bbox[3] - y
        return x, y, w, h

    @selected_roi.setter
    def selected_roi(self, roi):
        self._selected_bbox = [roi[0], roi[1], roi[0] + roi[2], roi[1] + roi[3]]

    def set_bbox_color(self, bbox_color: tuple[float, float, float]):
        self._bbox_color = bbox_color

    def reset_roi(self):
        self._selected_bbox = None
        self._is_roi_select = False
        self._bbox_color = self.DEFAULT_BBOX_COLOR

    def _handle_input(self):
        super()._handle_input()

        if not self._is_image_hovering:
            return

        def cursor_image_pos():
            cursor_screen = imgui.get_mouse_pos()
            return self.screen2image(self, cursor_screen.x, cursor_screen.y)

        if self._is_roi_select and self._selected_bbox is not None:
            cursor_pos = cursor_image_pos()
            self._selected_bbox[2] = cursor_pos.x
            self._selected_bbox[3] = cursor_pos.y

        if imgui.is_mouse_double_clicked(0):
            cursor_pos = cursor_image_pos()

            if not self._is_roi_select:
                self._is_roi_select = True
                self._selected_bbox = [cursor_pos.x, cursor_pos.y, cursor_pos.x, cursor_pos.y]
            else:
                self._is_roi_select = False

                if self._on_roi_selected:
                    self._on_roi_selected(self.selected_roi)

    def _draw_overlay(self):
        if self._selected_bbox is None:
            return

        draw_list = imgui.get_window_draw_list()

        p1 = self.image2screen(self, self._selected_bbox[0], self._selected_bbox[1])
        p2 = self.image2screen(self, self._selected_bbox[2], self._selected_bbox[3])

        foreground_color = imgui.color_convert_float4_to_u32(*self._bbox_color, 0.8)
        background_color = imgui.color_convert_float4_to_u32(*self._bbox_color, 0.2)

        draw_list.add_rect(p1.x, p1.y, p2.x, p2.y, foreground_color, thickness=1)
        draw_list.add_rect_filled(p1.x, p1.y, p2.x, p2.y, background_color)

        image_center = self.image2screen(self, self._texture_width / 2, self._texture_height / 2)
        draw_list.add_line((p1.x + p2.x) / 2, (p1.y + p2.y) / 2,
                           image_center.x, image_center.y,
                           foreground_color, thickness=1)
