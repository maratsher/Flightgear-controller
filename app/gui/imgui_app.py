from __future__ import annotations

import signal

import glfw
import OpenGL.GL as gl

import imgui
from imgui import plot as implot
from imgui.integrations.glfw import GlfwRenderer

from app.gui.imgui_fonts import ImGuiFonts


class ImGuiApp:
    def __init__(self, window_width, window_height, fullscreen):
        self._window_width = window_width
        self._window_height = window_height

        self._fullscreen = fullscreen

        self.__window = None
        self.__renderer = None

        self.__init_app()

    @staticmethod
    def init_glfw_window(name, width, height, fullscreen):
        if not glfw.init():
            print("[ERROR] Could not initialize OpenGL context")
            exit(1)

        # OS X supports only forward-compatible modules profiles from 3.2
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

        # Select window mode
        primary_monitor = None
        if fullscreen:
            primary_monitor = glfw.get_primary_monitor()
            width, height = glfw.get_video_mode(primary_monitor).size

        # Create a windows and its OpenGL context
        window = glfw.create_window(width, height, name, primary_monitor, None)
        glfw.make_context_current(window)

        if not window:
            glfw.terminate()
            print("[ERROR] Could not initialize Window")
            exit(1)

        return window

    @staticmethod
    def set_custom_style():
        styles = imgui.get_style()

        styles.window_rounding = 0
        styles.child_rounding = 0
        styles.frame_rounding = 2
        styles.popup_rounding = 0
        styles.scrollbar_size = 7
        styles.scrollbar_rounding = 3
        styles.grab_rounding = 2
        styles.tab_rounding = 2

        colors = styles.colors

        colors[imgui.COLOR_TEXT] = imgui.Vec4(0.97, 0.97, 0.97, 0.99)
        colors[imgui.COLOR_TEXT_DISABLED] = imgui.Vec4(0.6, 0.6, 0.6, 0.6)
        colors[imgui.COLOR_WINDOW_BACKGROUND] = imgui.Vec4(0.09, 0.09, 0.09, 0.99)
        colors[imgui.COLOR_CHILD_BACKGROUND] = imgui.Vec4(0.09, 0.09, 0.09, 0.99)
        colors[imgui.COLOR_POPUP_BACKGROUND] = imgui.Vec4(0.15, 0.15, 0.15, 0.99)
        colors[imgui.COLOR_BORDER] = imgui.Vec4(0.2, 0.2, 0.2, 0.99)
        colors[imgui.COLOR_BORDER_SHADOW] = imgui.Vec4(0.0, 0.0, 0.0, 0.0)
        colors[imgui.COLOR_FRAME_BACKGROUND] = imgui.Vec4(0.25, 0.25, 0.25, 0.99)
        colors[imgui.COLOR_FRAME_BACKGROUND_HOVERED] = imgui.Vec4(0.27, 0.27, 0.27, 0.99)
        colors[imgui.COLOR_FRAME_BACKGROUND_ACTIVE] = imgui.Vec4(0.24, 0.24, 0.24, 0.99)
        colors[imgui.COLOR_TITLE_BACKGROUND] = imgui.Vec4(0.07, 0.07, 0.07, 0.99)
        colors[imgui.COLOR_TITLE_BACKGROUND_ACTIVE] = imgui.Vec4(0.13, 0.13, 0.13, 0.99)
        colors[imgui.COLOR_TITLE_BACKGROUND_COLLAPSED] = imgui.Vec4(0.13, 0.13, 0.13, 0.99)
        colors[imgui.COLOR_MENUBAR_BACKGROUND] = imgui.Vec4(0.07, 0.07, 0.07, 0.99)
        colors[imgui.COLOR_SCROLLBAR_BACKGROUND] = imgui.Vec4(0.13, 0.13, 0.13, 0.0)
        colors[imgui.COLOR_SCROLLBAR_GRAB] = imgui.Vec4(0.15, 0.15, 0.15, 0.99)
        colors[imgui.COLOR_SCROLLBAR_GRAB_HOVERED] = imgui.Vec4(0.13, 0.13, 0.13, 0.99)
        colors[imgui.COLOR_SCROLLBAR_GRAB_ACTIVE] = imgui.Vec4(0.16, 0.16, 0.16, 0.99)
        colors[imgui.COLOR_CHECK_MARK] = imgui.Vec4(0.78, 0.78, 0.78, 0.99)
        colors[imgui.COLOR_SLIDER_GRAB] = imgui.Vec4(0.39, 0.39, 0.39, 0.99)
        colors[imgui.COLOR_SLIDER_GRAB_ACTIVE] = imgui.Vec4(0.35, 0.35, 0.35, 0.99)
        colors[imgui.COLOR_BUTTON] = imgui.Vec4(0.13, 0.59, 0.95, 0.99)
        colors[imgui.COLOR_BUTTON_HOVERED] = imgui.Vec4(0.19, 0.62, 0.96, 0.99)
        colors[imgui.COLOR_BUTTON_ACTIVE] = imgui.Vec4(0.13, 0.59, 0.95, 0.99)
        colors[imgui.COLOR_HEADER] = imgui.Vec4(0.27, 0.27, 0.27, 0.99)
        colors[imgui.COLOR_HEADER_HOVERED] = imgui.Vec4(0.24, 0.24, 0.24, 0.99)
        colors[imgui.COLOR_HEADER_ACTIVE] = imgui.Vec4(0.31, 0.31, 0.31, 0.99)
        colors[imgui.COLOR_SEPARATOR] = imgui.Vec4(0.5, 0.5, 0.5, 0.6)
        colors[imgui.COLOR_SEPARATOR_HOVERED] = imgui.Vec4(0.7, 0.7, 0.7, 0.99)
        colors[imgui.COLOR_SEPARATOR_ACTIVE] = imgui.Vec4(0.9, 0.9, 0.9, 0.99)
        colors[imgui.COLOR_RESIZE_GRIP] = imgui.Vec4(0.13, 0.13, 0.13, 0.99)
        colors[imgui.COLOR_RESIZE_GRIP_HOVERED] = imgui.Vec4(0.2, 0.2, 0.2, 0.99)
        colors[imgui.COLOR_RESIZE_GRIP_ACTIVE] = imgui.Vec4(0.16, 0.16, 0.16, 0.99)
        colors[imgui.COLOR_TAB] = imgui.Vec4(0.09, 0.09, 0.09, 0.99)
        colors[imgui.COLOR_TAB_HOVERED] = imgui.Vec4(0.13, 0.13, 0.13, 0.99)
        colors[imgui.COLOR_TAB_ACTIVE] = imgui.Vec4(0.13, 0.59, 0.95, 0.99)
        colors[imgui.COLOR_TAB_UNFOCUSED] = imgui.Vec4(0.34, 0.54, 0.74, 0.65)
        colors[imgui.COLOR_TAB_UNFOCUSED_ACTIVE] = imgui.Vec4(0.31, 0.51, 0.71, 0.78)
        colors[imgui.COLOR_PLOT_LINES] = imgui.Vec4(1.0, 1.0, 1.0, 0.99)
        colors[imgui.COLOR_PLOT_LINES_HOVERED] = imgui.Vec4(0.9, 0.7, 0.0, 0.99)
        colors[imgui.COLOR_PLOT_HISTOGRAM] = imgui.Vec4(0.9, 0.7, 0.0, 0.99)
        colors[imgui.COLOR_PLOT_HISTOGRAM_HOVERED] = imgui.Vec4(1.0, 0.6, 0.0, 0.99)
        colors[imgui.COLOR_TABLE_HEADER_BACKGROUND] = imgui.Vec4(0.19, 0.19, 0.19, 0.99)
        colors[imgui.COLOR_TABLE_BORDER_STRONG] = imgui.Vec4(0.31, 0.31, 0.35, 0.99)
        colors[imgui.COLOR_TABLE_BORDER_LIGHT] = imgui.Vec4(0.23, 0.23, 0.25, 0.99)
        # colors[imgui.TABLE_ROW_BACKGROUND] = imgui.Vec4(0.0, 0.0, 0.0, 0.0)
        colors[imgui.COLOR_TABLE_ROW_BACKGROUND_ALT] = imgui.Vec4(0.99, 0.99, 0.99, 0.06)
        colors[imgui.COLOR_TEXT_SELECTED_BACKGROUND] = imgui.Vec4(0.39, 0.39, 0.39, 0.6)
        colors[imgui.COLOR_DRAG_DROP_TARGET] = imgui.Vec4(0.99, 0.99, 0.0, 0.9)
        colors[imgui.COLOR_NAV_HIGHLIGHT] = imgui.Vec4(0.2, 0.4, 0.6, 0.79)
        colors[imgui.COLOR_NAV_WINDOWING_HIGHLIGHT] = imgui.Vec4(0.99, 0.99, 0.99, 0.7)
        colors[imgui.COLOR_NAV_WINDOWING_DIM_BACKGROUND] = imgui.Vec4(0.8, 0.8, 0.8, 0.2)
        colors[imgui.COLOR_MODAL_WINDOW_DIM_BACKGROUND] = imgui.Vec4(0.2, 0.2, 0.2, 0.35)

    def __init_app(self):
        # Init interrupt handler
        InterruptHandler.signal()

        # Create imgui and impot context
        imgui_context = imgui.create_context()
        _ = implot.create_context()
        implot.set_imgui_context(imgui_context)

        # Create glfw windows and renderer
        self.__window = self.init_glfw_window("Flight Gear Controller", self._window_width, self._window_height, self._fullscreen)
        self.__renderer = GlfwRenderer(self.__window)

        # Init theme for impot and imgui
        imgui.style_colors_dark()
        self.set_custom_style()
        implot.get_style().anti_aliased_lines = True

        # Init fonts
        ImGuiFonts.init_fonts(font_size=20, fonts_path="resources/fonts/PT_Sans/", glfw_window=self.__window)
        self.__renderer.refresh_font_texture()

        return self

    def __shutdown(self):
        self._terminate()

        self.__renderer.shutdown()
        glfw.terminate()

    def _terminate(self):
        pass

    def draw_content(self):
        pass

    def keyboard_input(self):
        if imgui.is_key_pressed(glfw.KEY_F11):
            if not self._fullscreen:
                primary_monitor = glfw.get_primary_monitor()
                mode = glfw.get_video_mode(primary_monitor)
                glfw.set_window_monitor(self.__window, primary_monitor, 0, 0, mode.size[0], mode.size[1], 0)
            else:
                glfw.set_window_monitor(self.__window, None, 0, 0, self._window_width, self._window_height, 0)
            self._fullscreen = not self._fullscreen

    def run(self):
        if not self.__renderer:
            print("[ERROR] glfw windows is not initialized. Call ImGuiApp.init()")
            exit(1)

        while not glfw.window_should_close(self.__window) and not InterruptHandler.interrupted:
            glfw.poll_events()
            self.__renderer.process_inputs()

            imgui.new_frame()

            self.draw_content()

            self.keyboard_input()

            gl.glClearColor(0.0, 0.0, 0.0, 1.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)

            imgui.render()
            self.__renderer.render(imgui.get_draw_data())
            glfw.swap_buffers(self.__window)

        self.__shutdown()


class InterruptHandler:
    interrupted = False

    @staticmethod
    def signal():
        signal.signal(signal.SIGINT, InterruptHandler.exit)
        signal.signal(signal.SIGTERM, InterruptHandler.exit)

    @staticmethod
    def exit(*args):
        InterruptHandler.interrupted = True
