from abc import abstractmethod

from threading import Thread

import cv2


class VideoCaptureBase:
    @abstractmethod
    def read(self) -> tuple:
        return False, None

    @abstractmethod
    def release(self):
        pass


class VideoCaptureCV(VideoCaptureBase):
    def __init__(self, src=0, width=1280, height=720):
        self.camera = cv2.VideoCapture(src)

        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read(self) -> tuple:
        return self.camera.read()

    def release(self):
        self.camera.release()


class VideoCaptureCVStream(VideoCaptureCV):
    def __init__(self, src=0, width=1280, height=720):
        super().__init__(src, width, height)

        self._grabbed, self._frame = self.camera.read()

        self._stopped = False

        self._thread = Thread(target=self.update, daemon=False, args=())

        self.start()

    def start(self):
        self._thread.start()
        return self

    def update(self):
        while not self._stopped:
            self._grabbed, self._frame = self.camera.read()
        self._grabbed, self._frame = False, None

    def read(self):
        return self._grabbed, self._frame

    def stop(self):
        self._stopped = True
        self._thread.join()


if __name__ == "__main__":
    capture = VideoCaptureCVStream(0)
    while True:
        grabbed, frame = capture.read()

        if not grabbed:
            break

        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1)
        if key == ord('q'):
            capture.stop()
