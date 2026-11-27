import logging
import queue
import sys
import tkinter as tk
import ttkbootstrap as ttk

SECTION_COLOR = "#2B2F36"
HOVER_COLOR = "#383E48"
TEXT_COLOR = "#FFFFFF"
MUTED_COLOR = "#A0A5AE"
ACCENT_COLOR = "#36C98F"
ACCENT_HOVER = "#45DCA2"

LOG_FONT = ("Consolas", 10)
MAX_LOG_LINES = 2000
REFRESH_DELAY = 100
MAX_CHUNKS_PER_REFRESH = 500

# ======================================================
# LOG CAPTURE
# ======================================================
class LogStream:
    encoding = "utf-8"

    def __init__(self, messages):
        self.messages = messages

    def write(self, text):
        if text:
            self.messages.put(text)
        return len(text)

    def flush(self):
        pass

    def isatty(self):
        return False


class LogCapture:
    def __init__(self):
        self.messages = queue.SimpleQueue()
        self.stream = LogStream(self.messages)
        self.installed = False

    def install(self):
        if self.installed:
            return

        self.originalStdout = sys.stdout
        self.originalStderr = sys.stderr
        self.originalExceptHook = sys.excepthook

        sys.stdout = self.stream
        sys.stderr = self.stream
        sys.excepthook = self.onFatalError

        # Move the logging handlers created before this point
        self.redirectedHandlers = []
        loggers = [logging.getLogger()] + [logging.getLogger(name) for name in list(logging.root.manager.loggerDict)]

        for logger in loggers:
            for handler in logger.handlers:
                if (isinstance(handler, logging.StreamHandler) and handler.stream is not None
                        and handler.stream in (self.originalStdout, self.originalStderr)):
                    self.redirectedHandlers.append((handler, handler.stream))
                    handler.setStream(self.stream)

        self.installed = True

    def uninstall(self):
        if not self.installed:
            return

        sys.stdout = self.originalStdout
        sys.stderr = self.originalStderr
        sys.excepthook = self.originalExceptHook

        for handler, stream in self.redirectedHandlers:
            handler.setStream(stream)

        # Handlers created while capturing go back to the real console
        loggers = [logging.getLogger()] + [logging.getLogger(name) for name in list(logging.root.manager.loggerDict)]

        for logger in loggers:
            for handler in list(logger.handlers):
                if isinstance(handler, logging.StreamHandler) and handler.stream is self.stream:
                    if self.originalStderr is None:
                        logger.removeHandler(handler)
                    else:
                        handler.setStream(self.originalStderr)

        self.installed = False

    # A crash closes the app, so it must be printed in the real console
    def onFatalError(self, errorType, error, traceback):
        self.uninstall()
        sys.excepthook(errorType, error, traceback)


# ======================================================
# LOGS PAGE
# ======================================================
class LogsPage:
    def __init__(self, parent, logCapture):
        self.logCapture = logCapture
        self.sections = {}

        # A single box taking all the space under the navbar
        self.frame = tk.Frame(parent, bg = SECTION_COLOR)
        self.frame.grid_rowconfigure(0, weight = 1)
        self.frame.grid_columnconfigure(0, weight = 1)

        # Small requested size, the grid stretches it to the available space
        self.console = tk.Text(self.frame, width = 1, height = 1, wrap = "word", font = LOG_FONT,
            bg = SECTION_COLOR, fg = TEXT_COLOR, selectbackground = HOVER_COLOR,
            inactiveselectbackground = HOVER_COLOR, borderwidth = 0, highlightthickness = 0,
            padx = 18, pady = 15, state = "disabled")
        self.console.grid(row = 0, column = 0, sticky = "nsew")

        # Override default Windows scrollbar style
        style = ttk.Style.get_instance()
        style.configure("Dark.Vertical.TScrollbar", background = "#4A515C",
            troughcolor = SECTION_COLOR, bordercolor = SECTION_COLOR, lightcolor = "#4A515C",
            darkcolor = "#4A515C", arrowcolor = MUTED_COLOR, gripcount = 0, relief = "flat")
        style.map("Dark.Vertical.TScrollbar",
            background = [("active", ACCENT_COLOR), ("pressed", ACCENT_HOVER)],
            lightcolor = [("active", ACCENT_COLOR), ("pressed", ACCENT_HOVER)],
            darkcolor = [("active", ACCENT_COLOR), ("pressed", ACCENT_HOVER)])

        self.scrollbar = ttk.Scrollbar(self.frame, orient = "vertical",
            command = self.console.yview, style = "Dark.Vertical.TScrollbar")

        # The column keeps its width so the text doesn't move when the scrollbar appears
        self.frame.grid_columnconfigure(1, minsize = self.scrollbar.winfo_reqwidth())
        self.console.configure(yscrollcommand = self.onConsoleScroll)
        self.refresh()

    # Only show the scrollbar when the logs don't fit in the console
    def onConsoleScroll(self, first, last):
        if float(first) <= 0 and float(last) >= 1:
            self.scrollbar.grid_remove()
        else:
            self.scrollbar.grid(row = 0, column = 1, sticky = "ns")
            self.scrollbar.set(first, last)

    # Move the pending messages into the console
    def refresh(self):
        chunks = []

        while len(chunks) < MAX_CHUNKS_PER_REFRESH and not self.logCapture.messages.empty():
            chunks.append(self.logCapture.messages.get())

        if chunks:
            self.appendText("".join(chunks))

        self.frame.after(REFRESH_DELAY, self.refresh)

    def appendText(self, text):
        atBottom = self.console.yview()[1] >= 0.999

        self.console.config(state = "normal")
        self.console.insert("end-1c", text)

        # Drop the oldest lines to keep the app responsive
        lineCount = int(self.console.index("end-1c").split(".")[0])

        if lineCount > MAX_LOG_LINES:
            self.console.delete("1.0", f"{lineCount - MAX_LOG_LINES + 1}.0")

        self.console.config(state = "disabled")

        if atBottom:
            self.console.see("end")

    # Same methods as InterfacePage, used by the main application
    def getSelectedOptions(self):
        return []

    def updateImage(self, generatedImage):
        pass
