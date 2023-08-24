import imgui

from app.core.autopilot.fg_pid import PIDControllerCoefficient
from .panel import Panel


class PIDSettingsPanel(Panel):
    def __init__(self, on_changed_callback: callable):
        super().__init__(name="PID Controller")

        self._pitch_pid_c = PIDControllerCoefficient(0.1, 0.005, 0.001)
        self._yaw_pid_c = PIDControllerCoefficient(0.1, 0, 0)
        self._roll_pid_c = PIDControllerCoefficient(0.05, 0.005, 0.001)

        self._on_changed_callback = on_changed_callback

    # TODO: Set by type
    def set_pitch_pid_c(self, pid_c: PIDControllerCoefficient):
        self._pitch_pid_c = pid_c

    def set_yaw_pid_c(self, pid_c: PIDControllerCoefficient):
        self._yaw_pid_c = pid_c

    def set_roll_pid_c(self, pid_c: PIDControllerCoefficient):
        self._roll_pid_c = pid_c

    @staticmethod
    def _draw_pid_coefficients(pid_name, pid_c):
        imgui.text(f"{pid_name} PID (Kp, Ki, Kd)")

        imgui.set_next_item_width(-1)
        pitch_changed, pid_c_raw = imgui.drag_float3(f'##{pid_name}', pid_c.K_p, pid_c.K_i, pid_c.K_d, 0.001)

        if pitch_changed:
            pid_c.K_p, pid_c.K_i, pid_c.K_d = pid_c_raw

        return pitch_changed, pid_c

    def _draw_content(self):
        pitch_changed, self._pitch_pid_c = self._draw_pid_coefficients("Pitch", self._pitch_pid_c)
        yaw_changed, self._yaw_pid_c = self._draw_pid_coefficients("Yaw", self._yaw_pid_c)
        roll_changed, self._roll_pid_c = self._draw_pid_coefficients("Roll", self._roll_pid_c)

        if pitch_changed or yaw_changed or roll_changed:
            self._on_changed_callback(self._pitch_pid_c, self._yaw_pid_c, self._roll_pid_c)
