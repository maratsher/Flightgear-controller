from typing import Optional

import time
import threading

from flightgear_python.fg_if import FDMConnection
from flightgear_python.fg_if import CtrlsConnection

from app.core.autopilot import Port

from app.core.autopilot.fg_brain import BrainBase


class FGController(threading.Thread):
    FDM_VERSION = 24
    CTRLS_VERSION = 27

    def __init__(self, brain: BrainBase):
        super().__init__()

        self._brain = brain

        self._fdm_connection: Optional[FDMConnection] = None
        self._ctrls_connection: Optional[CtrlsConnection] = None

        self._fdm_data = None
        self._ctrls_data = None

        self._stop_event = threading.Event()

    def connect(self, host: str, fdm_port: Port, ctrls_port: Port, disconnect_callback: callable):
        """
        Connect to a UDP connection with FlightGear

        :param host: IP address of FG (usually localhost)
        :param fdm_port: Out/In fdm ports of the socket
        :param ctrls_port: Out/In ctrls  ports of the socket
        """

        self._fdm_connection = FDMConnection(fdm_version=self.FDM_VERSION)
        self._fdm_connection.set_disconnect_callback(disconnect_callback=disconnect_callback)
        self._fdm_connection.connect_rx(host, fdm_port.port_out, self._fdm_callback)
        self._fdm_connection.connect_tx(host, fdm_port.port_in)
        self._fdm_connection.start()  # Start the FDM RX/TX loop

        self._ctrls_connection = CtrlsConnection(ctrls_version=self.CTRLS_VERSION)
        self._ctrls_connection.set_disconnect_callback(disconnect_callback=disconnect_callback)
        self._ctrls_connection.connect_rx(host, ctrls_port.port_out, self._ctrls_callback)
        self._ctrls_connection.connect_tx(host, ctrls_port.port_in)
        self._ctrls_connection.start()  # Start the Ctrls RX/TX loop

    def run(self):
        while not self._stop_event.is_set():
            self.update()
            time.sleep(0.01)

    def stop(self):
        self._stop_event.set()

        if self._fdm_connection:
            self._fdm_connection.stop()
        if self._ctrls_connection:
            self._ctrls_connection.stop()

        self.join()

    def update(self):
        self._brain.update(self._fdm_connection.event_pipe, self._ctrls_connection.event_pipe)

    def _fdm_callback(self, fdm_data, event_pipe):
        return self._brain.fdm_update(fdm_data, event_pipe)

    def _ctrls_callback(self, ctrls_data, event_pipe):
        return self._brain.ctrls_update(ctrls_data, event_pipe)


if __name__ == "__main__":
    from app.core.autopilot.fg_brain import AutopilotBrain

    ap_brain = AutopilotBrain()
    ap_brain.set_target_pitch(20)
    ap_brain.set_target_yaw(180)
    ap_brain.set_target_roll(0)
    ap_brain.set_target_throttle(0.6)

    controller = FGController(ap_brain)
    controller.connect("localhost", Port(5501, 5502), Port(5503, 5504))

    while True:
        controller.update()
        time.sleep(0.01)
