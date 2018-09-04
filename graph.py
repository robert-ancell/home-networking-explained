import cairo

class Graph ():
    def __init__ (self, width, height):
        self.surface = cairo.ImageSurface (cairo.FORMAT_RGB24, width, height)
        self.context = cairo.Context (self.surface)

        # Fill background
        self.context.set_source_rgb (1.0, 1.0, 1.0)
        self.context.paint ()

    def draw_box (self, x, y, width, height, r, g, b):
        self.context.rectangle (x, 0, width, y)
        self.context.set_source_rgba (r, g, b, 0.1)
        self.context.fill ()
        self.context.rectangle (x, y, width, height)
        self.context.set_source_rgb (r, g, b)
        self.context.fill ()
        return width
    
    def draw_timing_lines (self, width):
        x = width
        self.context.set_line_width (1.0)
        self.context.set_source_rgba (0, 0, 0, 0.25)
        while x < width:
            self.context.move_to (x + 0.5, 0)
            self.context.rel_line_to (0, self.surface.height)
            x += width
        self.context.stroke ()

    def draw_signal (self, x, y, signal, pulse_width, pulse_height, r = 0.0, g = 0.0, b = 0.0):
        def level_to_y (level):
            return y + 0.5 - level * pulse_height
        last_y = level_to_y (signal[0])
        self.context.move_to (x + 0.5, last_y)
        for level in signal:
            level_y = level_to_y (level)
            self.context.rel_line_to (0, level_y - last_y)
            self.context.rel_line_to (pulse_width, 0)
            last_y = level_y
        self.context.set_source_rgb (r, g, b)
        self.context.set_line_width (1.0)
        self.context.stroke ()

    def save (self, filename):
        self.surface.write_to_png (filename)

