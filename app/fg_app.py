from typing import Optional

import cv2

import glfw
import imgui

from app.core import VideoCaptureCVStream
from app.core.tracker import TargetManager

from app.core.autopilot import Port
from app.core.autopilot.fg_controller import FGController

from app.core.autopilot.fg_brain import BrainBase
from app.core.autopilot.fg_brain import ManualBrain
from app.core.autopilot.fg_brain import AutopilotBrain
from app.core.autopilot.fg_brain import TrackingAutopilotBrain

from app.gui import ImGuiApp

from app.gui.objects.windows.control_windows import UserWindow
from app.gui.objects.windows.image_windows import ZoomImageWindow
from app.gui.objects.windows.image_windows import TrackerImageWindow


class FGApp(ImGuiApp):
    def __init__(self, window_width, window_height, fullscreen):
        super().__init__(window_width, window_height, fullscreen)

        self._video_capture = VideoCaptureCVStream(src=2)

        #self._target_manager = TargetManager()
        self._is_tracking = False

        self._brains = {
            BrainBase.BrainType.MANUAL: ManualBrain(),
            BrainBase.BrainType.AUTOPILOT: AutopilotBrain(),
            BrainBase.BrainType.TRACKING: TrackingAutopilotBrain()
        }
        self._brain = BrainBase()

        self._controller: Optional[FGController] = None

        self._settings_window = UserWindow(self._on_connect_clicked, self._on_stop_clicked, self._on_brain_changed)

        self._image_window = ZoomImageWindow()

    def _terminate(self):
        super()._terminate()

        self._video_capture.stop()

        if self._controller:
            self._controller.stop()

    def _on_connect_clicked(self,
                            host: str,
                            fdm_out_port: int, fdm_in_port: int,
                            ctrls_out_port: int, ctrls_in_port: int):

        if type(self._brain) is BrainBase:
            self._brain = self._brains[BrainBase.BrainType.MANUAL]
            
        if self._controller:
            self._controller.stop()

        self._controller = FGController(self._brain)
        self._controller.connect(host=host,
                                 fdm_port=Port(fdm_out_port, fdm_in_port),
                                 ctrls_port=Port(ctrls_out_port, ctrls_in_port),
                                 disconnect_callback=self._disconnect_callback)
        self._controller.start()

        if isinstance(self._brain, TrackingAutopilotBrain):
            self._image_window = TrackerImageWindow(self._on_roi_selected)
        else:
            self._image_window = ZoomImageWindow()
            
    def _disconnect_callback(self, disconnect):
        if disconnect:
            print("=====================+NO CONNECTION==========================")

    def _on_stop_clicked(self):
        if self._controller:
            self._controller.stop()

    def _on_brain_changed(self, brain_type):
        self._brain = self._brains[brain_type]
        self._settings_window.set_brain(self._brain)

    def _on_roi_selected(self, selected_roi):
        if not isinstance(self._brain, TrackingAutopilotBrain):
            return

        if not selected_roi:
            return

        grabbed, frame = self._video_capture.read()
        if grabbed:
            self._target_manager.init_tracker(frame, selected_roi)
            self._brain.set_target_location(self._target_manager.target_location)

    def _update_target_manager(self, frame):
        if not isinstance(self._brain, TrackingAutopilotBrain):
            return

        if self._target_manager.is_tracker_initialized:
            score, roi = self._target_manager.update_tracker(frame)

            if score < 0.6 and self._is_tracking:
                self._toggle_tracking()
                return

            if self._is_tracking:
                self._brain.set_object_bbox(roi)

            self._image_window.selected_roi = roi

    def _update_image_window(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self._image_window.upload_image(rgb_frame)

    def _toggle_tracking(self):
        if not isinstance(self._brain, TrackingAutopilotBrain):
            return
        if not isinstance(self._image_window, TrackerImageWindow):
            return

        if self._target_manager.is_tracker_initialized:
            self._is_tracking = not self._is_tracking

            if self._is_tracking:
                self._image_window.set_bbox_color(self._image_window.TRACKING_BBOX_COLOR)
            else:
                self._brain.set_object_bbox(None)
                self._image_window.set_bbox_color(self._image_window.DEFAULT_BBOX_COLOR)
        else:
            print("Tracker is not initialized.")

    def _cancel_tracking(self):
        if not isinstance(self._brain, TrackingAutopilotBrain):
            return
        if not isinstance(self._image_window, TrackerImageWindow):
            return

        self._is_tracking = False

        self._target_manager.reset_tracker()

        self._brain.set_object_bbox(None)

        self._image_window.reset_roi()

    def keyboard_input(self):
        super().keyboard_input()

        if isinstance(self._brain, TrackingAutopilotBrain):
            if imgui.is_key_pressed(glfw.KEY_T):
                self._toggle_tracking()

            if imgui.is_key_pressed(glfw.KEY_C):
                self._cancel_tracking()

    def draw_content(self):
        display_size = imgui.get_io().display_size

        image_window_width_scale = 0.8
        self._image_window.size = imgui.Vec2(display_size[0] * image_window_width_scale, display_size[1])
        self._settings_window.position = imgui.Vec2(display_size[0] * image_window_width_scale, 0)
        self._settings_window.size = imgui.Vec2(display_size[0] * (1 - image_window_width_scale), display_size[1])

        grabbed, frame = self._video_capture.read()
        if grabbed:
            #self._update_target_manager(frame)
            self._update_image_window(frame)
        self._image_window.draw()

        self._settings_window.draw()


if __name__ == "__main__":
    app = FGApp(1280, 720, fullscreen=False)
    app.run()
