import enum

import numpy as np

from app.core.autopilot.fg_pid import LerpController
from app.core.autopilot.fg_pid import PIDController, PIDControllerCoefficient


class BrainBase:
    class BrainType(enum.Enum):
        MANUAL = "Manual"
        AUTOPILOT = "Autopilot"
        TRACKING = "Tracking"

    def update(self, fdm_event_pipe=None, ctrls_event_pipe=None):
        raise NotImplementedError()

    def fdm_update(self, fdm_data, event_pipe):
        raise NotImplementedError()

    def ctrls_update(self, ctrls_data, event_pipe):
        raise NotImplementedError()


class StorageBrain(BrainBase):
    def __init__(self):
        super().__init__()

        self._current_pitch = 0
        self._current_yaw = 0
        self._current_roll = 0

    @property
    def pitch(self) -> float:
        return self._current_pitch

    @property
    def yaw(self) -> float:
        return self._current_yaw

    @property
    def roll(self) -> float:
        return self._current_roll


class ManualBrain(StorageBrain):
    def __init__(self):
        super().__init__()

    def update(self, fdm_event_pipe=None, ctrls_event_pipe=None):
        if fdm_event_pipe and fdm_event_pipe.parent_poll():
            self._current_pitch, self._current_yaw, self._current_roll = fdm_event_pipe.parent_recv()

    def fdm_update(self, fdm_data, event_pipe):
        pitch = np.rad2deg(fdm_data.theta_rad)
        yaw = np.rad2deg(fdm_data.psi_rad)
        roll = np.rad2deg(fdm_data.phi_rad)

        event_pipe.child_send((pitch, yaw, roll))

    def ctrls_update(self, ctrls_data, event_pipe):
        return None


class PilotBrain(StorageBrain):
    def __init__(self):
        super().__init__()

        self._throttle_controller = LerpController()

        self._pitch_controller = PIDController()
        self._yaw_controller = PIDController()
        self._roll_controller = PIDController()

        self._pitch_controller_coefficients = PIDControllerCoefficient(K_p=0.1, K_i=0.005, K_d=0.001)
        self._yaw_controller_coefficients = PIDControllerCoefficient(K_p=0.1, K_i=0, K_d=0)
        self._roll_controller_coefficients = PIDControllerCoefficient(K_p=0.05, K_i=0.005, K_d=0.001)

    @property
    def pitch_pid_c(self):
        return self._pitch_controller_coefficients

    @property
    def yaw_pid_c(self):
        return self._yaw_controller_coefficients

    @property
    def roll_pid_c(self):
        return self._roll_controller_coefficients

    @pitch_pid_c.setter
    def pitch_pid_c(self, pid_c):
        self._pitch_controller_coefficients = pid_c

    @yaw_pid_c.setter
    def yaw_pid_c(self, pid_c):
        self._yaw_controller_coefficients = pid_c

    @roll_pid_c.setter
    def roll_pid_c(self, pid_c):
        self._roll_controller_coefficients = pid_c


class AutopilotBrain(PilotBrain):
    def __init__(self):
        super().__init__()

        self._target_pitch = 0
        self._target_yaw = 0
        self._target_roll = 0
        self._target_throttle = 0

    def set_target_pitch(self, pitch):
        self._target_pitch = pitch

    def set_target_yaw(self, yaw):
        self._target_yaw = yaw

    def set_target_roll(self, roll):
        self._target_roll = roll

    def set_target_throttle(self, throttle):
        self._target_throttle = throttle

    def update(self, fdm_event_pipe=None, ctrls_event_pipe=None):
        if fdm_event_pipe and fdm_event_pipe.parent_poll():
            self._current_pitch, self._current_yaw, self._current_roll = fdm_event_pipe.parent_recv()

            ctrls_event_pipe.parent_send((self._target_throttle,
                                          self._target_pitch, self._target_yaw, self._target_roll,
                                          self._current_pitch, self._current_yaw, self._current_roll,
                                          self._pitch_controller_coefficients,
                                          self._yaw_controller_coefficients,
                                          self._roll_controller_coefficients))

    def fdm_update(self, fdm_data, event_pipe):
        pitch = np.rad2deg(fdm_data.theta_rad)
        yaw = np.rad2deg(fdm_data.psi_rad)
        roll = np.rad2deg(fdm_data.phi_rad)

        event_pipe.child_send((pitch, yaw, roll))

    def ctrls_update(self, ctrls_data, event_pipe):
        target_throttle = 0

        if event_pipe.child_poll():
            target_throttle, target_pitch, target_yaw, target_roll, \
                pitch, yaw, roll, \
                pitch_pid_c, yaw_pid_c, roll_pid_c = event_pipe.child_recv()

            # Update controllers
            self._pitch_controller.update(target_pitch, pitch,
                                          K_p=pitch_pid_c.K_p,
                                          K_i=pitch_pid_c.K_i,
                                          K_d=pitch_pid_c.K_d)
            self._yaw_controller.update(target_yaw, yaw,
                                        K_p=yaw_pid_c.K_p,
                                        K_i=yaw_pid_c.K_i,
                                        K_d=yaw_pid_c.K_d)
            self._roll_controller.update(target_roll, roll,
                                         K_p=yaw_pid_c.K_p,
                                         K_i=yaw_pid_c.K_i,
                                         K_d=yaw_pid_c.K_d)

            # Debug
            # print(f"Pitch:\t {pitch:.2f} \t Elevator:\t {self._pitch_controller.P_out:.2f}")
            # print(f"Yaw:\t {yaw:.2f} \t Rudder:\t {self._yaw_controller.P_out:.2f}", end='\n\n')
            # print(f"Roll:\t {roll:.2f} \t Aileron:\t {self._roll_controller.P_out:.2f}")

        # Control surfaces
        ctrls_data.elevator = -self._pitch_controller.P_out
        ctrls_data.rudder = self._yaw_controller.P_out
        ctrls_data.aileron = self._roll_controller.P_out

        # Throttle
        current_throttle = self._throttle_controller.P_out
        target_throttle = self._throttle_controller.update(target_throttle, current_throttle, t=0.1)
        ctrls_data.throttle = [target_throttle] * 4  # engines number

        return ctrls_data


