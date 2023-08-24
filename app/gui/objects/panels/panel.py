import imgui

from app.gui.objects import GUIObject


class Panel(GUIObject):
    def __init__(self, name):
        super().__init__()

        self._name = name

    def _draw_content(self):
        pass

    def draw(self):
        expanded, _ = imgui.collapsing_header(self._name, None)

        if expanded:
            self._draw_content()

            imgui.separator()
