from .tracker import Tracker


class TargetManager:
    def __init__(self):
        self._tracker = Tracker(backbone="resources/models/tracker/backbone.onnx",
                                rpn_head="resources/models/tracker/rpn.onnx")
        self._is_tracker_initialized = False

        self._target_location = None

    @property
    def is_tracker_initialized(self):
        return self._is_tracker_initialized

    @property
    def target_location(self):
        return self._target_location

    def reset_tracker(self):
        self._is_tracker_initialized = False

    def init_tracker(self, image, roi):
        self._tracker.select_obj(image, roi)
        self._is_tracker_initialized = True

        self._target_location = image.shape[1] // 2, image.shape[0] // 2

    def update_tracker(self, image):
        assert self._is_tracker_initialized

        score, roi = self._tracker.search_obj(image)
        roi = list(map(int, roi))

        return score, roi
