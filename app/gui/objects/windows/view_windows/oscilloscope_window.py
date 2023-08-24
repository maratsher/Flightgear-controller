from __future__ import annotations

import enum
from array import array

import numpy as np

import imgui
from imgui import plot as implot

from app.gui.objects.windows import Window


class OscilloscopeWindow(Window):
    class PlotType(enum.Enum):
        PITCH = "Pitch"
        YAW = "Yaw"
        ROLL = "Roll"

    class AxisColor:
        X = (255, 0, 0, 1)
        Y = (0, 255, 0, 1)
        Z = (0, 0, 255, 1)

        @staticmethod
        def get_color(plot_type: OscilloscopeWindow.PlotType):
            if plot_type is OscilloscopeWindow.PlotType.PITCH:
                return OscilloscopeWindow.AxisColor.X
            elif plot_type is OscilloscopeWindow.PlotType.YAW:
                return OscilloscopeWindow.AxisColor.Y
            elif plot_type is OscilloscopeWindow.PlotType.ROLL:
                return OscilloscopeWindow.AxisColor.Z

    def __init__(self, plot_length=2000):
        super().__init__()
        self._id = "Plot"

        self._plot_length = plot_length

        self._target_pitch = 0
        self._target_yaw = 0
        self._target_roll = 0

        self._has_target_data = False

        self._pitch_data = []
        self._roll_data = []
        self._yaw_data = []

        self._target_line_color = (30, 221, 221, 1)

    def put_plot_data(self, value, data_type):
        if data_type is self.PlotType.PITCH:
            self._pitch_data = (self._pitch_data + [value])[-self._plot_length:]
        elif data_type is self.PlotType.YAW:
            self._yaw_data = (self._yaw_data + [value])[-self._plot_length:]
        elif data_type is self.PlotType.ROLL:
            self._roll_data = (self._roll_data + [value])[-self._plot_length:]

    def put_target_data(self, value, data_type):
        if data_type is self.PlotType.PITCH:
            self._target_pitch = value
        elif data_type is self.PlotType.YAW:
            self._target_yaw = value
        elif data_type is self.PlotType.ROLL:
            self._target_roll = value

        self._has_target_data = True

    def clear_plot_data(self):
        self._pitch_data.clear()
        self._yaw_data.clear()
        self._roll_data.clear()

    def clear_target_data(self):
        self._target_pitch = 0
        self._target_yaw = 0
        self._target_roll = 0
        self._has_target_data = False

    def _draw_content(self):
        plot_data = {
            self.PlotType.PITCH: self._pitch_data,
            self.PlotType.YAW: self._yaw_data,
            self.PlotType.ROLL: self._roll_data
        }
        target_data = {
            self.PlotType.PITCH: self._target_pitch,
            self.PlotType.YAW: self._target_yaw,
            self.PlotType.ROLL: self._target_roll
        }

        for plot_type in self.PlotType:
            implot.fit_next_plot_axes()
            if implot.begin_plot(plot_type.value, size=(imgui.get_content_region_available_width(), 200)):

                values = plot_data.get(plot_type)
                n_values = len(values)
                target = target_data.get(plot_type)

                implot.push_colormap(0)

                if self._has_target_data:
                    implot.set_next_line_style(self._target_line_color, 2)
                    implot.plot_line2(plot_type.value + " target",
                                      array("f", [0, n_values]), array("f", [target] * 2), 2)

                implot.set_next_line_style(self.AxisColor.get_color(plot_type), 4)
                implot.plot_line2(plot_type.value, array("f", np.arange(n_values)), array("f", values), n_values)

                implot.pop_colormap()

                implot.end_plot()
