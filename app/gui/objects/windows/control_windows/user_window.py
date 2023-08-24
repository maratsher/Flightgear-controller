import imgui

from app.core.autopilot.fg_brain import BrainBase, StorageBrain, PilotBrain, AutopilotBrain

from app.gui.objects.windows import Window
from app.gui.objects.windows.view_windows import OscilloscopeWindow

from app.gui.objects.panels import ConnectionPanel
from app.gui.objects.panels import AutopilotSettingsPanel
from app.gui.objects.panels import PIDSettingsPanel
from app.gui.objects.panels import OscilloscopePanel


class UserWindow(Window):
    def __init__(self, on_connect_callback: callable, on_stop_callback: callable, on_brain_changed: callable):
        super().__init__()
        self._id = "General Settings"

        self._brain: BrainBase = BrainBase()

        self._is_show_oscilloscope_window = False

        self._oscilloscope_window = OscilloscopeWindow()

        self._connection_panel = ConnectionPanel(on_connect_callback, on_stop_callback, on_brain_changed)
        self._autopilot_settings_panel = AutopilotSettingsPanel(self._on_autopilot_settings_changed)
        self._pid_settings_panel = PIDSettingsPanel(self._on_pid_controller_change)

        self._oscilloscope_panel = OscilloscopePanel()

        self._oscilloscope_panel.set_on_show_oscilloscope_change(self._set_show_oscilloscope_window)

    def set_brain(self, brain: BrainBase):
        self._brain = brain

        if isinstance(self._brain, AutopilotBrain):
            self._autopilot_settings_panel.install_target_properties()

        if isinstance(self._brain, PilotBrain):
            self._pid_settings_panel.set_pitch_pid_c(self._brain.pitch_pid_c)
            self._pid_settings_panel.set_yaw_pid_c(self._brain.yaw_pid_c)
            self._pid_settings_panel.set_roll_pid_c(self._brain.roll_pid_c)

    def _set_show_oscilloscope_window(self, is_show):
        self._is_show_oscilloscope_window = is_show

    def _on_autopilot_settings_changed(self, pitch, yaw, roll, throttle):
        if not isinstance(self._brain, AutopilotBrain):
            return

        self._brain.set_target_pitch(pitch)
        self._brain.set_target_yaw(yaw)
        self._brain.set_target_roll(roll)
        self._brain.set_target_throttle(throttle)

        self._oscilloscope_window.put_target_data(pitch, OscilloscopeWindow.PlotType.PITCH)
        self._oscilloscope_window.put_target_data(yaw, OscilloscopeWindow.PlotType.YAW)
        self._oscilloscope_window.put_target_data(roll, OscilloscopeWindow.PlotType.ROLL)

    def _on_pid_controller_change(self, pitch_pid_c, yaw_pid_c, roll_pid_c):
        if isinstance(self._brain, PilotBrain):
            self._brain.pitch_pid_c = pitch_pid_c
            self._brain.yaw_pid_c = yaw_pid_c
            self._brain.roll_pid_c = roll_pid_c

    def _begin_window(self):
        imgui.set_next_window_position(self.position.x, self.position.y, imgui.ALWAYS)
        imgui.set_next_window_size(self.size.x, self.size.y)

        imgui.push_style_var(imgui.STYLE_WINDOW_BORDERSIZE, 0)

        imgui.begin(self._id, False, imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE |
                    imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS)

    def _end_window(self):
        imgui.end()
        imgui.pop_style_var()

    def _draw_panels(self):
        self._connection_panel.draw()

        imgui.dummy(0, 4)

        if isinstance(self._brain, PilotBrain):
            self._pid_settings_panel.draw()

            imgui.dummy(0, 4)

        if isinstance(self._brain, AutopilotBrain):
            self._autopilot_settings_panel.draw()

            imgui.dummy(0, 4)

        self._oscilloscope_panel.draw()

        imgui.dummy(0, 4)

    def _draw_windows(self):
        if self._is_show_oscilloscope_window:
            if isinstance(self._brain, StorageBrain):
                self._oscilloscope_window.put_plot_data(self._brain.pitch, OscilloscopeWindow.PlotType.PITCH)
                self._oscilloscope_window.put_plot_data(self._brain.yaw, OscilloscopeWindow.PlotType.YAW)
                self._oscilloscope_window.put_plot_data(self._brain.roll, OscilloscopeWindow.PlotType.ROLL)

            self._oscilloscope_window.draw()

    def _draw_content(self):
        self._draw_panels()
        self._draw_windows()
