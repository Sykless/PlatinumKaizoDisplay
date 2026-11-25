import ctypes
import tkinter as tk
from typing import Dict
import ttkbootstrap as ttk
from ctypes import wintypes

from page import InterfacePage

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 850
MIN_WINDOW_WIDTH = 760
MIN_WINDOW_HEIGHT = 480
IMAGE_AREA_WIDTH = 660
IMAGE_AREA_HEIGHT = 260

BACKGROUND_COLOR = "#22252B"
ACCENT_COLOR = "#36C98F"
ACCENT_HOVER = "#45DCA2"
MUTED_COLOR = "#A0A5AE"

STATUS_BACKGROUND = "#191C21"
STATUS_RUNNING = "#36C98F"
STATUS_STOPPED = "#F06464"
STATUS_CHECKING = "#F0A43C"

LUA_RUNNING = 1
LUA_CHECKING = 0
LUA_STOPPED = -1

FONT = "Segoe UI"


# ======================================================
# MAIN APPLICATION
# ======================================================
class MainInterface:
    def __init__(self, pages):
        self.pages: Dict[str, InterfacePage] = {}
        self.currentPage = None

        # Overriden methodes
        self.onTrainerPreview = None
        self.handleOptionsChanged = None

        # Init Window
        self.setupWindowsDpi()
        self.root = ttk.Window(themename = "darkly")
        self.root.title("Pokémon Platinum Kaizo Display")

        # Setup size, style
        self.setupWindow()
        self.setupStyles()
        self.createInterface(pages)
        self.setupWindowsTitleBar(self.root)

        # Give focus to root when clicking away
        self.root.bind_all("<Button-1>", self.clearFocus, add = "+")
        

    # ======================================================
    # WINDOWS DPI AND TITLE BAR
    # ======================================================
    def setupWindowsDpi(self):
        try:
            ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except (AttributeError, OSError):
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except (AttributeError, OSError):
                pass

    # Vibe-coded, I'm shit using ctypes
    def setupWindowsTitleBar(self, root):
        try:
            root.update_idletasks()

            user32 = ctypes.windll.user32
            dwmApi = ctypes.windll.dwmapi

            user32.GetAncestor.argtypes = [
                wintypes.HWND,
                wintypes.UINT
            ]
            user32.GetAncestor.restype = wintypes.HWND

            hwnd = user32.GetAncestor(root.winfo_id(), 2)

            if not hwnd:
                hwnd = root.winfo_id()

            dwmApi.DwmSetWindowAttribute.argtypes = [
                wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
            dwmApi.DwmSetWindowAttribute.restype = ctypes.c_long

            def setAttribute(attribute, value):
                return dwmApi.DwmSetWindowAttribute(
                    hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value))

            def toColorRef(hexColor):
                red = int(hexColor[1:3], 16)
                green = int(hexColor[3:5], 16)
                blue = int(hexColor[5:7], 16)

                return ctypes.c_uint32(red | (green << 8) | (blue << 16))

            # Enable dark title bar
            setAttribute(20, ctypes.c_int(1))

            # Custom title bar colors
            setAttribute(35, toColorRef("#191C22"))
            setAttribute(36, toColorRef("#FFFFFF"))
            setAttribute(34, toColorRef("#191C22"))

        except Exception as error:
            print(f"Title bar customization failed: {error}")


    # --------------------------------------------------
    # WINDOW
    # --------------------------------------------------
    def setupWindow(self):
        screenWidth = self.root.winfo_screenwidth()
        screenHeight = self.root.winfo_screenheight()

        # Setup window screen
        windowWidth = max(MIN_WINDOW_WIDTH, min(WINDOW_WIDTH, int(screenWidth * 0.8)))
        windowHeight = max(MIN_WINDOW_HEIGHT, min( WINDOW_HEIGHT, int(screenHeight * 0.8)))
        posX = (screenWidth - windowWidth) // 2
        posY = (screenHeight - windowHeight) // 2
        self.root.geometry(f"{windowWidth}x{windowHeight}+{posX}+{posY}")

        # Setup titlebar
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.root.resizable(True, True)
        self.root.configure(background = BACKGROUND_COLOR)

    # Keep focus if the click is on a textbox, otherwise release it
    def clearFocus(self, event):
        if isinstance(event.widget, tk.Entry):
            return

        self.root.focus_set()

    # --------------------------------------------------
    # STYLES
    # --------------------------------------------------
    def setupStyles(self):
        style = self.root.style
        style.configure("App.TFrame", background = BACKGROUND_COLOR)

    # --------------------------------------------------
    # INTERFACE
    # --------------------------------------------------
    def createInterface(self, pageConfigs):

        # Main container
        self.mainFrame = tk.Frame(self.root, bg = BACKGROUND_COLOR)
        self.mainFrame.pack(fill = "both", expand = True, padx = 10, pady = 10)

        # Top taskbar
        self.createTaskbar(pageConfigs)

        # Page container
        self.pageContainer = tk.Frame(self.mainFrame, bg = BACKGROUND_COLOR)
        self.pageContainer.grid_rowconfigure(0, weight = 1)
        self.pageContainer.grid_columnconfigure(0, weight = 1)
        self.pageContainer.pack(fill = "both", expand = True, pady = (15, 0))

        # Pre-load all pages and store them in a list
        for pageName, config in pageConfigs.items():
            page = InterfacePage(parent = self.pageContainer, name = pageName, sections = config.get("sections"),
                checkboxes = config.get("checkboxes"),
                settings = config.get("settings"),
                optionals = config.get("optionals"))
            
            page.frame.grid(row = 0, column = 0, sticky = "nsew")
            self.pages[pageName] = page

            if pageName == "Trainer":
                page.onPreviewRequested = lambda trainerId: self.onTrainerPreview(trainerId) if self.onTrainerPreview else None
                page.onPinChanged = lambda: self.handleOptionsChanged("Trainer")

        # Display first page
        firstPage = next(iter(self.pages), None)

        if firstPage:
            self.showPage(firstPage)

    # --------------------------------------------------
    # TASKBAR
    # --------------------------------------------------
    def createTaskbar(self, pageConfigs):
        self.taskbar = tk.Frame(self.mainFrame, bg = BACKGROUND_COLOR)
        self.taskbar.pack(fill = "x")

        # Main component
        self.navigationFrame = tk.Frame(self.taskbar, bg = BACKGROUND_COLOR)
        self.navigationFrame.pack(side = "left")
        self.navigationButtons = {}

        # Display all page buttons
        for pageName in pageConfigs:
            button = tk.Label(self.navigationFrame, text = pageName, font = (FONT, 11),
                bg = BACKGROUND_COLOR, fg = MUTED_COLOR, padx = 12, pady = 0, cursor = "hand2")

            button.pack(side = "left")
            button.bind("<Button-1>", lambda event, name = pageName: self.showPage(name))
            button.bind("<Enter>", lambda event, widget = button: self.onNavHover(widget, True))
            button.bind("<Leave>", lambda event, widget = button: self.onNavHover(widget, False))

            self.navigationButtons[pageName] = button

        # Right side, display Lua script status
        self.statusFrame = tk.Frame(self.taskbar, bg = STATUS_BACKGROUND, padx = 10, pady = 7)
        self.statusFrame.pack(side = "right", padx = (10, 0))

        self.luaStatusLabel = tk.Label(self.statusFrame, text = "● LUA STOPPED", font = (FONT, 9, "bold"),
            bg = STATUS_BACKGROUND, fg = STATUS_STOPPED)
        self.luaStatusLabel.pack()
        self.setLuaStatus(LUA_CHECKING)

    def onNavHover(self, button, hovered):
        isSelected = button == self.navigationButtons.get(self.currentPage)

        if isSelected:
            color = ACCENT_COLOR
        elif hovered:
            color = ACCENT_HOVER
        else:
            color = MUTED_COLOR

        button.config(fg = color)


    # --------------------------------------------------
    # PAGE NAVIGATION
    # --------------------------------------------------
    def showPage(self, pageName):
        if pageName not in self.pages or pageName == self.currentPage:
            return

        previousPage = self.pages.get(self.currentPage)
        newPage = self.pages[pageName]
        self.currentPage = pageName

        # Draw the new page on top of the old on
        newPage.frame.grid()
        newPage.frame.tkraise()
        self.root.update_idletasks()

        # Remove the old page (avoid small blink)
        if previousPage:
            previousPage.frame.grid_remove()

        # Highlight selected page button
        for buttonName, button in self.navigationButtons.items():
            isSelected = buttonName == pageName

            button.config(fg = (ACCENT_COLOR if isSelected else MUTED_COLOR),
                font = (FONT, 10, "bold" if isSelected else "normal"))


    # --------------------------------------------------
    # LUA STATUS
    # --------------------------------------------------
    def setLuaStatus(self, luaStatus):

        # Display info style 
        if (luaStatus == LUA_RUNNING):
            text = "● LUA SCRIPT RUNNING"
            color = STATUS_RUNNING
        elif (luaStatus == LUA_STOPPED):
            text = "● LUA SCRIPT STOPPED"
            color = STATUS_STOPPED
        else:
            text = "● CHECKING LUA SCRIPT..."
            color = STATUS_CHECKING

        self.luaStatusLabel.config(text = text, fg = color)


    # --------------------------------------------------
    # DATA ACCESS
    # --------------------------------------------------
    def findPage(self, sectionName):
        for page in self.pages.values():
            for section in page.sections:
                if section.lower() == sectionName.lower():
                    return page, section
        return None, None

    def updatePageImage(self, imageName, generatedImage):
        page, section = self.findPage(imageName)
        if page:
            page.updateImage(generatedImage, section)

    def getSelectedCheckboxes(self, sectionName):
        page, section = self.findPage(sectionName)
        return page.getSelectedCheckboxes(section) if page else []

    def getSettingsValues(self, sectionName):
        page, section = self.findPage(sectionName)
        return page.getSettingsValues(section) if page else {}

    def setTrainers(self, trainerList):
        self.pages["Trainer"].setTrainers(trainerList)

    def setLiveTrainer(self, trainer):
        self.pages["Trainer"].setLiveTrainer(trainer)

    def getPinnedTrainer(self):
        return self.pages["Trainer"].pinnedTrainer


    # --------------------------------------------------
    # RUN
    # --------------------------------------------------
    def run(self):
        self.root.mainloop()