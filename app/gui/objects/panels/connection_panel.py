import imgui

from app.core.autopilot.fg_brain import BrainBase

from .panel import Panel


class ConnectionPanel(Panel):
    def __init__(self, on_connect_callback: callable, on_stop_callback: callable, on_brain_changed: callable):
        super().__init__(name="Connection")

        self._host = "localhost"
        self._fdm_out_port = 5501
        self._fdm_in_port = 5502
        self._ctrls_out_port = 5503
        self._ctrls_in_port = 5504

        self._available_brains_types = [e.value for e in BrainBase.BrainType]
        self._selected_brain_idx = 0

        self._on_connect_callback = on_connect_callback
        self._on_stop_callback = on_stop_callback
        self._on_brain_changed_callback = on_brain_changed

    def _draw_host_input(self):
        imgui.text("Host")
        imgui.push_item_width(-1)
        _, self._host = imgui.input_text('##host', self._host)

    @staticmethod
    def _draw_port_input(port_name, port_out, port_in):
        imgui.push_id(port_name)

        item_spacing_x = imgui.get_style().item_spacing.x
        item_width = imgui.get_content_region_available_width() / 2 - item_spacing_x / 2

        imgui.text(f"{port_name} (Out\\In)")

        imgui.push_item_width(item_width)

        _, port_out = imgui.input_int('##out', port_out, 0)
        imgui.same_line()
        _, port_in = imgui.input_int('##in', port_in, 0)

        imgui.pop_item_width()

        imgui.pop_id()

        return port_out, port_in

    def _draw_brain_selector(self):
        imgui.text("Brain")

        changed, self._selected_brain_idx = imgui.combo("##brain",
                                                        self._selected_brain_idx, self._available_brains_types)
        if changed and self._on_brain_changed_callback:
            brain_type = BrainBase.BrainType(self._available_brains_types[self._selected_brain_idx])
            self._on_brain_changed_callback(brain_type)

        imgui.pop_item_width()

    def _draw_buttons(self):
        button_width = imgui.get_content_region_available_width() / 2 - imgui.get_style().item_spacing.x / 2

        if imgui.button("Connect", button_width):
            self._on_connect_callback(self._host,
                                      self._fdm_out_port, self._fdm_in_port,
                                      self._ctrls_out_port, self._ctrls_in_port)

        imgui.same_line()

        if imgui.button("Stop", button_width):
            self._on_stop_callback()

    def _draw_content(self):
        # Host
        self._draw_host_input()

        imgui.dummy(0, 2)

        # FDM & CTRLS ports
        self._draw_port_input("FDM Port", self._fdm_out_port, self._fdm_in_port)
        imgui.dummy(0, 2)
        self._draw_port_input("CTRLS Port", self._ctrls_out_port, self._ctrls_in_port)

        imgui.dummy(0, 2)

        # Brain
        self._draw_brain_selector()

        imgui.dummy(0, 4)

        # Buttons
        self._draw_buttons()
