import imgui

from .panel import Panel


class AutopilotSettingsPanel(Panel):
    def __init__(self, on_changed_callback: callable):
        super().__init__(name="Autopilot Settings")

        self._target_pitch = 20
        self._target_yaw = 180
        self._target_roll = 0
        self._target_throttle = 0.6

        self._on_changed_callback = on_changed_callback

    def install_target_properties(self):
        self._on_changed_callback(self._target_pitch, self._target_yaw, self._target_roll, self._target_throttle)

    def _draw_content(self):
        pitch_changed, self._target_pitch = imgui.input_float('Pitch', self._target_pitch, 0, 0, '%.1f',
                                                              imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
        yaw_changed, self._target_yaw = imgui.input_float('Yaw', self._target_yaw, 0, 0, '%.1f',
                                                          imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
        roll_changed, self._target_roll = imgui.input_float('Roll', self._target_roll, 0, 0, '%.1f',
                                                            imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
        throttle_changed, self._target_throttle = imgui.input_float('Throttle', self._target_throttle, 0, 0, '%.1f',
                                                                    imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)

        if pitch_changed or yaw_changed or roll_changed or throttle_changed:
            self.install_target_properties()
