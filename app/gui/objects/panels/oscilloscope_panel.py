import imgui

from .panel import Panel


class OscilloscopePanel(Panel):
    def __init__(self):
        super().__init__(name="Oscilloscope")

        self._is_show_oscilloscope = False

        self._on_show_oscilloscope_change = None

    def set_on_show_oscilloscope_change(self, cb: callable):
        self._on_show_oscilloscope_change = cb

    def _draw_content(self):
        changed, self._is_show_oscilloscope = imgui.checkbox("Show oscilloscope", self._is_show_oscilloscope)
        if changed and self._on_show_oscilloscope_change:
            self._on_show_oscilloscope_change(self._is_show_oscilloscope)

        if not self._is_show_oscilloscope:
            return

        # TODO: Oscilloscope properties