class TrackingAutopilotBrain(PilotBrain):
    def __init__(self):
        super().__init__()

        self._object_bbox = None
        self._target_location = None

        self._pitch_controller_coefficients = PIDControllerCoefficient(K_p=0.002, K_i=0.001, K_d=0)
        self._yaw_controller_coefficients = PIDControllerCoefficient(K_p=0.001, K_i=0.0001, K_d=0)
        self._roll_controller_coefficients = PIDControllerCoefficient(K_p=0.05, K_i=0, K_d=0)

    def set_object_bbox(self, object_bbox):
        self._object_bbox = object_bbox

    def set_target_location(self, location):
        self._target_location = location

    def update(self, fdm_event_pipe=None, ctrls_event_pipe=None):
        if fdm_event_pipe and fdm_event_pipe.parent_poll():
            self._current_pitch, self._current_yaw, self._current_roll = fdm_event_pipe.parent_recv()

            if ctrls_event_pipe:
                ctrls_event_pipe.parent_send((self._target_location, self._object_bbox,
                                              self._current_pitch, self._current_yaw, self._current_roll,
                                              self._pitch_controller_coefficients,
                                              self._yaw_controller_coefficients,
                                              self._roll_controller_coefficients))

    def fdm_update(self, fdm_data, event_pipe):
        pitch = np.rad2deg(fdm_data.theta_rad)
        yaw = np.rad2deg(fdm_data.psi_rad)
        roll = np.rad2deg(fdm_data.phi_rad)

        event_pipe.child_send((pitch, yaw, roll))

    def ctrls_update(self, ctrls_data, event_pipe):
        object_bbox = None

        if event_pipe.child_poll():
            target_location, object_bbox, pitch, yaw, roll,\
                pitch_pid_c, yaw_pid_c, roll_pid_c = event_pipe.child_recv()  # Unpack tuple from parent

            if object_bbox is not None:
                # Update controllers
                object_location = object_bbox[0] + object_bbox[2] / 2, object_bbox[1] + object_bbox[3] / 2

                self._pitch_controller.update(target_location[1], object_location[1],
                                              K_p=pitch_pid_c.K_p,
                                              K_i=pitch_pid_c.K_i,
                                              K_d=pitch_pid_c.K_d)
                self._yaw_controller.update(target_location[0], object_location[0],
                                            K_p=yaw_pid_c.K_p,
                                            K_i=yaw_pid_c.K_i,
                                            K_d=yaw_pid_c.K_d)
                self._roll_controller.update(0, roll,
                                             K_p=yaw_pid_c.K_p,
                                             K_i=yaw_pid_c.K_i,
                                             K_d=yaw_pid_c.K_d)

                print(f"Target location: {target_location}\t Current location: {object_location}")
                print(f"Roll:\t {roll:.2f} \t Aileron:\t {self._roll_controller.P_out:.2f}")

        # Control surfaces
        ctrls_data.elevator = -self._pitch_controller.P_out
        ctrls_data.rudder = -self._yaw_controller.P_out
        ctrls_data.aileron = self._roll_controller.P_out

        if object_bbox is not None:
            return ctrls_data
