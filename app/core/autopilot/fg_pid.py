import dataclasses
from abc import abstractmethod


@dataclasses.dataclass
class PIDControllerCoefficient:
    K_p: float
    K_i: float
    K_d: float


class Controller:
    def __init__(self):
        self._P_out = 0

    @property
    def P_out(self):
        return self._P_out

    @abstractmethod
    def update(self, SP, PV):
        raise NotImplemented()


class LerpController(Controller):
    def __init__(self):
        super().__init__()

    def update(self, SP, PV, t=0.01):
        self._P_out = (1 - t) * PV + t * SP
        return self._P_out


class PController(Controller):
    def __init__(self):
        """
        Simple Proportional Controller implementation

        https://en.wikipedia.org/wiki/Proportional_control
        """
        super(PController, self).__init__()

    def update(self, SP, PV, K_p=0.1):
        """
        Output of a proportional controller

        :param SP: Set point
        :param PV: Process variable
        :param K_p: Proportional gain
        :return: Output of the proportional controller
        """
        self._P_out = (SP - PV) * K_p
        return self._P_out


class PIDController(Controller):
    def __init__(self):
        """
        PID Controller implementation

        https://en.wikipedia.org/wiki/PID_controller
        """

        super(PIDController, self).__init__()

        self._error_sum = 0
        self._last_error = 0

    def update(self, SP, PV, K_p=0.1, K_i=0, K_d=0, dt=0.1):
        """
        Output of a PID controller

        :param SP: Set point
        :param PV: Process variable
        :param K_p: Proportional gain
        :param K_i: Integral gain
        :param K_d: Derivative gain
        :param dt: Delta time
        :return: Output of the PID controller
        """

        error = SP - PV

        # Proportional component
        proportional_term = K_p * error

        # Integral component
        self._error_sum += error * dt
        integral_term = K_i * self._error_sum

        # Derivative component
        derivative_term = K_d * (error - self._last_error) / dt
        self._last_error = error

        self._P_out = proportional_term + integral_term + derivative_term

        return self._P_out
