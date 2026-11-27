import os
import tkinter as tk
import ttkbootstrap as ttk
from tkinter import font
from typing import List, Optional
from PIL import Image, ImageTk

from trainer import TrainerData
from file import TRAINERSPRITE_FOLDER, OUTPUT_FOLDER

IMAGE_AREA_WIDTH = 660
IMAGE_AREA_HEIGHT = 260
SUGGESTION_MIN_WIDTH = 360
TRAINER_BAR_HEIGHT = 40

# Pages whose generated image is enlarged before display
IMAGE_SCALES = {
    "Party": 2,
    "Trainer": 0.5
}

OPTIONS_PER_ROW = 4

BACKGROUND_COLOR = "#22252B"
SECTION_COLOR = "#2B2F36"
HOVER_COLOR = "#383E48"
BUTTON_COLOR = "#191C21"
BUTTON_HOVER = "#22262C"

TEXT_COLOR = "#FFFFFF"
MUTED_COLOR = "#A0A5AE"
ACCENT_COLOR = "#36C98F"
ACCENT_HOVER = "#45DCA2"

STATUS_RUNNING = "#36C98F"
STATUS_STOPPED = "#F06464"
STATUS_CHECKING = "#F0A43C"

FONT = "Segoe UI"

# ======================================================
# PAGE COMPONENT
# ======================================================
class InterfacePage:
    def __init__(self, parent, name, sections = None, checkboxes = None, textboxes = None, optionals = None, settings = None):
        self.parent = parent
        self.name = name

        # Top area is split into sections, most pages only have one
        self.sections = sections or {name: {"title": name, "checkboxes": checkboxes or {}, "optionals": optionals or {}, "textboxes": textboxes or {}}}
        self.settings = settings or {"sections": {}}
        self.defaultSection = next(iter(self.sections))

        self.checkboxValues = {section: {} for section in self.sections}
        self.textboxesValues = {section: {} for section in self.sections}
        self.textboxWidgets = {section: {} for section in self.sections}
        self.optionalValues = {}
        
        self.outputImages = {}
        self.previewPhotos = {}
        self.imageAreas = {}
        self.imageLabels = {}
        self.sectionFrames = {}

        # Pages with a bar under the image (trainer bar or section titles) have less room for the image
        self.minImageHeight = IMAGE_AREA_HEIGHT + (TRAINER_BAR_HEIGHT if name == "Trainer" or len(self.sections) > 1 else 0)
        self.areaWidth = IMAGE_AREA_WIDTH // len(self.sections)

        # Trainer-only attributes
        self.previewImage = None
        self.spritePhotoRefs = {}
        self.trainerList: List[TrainerData] = []
        self.liveTrainer: Optional[TrainerData] = None
        self.previewTrainer: Optional[TrainerData] = None
        self.pinnedTrainer: Optional[TrainerData] = None

        self.onPreviewRequested = None # Generate new image, set by trainer.py
        self.onPinChanged = None # Override generated image, set by trainer.py
        self.onChange = None # Called when ticking an option

        self.createInterface() 


    # --------------------------------------------------
    # INTERFACE
    # --------------------------------------------------
    def createInterface(self):

        # Main component
        self.frame = tk.Frame(self.parent, bg = BACKGROUND_COLOR)

        # Display the preview for generated image
        self.createImagePreview()

        # Specific interface for Trainers, show arrows to move from a trainer to another
        if (self.name == "Trainer"):
            self.createTrainerNavigation()
            self.createTrainerBar()
        else:
            self.createSectionTitles()

        # Separator between image and options
        separator = ttk.Separator(self.frame, bootstyle = "secondary")
        separator.pack(fill = "x", pady = (18, 18))

        # Options Panel
        self.optionsSection = tk.Frame(self.frame, bg = SECTION_COLOR)
        self.optionsSection.pack(fill = "both", expand = True)
        self.optionsSection.grid_columnconfigure(0, weight = 1)

        # Checkboxes
        self.optionsFrame = tk.Frame(self.optionsSection, bg = SECTION_COLOR)
        self.createSectionOptions()

        # Specific menus for Trainer page
        if (self.name == "Trainer"):
            self.optionalsFrame = tk.Frame(self.optionsSection, bg = SECTION_COLOR)
            self.createOptionsHeader()
            self.createOptionalsScrollArea()
            self.createCheckboxes(self.optionalsFrame, self.name, self.sections["Trainer"]["optionals"], self.optionalValues,
                self.settings["sections"].get("Trainer", {}).get("optionals"))
            self.updateSelectAllLabel()

        self.createFooter()
        

    # --------------------------------------------------
    # IMAGE PREVIEW
    # --------------------------------------------------
    def createImagePreview(self):

        # Main top component
        self.imageSection = tk.Frame(self.frame, bg = BACKGROUND_COLOR)
        self.imageSection.pack(fill = "both", padx = 15, pady = 15)
        self.imageSection.grid_columnconfigure(2, weight = 1)
        self.imageSection.grid_rowconfigure(0, weight = 1)
        imagesContainer = tk.Frame(self.imageSection, bg = BACKGROUND_COLOR)
        imagesContainer.grid(row = 0, column = 2, sticky = "nsew")
        imagesContainer.grid_rowconfigure(0, weight = 1)

        # One column per section
        for column, section in enumerate(self.sections):
            imagesContainer.grid_columnconfigure(column, weight = 1, uniform = "imageColumns")

            # Generated image preview
            imageArea = tk.Frame(imagesContainer, bg = BACKGROUND_COLOR, width = self.areaWidth, height = self.minImageHeight)
            imageArea.grid(row = 0, column = column, sticky = "nsew")
            imageArea.grid_propagate(False)
            imageLabel = tk.Label(imageArea, bg = BACKGROUND_COLOR)
            imageLabel.place(relx = 0.5, rely = 0.5, anchor = "center")

            self.imageAreas[section] = imageArea
            self.imageLabels[section] = imageLabel


    # Zoom in or out the image
    def scaleImage(self, image, section = None):
        scale = IMAGE_SCALES.get(section or self.defaultSection, 1)
        if (scale == 1):
            return image
        return image.resize((int(image.width * scale), int(image.height * scale)), Image.Resampling.NEAREST)


    # Display the current image at its native size
    def renderImage(self, section = None):
        section = section or self.defaultSection
        displayedImage = self.previewImage or self.outputImages.get(section)
        if not displayedImage:
            return

        image = displayedImage.convert("RGBA")
        self.previewPhotos[section] = ImageTk.PhotoImage(image)
        self.imageLabels[section].config(image = self.previewPhotos[section])
        self.imageAreas[section].config(width = max(IMAGE_AREA_WIDTH, image.width),
            height = max(IMAGE_AREA_HEIGHT, image.height))


    # Show provided image
    def updateImage(self, generatedImage, section = None):
        section = section or self.defaultSection
        self.outputImages[section] = self.scaleImage(generatedImage, section)

        # Override displayed image
        if self.previewImage is None:
             self.renderImage(section)

    def clearPreview(self):
        self.previewTrainer = None
        self.previewImage = None


    # --------------------------------------------------
    # TRAINER : IMAGE NAVIGATION
    # --------------------------------------------------
    def createTrainerNavigation(self):

        # Previous trainer arrow
        self.previousButton = tk.Label(self.imageSection, text = "❮", font = (FONT, 38), 
            bg = BACKGROUND_COLOR, fg = MUTED_COLOR, cursor = "hand2", width = 2)
        self.previousButton.grid(row = 0, column = 0)
        self.previousButton.bind("<Button-1>", lambda event: self.navigateImage(-1))
        self.previousButton.bind("<Enter>", lambda event: self.previousButton.config(fg = ACCENT_COLOR))
        self.previousButton.bind("<Leave>", lambda event: self.previousButton.config(fg = MUTED_COLOR))

        # Previous trainer sprite
        self.previousSpriteFrame = tk.Frame(self.imageSection, width = 80, height = 80, bg = BACKGROUND_COLOR)
        self.previousSpriteFrame.grid(row = 0, column = 1)
        self.previousSpriteFrame.grid_propagate(False)
        self.previousSprite = tk.Label(self.previousSpriteFrame, bg = BACKGROUND_COLOR, cursor = "hand2")
        self.previousSprite.place(relx = 0.5, rely = 0.5, anchor = "center")
        self.previousSprite.bind("<Button-1>", lambda event: self.navigateImage(-1))
        self.previousSprite.bind("<Enter>", lambda event: self.previousButton.config(fg = ACCENT_COLOR))
        self.previousSprite.bind("<Leave>", lambda event: self.previousButton.config(fg = MUTED_COLOR))

        # Next trainer arrow
        self.nextButton = tk.Label(self.imageSection, text = "❯", font = (FONT, 38), 
            bg = BACKGROUND_COLOR, fg = MUTED_COLOR, cursor = "hand2", width = 2)
        self.nextButton.grid(row = 0, column = 4)
        self.nextButton.bind("<Button-1>", lambda event: self.navigateImage(1))
        self.nextButton.bind("<Enter>", lambda event: self.nextButton.config(fg = ACCENT_COLOR))
        self.nextButton.bind("<Leave>", lambda event: self.nextButton.config(fg = MUTED_COLOR))

        # Next trainer sprite
        self.nextSpriteFrame = tk.Frame(self.imageSection, width = 80, height = 80, bg = BACKGROUND_COLOR)
        self.nextSpriteFrame.grid(row = 0, column = 3)
        self.nextSpriteFrame.grid_propagate(False)
        self.nextSprite = tk.Label(self.nextSpriteFrame, bg = BACKGROUND_COLOR, cursor = "hand2")
        self.nextSprite.place(relx = 0.5, rely = 0.5, anchor = "center")
        self.nextSprite.bind("<Button-1>", lambda event: self.navigateImage(1))
        self.nextSprite.bind("<Enter>", lambda event: self.nextButton.config(fg = ACCENT_COLOR))
        self.nextSprite.bind("<Leave>", lambda event: self.nextButton.config(fg = MUTED_COLOR))

        # Update sprites images
        self.updateSpritePreviews()


    # Previous/next trainer button helpers
    def unbindButton(self, button: tk.Label):
        button.unbind("<Button-1>")
        button.unbind("<Enter>")
        button.unbind("<Leave>")

    def disableButton(self, button: tk.Label):
        button.config(text = "", cursor = "")
        self.unbindButton(button)

    def disableSprite(self, sprite: tk.Label):
        sprite.config(image = "", cursor = "")
        self.unbindButton(sprite)

    def enableButton(self, button: tk.Label, previous):
        button.config(text = "❮" if previous else "❯", cursor = "hand2")
        button.bind("<Button-1>", lambda event: self.navigateImage(-1 if previous else 1))
        button.bind("<Enter>", lambda event: button.config(fg = ACCENT_COLOR))
        button.bind("<Leave>", lambda event: button.config(fg = MUTED_COLOR))

    def enableSprite(self, button: tk.Label, sprite: tk.Label, previous):
        sprite.config(cursor = "hand2")
        sprite.bind("<Button-1>", lambda event: self.navigateImage(-1 if previous else 1))
        sprite.bind("<Enter>", lambda event: button.config(fg = ACCENT_COLOR))
        sprite.bind("<Leave>", lambda event: button.config(fg = MUTED_COLOR))


    # Previous/Next trainer buttons
    def disableLeftArrow(self):
        self.disableButton(self.previousButton)
        self.disableSprite(self.previousSprite)

    def disableRightArrow(self):
        self.disableButton(self.nextButton)
        self.disableSprite(self.nextSprite)
        
    def enableLeftArrow(self):
        self.enableButton(self.previousButton, previous = True)
        self.enableSprite(self.previousButton, self.previousSprite, previous = True)

    def enableRightArrow(self):
        self.enableButton(self.nextButton, previous = False)
        self.enableSprite(self.nextButton, self.nextSprite, previous = False)


    def getDisplayedTrainer(self):
        return self.pinnedTrainer or self.liveTrainer

    def setTrainers(self, trainerList):
        self.trainerList = trainerList
        self.updateSpritePreviews()
        self.updateTrainerBar()


    # Called every tick with the trainer currently in the game
    def setLiveTrainer(self, trainer):
        if trainer == self.liveTrainer:
            return

        # Variable strictly set by emulator
        self.liveTrainer = trainer

        # Currently displaying the trainer, nothing to preview
        if self.previewTrainer == self.getDisplayedTrainer():
            self.clearPreview()

        self.renderImage()
        self.updateSpritePreviews()
        self.updateTrainerBar()

    # Triggered when clicking an arrow
    def navigateImage(self, direction):
        currentTrainer = self.previewTrainer or self.getDisplayedTrainer()
        newTrainer = None

        if not self.trainerList or not currentTrainer:
            return

        # First trainer or superboss, disable left arrow
        if (direction == -1 and currentTrainer.trainerId not in [-1,0]):
            newTrainer = self.trainerList[currentTrainer.trainerId - 1]

        # Last trainer or superboss, disable right arrow
        if (direction == 1 and currentTrainer.trainerId not in [-1, len(self.trainerList) - 1]):
            newTrainer = self.trainerList[currentTrainer.trainerId + 1]

        # Back on the live trainer : nothing to preview anymore
        self.previewTrainer = None if newTrainer == self.getDisplayedTrainer() else newTrainer
        self.refreshTrainerView()


    def refreshTrainerView(self):
        self.previewImage = None

        if self.previewTrainer and self.onPreviewRequested:
            self.previewImage = self.scaleImage(self.onPreviewRequested(self.previewTrainer))

        self.renderImage()
        self.updateSpritePreviews()
        self.updateTrainerBar()

    def pinPreviewedTrainer(self):
        self.pinnedTrainer = self.previewTrainer
        self.outputImages[self.name] = self.previewImage or self.outputImages[self.name]
        self.clearPreview()
        self.renderImage()
        self.updateTrainerBar()
        self.updateSpritePreviews()

        if self.onPinChanged:
            self.onPinChanged()

    def returnToCurrentTrainer(self):
        self.pinnedTrainer = None
        self.clearPreview()
        self.renderImage()
        self.updateTrainerBar()
        self.updateSpritePreviews()

        if self.onPinChanged:
            self.onPinChanged()

    def getTrainerSprite(self, spriteName):
        spritePath = TRAINERSPRITE_FOLDER / f"{spriteName}.png"

        if spritePath not in self.spritePhotoRefs:
            try:
                spriteImage = Image.open(spritePath).convert("RGBA")
                spriteImage.thumbnail((80, 80), Image.Resampling.LANCZOS)
                self.spritePhotoRefs[spritePath] = ImageTk.PhotoImage(spriteImage)
            except Exception as error:
                print(f"Could not load sprite {spritePath} : {error}")
                return None

        return self.spritePhotoRefs[spritePath]

    def updateSpritePreviews(self):
        currentTrainer = self.previewTrainer or self.getDisplayedTrainer()

        if not self.trainerList or not currentTrainer:
            return

        # First trainer or superboss, disable left arrow
        if (currentTrainer.trainerId in [-1,0]):
            self.disableLeftArrow()
        else:
            self.enableLeftArrow()
            previousTrainer = self.trainerList[currentTrainer.trainerId - 1]
            self.previousSprite.config(image = self.getTrainerSprite(previousTrainer.spriteName) or "")

        # Last trainer or superboss, disable right arrow
        if (currentTrainer.trainerId in [-1, len(self.trainerList) - 1]):
            self.disableRightArrow()
        else:
            self.enableRightArrow()
            nextTrainer = self.trainerList[currentTrainer.trainerId + 1]
            self.nextSprite.config(image = self.getTrainerSprite(nextTrainer.spriteName) or "")


    # --------------------------------------------------
    # TRAINER BAR (status + contextual buttons)
    # --------------------------------------------------
    def createTrainerBar(self):
        self.trainerBar = tk.Frame(self.frame, bg = BACKGROUND_COLOR, height = TRAINER_BAR_HEIGHT)
        self.trainerBar.pack(fill = "x", padx = 15)
        self.trainerBar.grid_propagate(False)  # fixed height
        self.trainerBar.grid_columnconfigure(0, weight = 1, uniform = "trainerBarSides")
        self.trainerBar.grid_columnconfigure(1, weight = 0)
        self.trainerBar.grid_columnconfigure(2, weight = 1, uniform = "trainerBarSides")
        self.trainerBar.grid_rowconfigure(0, weight = 1)

        # Left: search
        self.createTrainerSearch(self.trainerBar)

        # Center: status
        self.trainerStatus = tk.Label(self.trainerBar, text = "", font = (FONT, 10, "bold"),
            bg = BACKGROUND_COLOR, fg = MUTED_COLOR)
        self.trainerStatus.grid(row = 0, column = 1)

        # Right: contextual buttons
        self.buttonsFrame = tk.Frame(self.trainerBar, bg = BACKGROUND_COLOR)
        self.buttonsFrame.grid(row = 0, column = 2, sticky = "e")
        self.pinButton = self.createFlatButton(self.buttonsFrame, "📌 Show in output", self.pinPreviewedTrainer)
        self.returnButton = self.createFlatButton(self.buttonsFrame, "⮌  Current trainer", self.returnToCurrentTrainer)

        self.updateTrainerBar()


    # Triggered on any trainer change, display or hide trainer buttons
    def updateTrainerBar(self):
        text, color = "", BACKGROUND_COLOR

        # Display label depending on currently 
        if self.previewTrainer:
            text = f"Preview : {self.previewTrainer.getCompleteName()}"
            color = STATUS_CHECKING
        elif self.pinnedTrainer:
            text = f"● Pinned : {self.pinnedTrainer.getCompleteName()}"
            color = STATUS_RUNNING
        elif self.liveTrainer:
            text = f"● Live : {self.liveTrainer.getCompleteName()}"
            color = STATUS_RUNNING

        self.trainerStatus.config(text = text, fg = color)
        self.pinButton.pack_forget()
        self.returnButton.pack_forget()

        # Display pin and return to current trainer buttons
        if self.previewTrainer:
            self.pinButton.pack(side = "left", padx = (8, 0))
        if self.previewTrainer or self.pinnedTrainer:
            self.returnButton.pack(side = "left", padx = (8, 0))


    def createFlatButton(self, parent, text, command):
        button = tk.Label(parent, text = text, font = (FONT, 9), bg = BUTTON_COLOR, fg = MUTED_COLOR,
            cursor = "hand2", padx = 14, pady = 6)
        button.bind("<Button-1>", lambda event: command())
        button.bind("<Enter>", lambda event: button.config(bg = BUTTON_HOVER, fg = ACCENT_COLOR))
        button.bind("<Leave>", lambda event: button.config(bg = BUTTON_COLOR, fg = MUTED_COLOR))
        return button


    # Instead of trainer bar, we can use section titles bar
    def createSectionTitles(self):
        sectionBar = tk.Frame(self.frame, bg = BACKGROUND_COLOR, height = TRAINER_BAR_HEIGHT)
        sectionBar.pack(fill = "x", padx = 15)
        sectionBar.grid_propagate(False)
        sectionBar.grid_rowconfigure(0, weight = 1)

        for column, config in enumerate(self.sections.values()):
            sectionBar.grid_columnconfigure(column, weight = 1, uniform = "sectionColumns")
            tk.Label(sectionBar, text = f"Preview : {config["title"]}", font = (FONT, 11, "bold"),
                bg = BACKGROUND_COLOR, fg = TEXT_COLOR).grid(row = 0, column = column)


    # --------------------------------------------------
    # TRAINER SEARCH
    # --------------------------------------------------
    def createTrainerSearch(self, parent):
        self.searchBox = tk.Frame(parent, bg = BUTTON_COLOR, highlightthickness = 1, highlightbackground = "#343A43")
        self.searchBox.grid(row = 0, column = 0, sticky = "w")

        tk.Label(self.searchBox, text = "🔍", font = (FONT, 9), bg = BUTTON_COLOR, fg = MUTED_COLOR).pack(side = "left", padx = (8, 0))

        self.searchVariable = tk.StringVar()
        self.searchVariable.trace_add("write", self.onSearchChanged)
        self.searchEntry = tk.Entry(self.searchBox, textvariable = self.searchVariable, width = 22, font = (FONT, 10),
            bg = BUTTON_COLOR, fg = TEXT_COLOR, insertbackground = TEXT_COLOR, relief = "flat", highlightthickness = 0)
        self.searchEntry.pack(side = "left", padx = (6, 8), ipady = 4)

        # Dropdown with the matches, created on the page so it can overlap the options below
        self.searchMatches = []
        self.suggestionFont = font.Font(family = FONT, size = 10)
        self.suggestions = tk.Listbox(self.frame, font = self.suggestionFont, bg = BUTTON_COLOR, fg = "#E5E7EB",
            selectbackground = HOVER_COLOR, selectforeground = ACCENT_HOVER, activestyle = "none", cursor = "hand2",
            relief = "flat", highlightthickness = 1, highlightbackground = "#343A43", exportselection = False)

        # Search logic : keyboard management, highlight on focus in and out
        self.suggestions.bind("<Button-1>", self.onSuggestionClicked)
        self.suggestions.bind("<Motion>", self.onSuggestionHover)
        self.searchEntry.bind("<FocusIn>", lambda event: self.searchBox.config(highlightbackground = ACCENT_COLOR))
        self.searchEntry.bind("<FocusOut>", self.onSearchFocusOut)
        self.searchEntry.bind("<Return>", lambda event: self.chooseSuggestion(self.suggestions.curselection()[0] if self.suggestions.curselection() else 0))
        self.searchEntry.bind("<Down>", lambda event: self.moveSuggestion(1))
        self.searchEntry.bind("<Up>", lambda event: self.moveSuggestion(-1))
        self.searchEntry.bind("<Escape>", lambda event: self.closeSearch())


    # Triggered when text added in search box
    def onSearchChanged(self, *args):
        searchedText = self.searchVariable.get().strip().lower().split(" ") if self.searchVariable.get() else []
        self.searchMatches = [
            trainer for trainer in self.trainerList
            if all(word in (trainer.name + " " + trainer.zone + " " + (trainer.doublePartner.name if trainer.doublePartner else "")).lower()
                   for word in searchedText)
        ][:8] if searchedText else []

        # No match
        if not self.searchMatches:
            self.suggestions.place_forget()
            return

        self.suggestions.delete(0, "end")
        for trainer in self.searchMatches:
            self.suggestions.insert("end", " " + trainer.getCompleteName() + " (" + trainer.zone + ")")

        self.suggestions.config(height = len(self.searchMatches))
        self.suggestions.selection_set(0)

        # Place the dropdown right under the search box
        x = self.searchBox.winfo_rootx() - self.frame.winfo_rootx()
        y = self.searchBox.winfo_rooty() - self.frame.winfo_rooty() + self.searchBox.winfo_height()

        # Fit the longest line, within a minimum width and the available space on the right
        longest = max(self.suggestionFont.measure(trainer.getCompleteName() + trainer.zone) for trainer in self.searchMatches) + 30
        maxWidth = self.frame.winfo_width() - x - 15
        width = max(self.searchBox.winfo_width(), SUGGESTION_MIN_WIDTH, min(longest, maxWidth))

        self.suggestions.place(x = x, y = y, width = width)
        self.suggestions.lift()


    # Triggered when pressing up/down key on search suggestions
    def moveSuggestion(self, direction):
        if not self.searchMatches:
            return

        selection = self.suggestions.curselection()
        index = (selection[0] if selection else 0) + direction
        index = max(0, min(len(self.searchMatches) - 1, index))

        self.suggestions.selection_clear(0, "end")
        self.suggestions.selection_set(index)

    # Triggered when search suggestion is clicked
    def onSuggestionClicked(self, event):
        index = self.suggestions.nearest(event.y)
        self.chooseSuggestion(index)
        return "break"

    # Triggered when suggestion is picked, by pressing Enter or clicking
    def chooseSuggestion(self, index):
        if not self.searchMatches or index >= len(self.searchMatches):
            return

        trainer = self.searchMatches[index]

        # Same behavior as the arrows: selecting the output trainer means nothing to preview
        self.previewTrainer = None if trainer == self.getDisplayedTrainer() else trainer
        self.refreshTrainerView()
        self.closeSearch()

    # Triggered when the mouse moves over the suggestions
    def onSuggestionHover(self, event):
        index = self.suggestions.nearest(event.y)

        if index not in self.suggestions.curselection():
            self.suggestions.selection_clear(0, "end")
            self.suggestions.selection_set(index)

    # Triggered when search suggestions are closed
    def closeSearch(self):
        self.searchVariable.set("")
        self.suggestions.place_forget()
        self.frame.focus_set()

    # Highlight suggestion 
    def onSearchFocusOut(self, event):
        self.searchBox.config(highlightbackground = "#343A43")
        self.frame.after(200, self.suggestions.place_forget)


    # --------------------------------------------------
    # TOGGLEABLE OPTIONS HEADER
    # --------------------------------------------------
    def createOptionsHeader(self):
        self.optionalsVisible = False

        # Main component
        headerFrame = tk.Frame(self.optionsSection, bg = SECTION_COLOR, cursor = "hand2")
        headerFrame.pack(fill = "x", padx = 18, pady = (15, 0))

        self.toggleArrow = tk.Label(headerFrame, text = "▸", font = (FONT, 16, "bold"),
            bg = SECTION_COLOR, fg = TEXT_COLOR, cursor = "hand2")
        self.toggleArrow.pack(side = "left", padx = (0, 10))

        self.titleLabel = tk.Label(headerFrame, text = "Display Optional Trainers", font = (FONT, 12, "bold"),
            bg = SECTION_COLOR, fg = TEXT_COLOR, cursor = "hand2")
        self.titleLabel.pack(side = "left")

        # Select all / Deselect all, aligned to the right
        self.selectAllLabel = tk.Label(headerFrame, text = "Select all", font = (FONT, 11),
            bg = SECTION_COLOR, fg = MUTED_COLOR, cursor = "hand2")
        self.selectAllLabel.pack(side = "left", padx = (15,0), pady = (2,0))
        self.selectAllLabel.bind("<Button-1>", lambda event: self.toggleAllOptionals())
        self.selectAllLabel.bind("<Enter>", lambda event: self.selectAllLabel.config(fg = ACCENT_COLOR))
        self.selectAllLabel.bind("<Leave>", lambda event: self.selectAllLabel.config(fg = MUTED_COLOR))

        # Make the entire header clickable
        for widget in (headerFrame, self.toggleArrow, self.titleLabel):
            widget.bind("<Button-1>", lambda event: self.toggleOptionals())


    # --------------------------------------------------
    # OPTIONAL ZONES SCROLL AREA
    # --------------------------------------------------
    def createOptionalsScrollArea(self):

        style = ttk.Style.get_instance()
        style.configure("Dark.Vertical.TScrollbar", background = "#4A515C",
            troughcolor = SECTION_COLOR, bordercolor = SECTION_COLOR, lightcolor = "#4A515C",
            darkcolor = "#4A515C", arrowcolor = MUTED_COLOR, gripcount = 0, relief = "flat")
        style.map("Dark.Vertical.TScrollbar",
            background = [("active", ACCENT_COLOR), ("pressed", ACCENT_HOVER)],
            lightcolor = [("active", ACCENT_COLOR), ("pressed", ACCENT_HOVER)],
            darkcolor = [("active", ACCENT_COLOR), ("pressed", ACCENT_HOVER)])

        # Main container
        self.optionalsScrollContainer = tk.Frame(self.optionsSection, bg = SECTION_COLOR)

        # Scrollable canvas
        self.optionalsCanvas = tk.Canvas(self.optionalsScrollContainer,
            bg = SECTION_COLOR, highlightthickness = 0, borderwidth = 0)

        self.optionalsScrollbar = ttk.Scrollbar(self.optionalsScrollContainer, orient = "vertical",
            command = self.optionalsCanvas.yview, style = "Dark.Vertical.TScrollbar")
        self.optionalsCanvas.configure(yscrollcommand = self.optionalsScrollbar.set)
        self.optionalsCanvas.pack(side = "left", fill = "both", expand = True)

        # Frame containing the actual checkboxes
        self.optionalsFrame = tk.Frame(self.optionalsCanvas, bg = SECTION_COLOR)
        self.optionalsFrame.bind("<Configure>", self.updateOptionalScrollRegion)
        
        self.optionalsWindow = self.optionalsCanvas.create_window((0, 0),
            window = self.optionalsFrame, anchor = "nw")
        
        # Keep inner frame width synchronized with canvas
        self.optionalsCanvas.bind("<Configure>",
            lambda event: self.optionalsCanvas.itemconfigure(self.optionalsWindow, width = event.width))

        # Mouse wheel scrolling
        self.optionalsCanvas.bind("<Enter>", self.bindOptionalMouseWheel)
        self.optionalsCanvas.bind("<Leave>", self.unbindOptionalMouseWheel)


    def updateOptionalScrollRegion(self, event = None):
        self.optionalsCanvas.configure(
            scrollregion = self.optionalsCanvas.bbox("all")
        )

        contentHeight = self.optionalsFrame.winfo_reqheight()
        visibleHeight = self.optionalsCanvas.winfo_height()

        if contentHeight > visibleHeight:
            if not self.optionalsScrollbar.winfo_manager():
                self.optionalsScrollbar.pack(side = "right", fill = "y")
        else:
            self.optionalsScrollbar.pack_forget()

    def bindOptionalMouseWheel(self, event = None):
        self.optionalsCanvas.bind_all("<MouseWheel>", self.onOptionalMouseWheel)

    def unbindOptionalMouseWheel(self, event = None):
        self.optionalsCanvas.unbind_all("<MouseWheel>")

    def onOptionalMouseWheel(self, event):
        self.optionalsCanvas.yview_scroll(int(-event.delta / 120), "units")


    # --------------------------------------------------
    # CHECKBOXES
    # --------------------------------------------------
    def createSectionOptions(self):
        for section, config in self.sections.items():

            # Title above each block
            tk.Label(self.optionsSection, text = f"{config["title"]} Settings", font = (FONT, 12, "bold"),
                bg = SECTION_COLOR, fg = TEXT_COLOR).pack(anchor = "w", padx = 24, pady = (15, 0))

            frame = tk.Frame(self.optionsSection, bg = SECTION_COLOR)
            frame.pack(fill = "x", padx = 24, pady = (12, 0))
            self.sectionFrames[section] = frame

            self.createCheckboxes(frame, section, config["checkboxes"], self.checkboxValues[section],
                self.settings["sections"].get(section, {}).get("checkboxes"))
            self.createTextboxes(section)
            self.applyRules(section)


    def createCheckboxes(self, parent, section, options, variables, settings = {}):

        # Setup style for all checkboxes
        style = ttk.Style.get_instance()
        style.configure("TCheckbutton", font = (FONT, 10), background = SECTION_COLOR, foreground = "#E5E7EB", padding = (6, 6))
        style.map("TCheckbutton", background = [("active", HOVER_COLOR), ("!active", SECTION_COLOR)],
            foreground = [("active", ACCENT_HOVER), ("!active", "#E5E7EB")])

        # Setup 4 checkboxes per line
        for column in range(OPTIONS_PER_ROW):
            parent.grid_columnconfigure(column, weight = 1, uniform = "optionColumns")

        # Display all options in checkboxes
        for index, (option, defaultValue) in enumerate(options.items()):
            row = index // OPTIONS_PER_ROW
            column = index % OPTIONS_PER_ROW

            optionValue = tk.BooleanVar(value = settings.get(option, defaultValue))
            checkbox = ttk.Checkbutton(parent, text = option, variable = optionValue,
                style = "TCheckbutton", cursor = "hand2", command = lambda: self.onCheckboxChanged(section))
            checkbox.grid(row = row, column = column, sticky = "w", padx = (0, 8), pady = 4)
            variables[option] = optionValue


    # Apply texbox enable/disable rules in a section
    def applyRules(self, section):
        rules = self.sections.get(section, {}).get("rules", {})
        optionValues = self.checkboxValues.get(section, {})

        # A textbox is only editable while its checkbox is ticked
        for checkbox, textboxes in rules.get("enables", {}).items():
            enabled = optionValues[checkbox].get()

            for name in textboxes:
                label, entry = self.textboxWidgets[section][name]

                if enabled:
                    entry.config(state = "normal", cursor = "xterm")
                    label.config(fg = "#E5E7EB", cursor = "")
                else:
                    entry.config(state = "disabled", cursor = "no")
                    label.config(fg = "#5C626C", cursor = "no")


    # Tick all optional checkboxes
    def toggleAllOptionals(self):
        allChecked = all(variable.get() for variable in self.optionalValues.values())

        for variable in self.optionalValues.values():
            variable.set(not allChecked)

        self.updateSelectAllLabel()
        self.onCheckboxChanged()

    def updateSelectAllLabel(self):
        if not self.optionalValues:
            return

        allChecked = all(variable.get() for variable in self.optionalValues.values())
        self.selectAllLabel.config(text = "Deselect all" if allChecked else "Select all")


    # Called whenever a checkbox is ticked
    def onCheckboxChanged(self, section = None):
        section = section or self.defaultSection

        # Apply textbox disable/enable rules, then apply value changed logic
        self.applyRules(section)
        self.onValueChanged(section)

        if self.name == "Trainer":
            self.updateSelectAllLabel()

            if self.previewTrainer:
                self.refreshTrainerView()

        


    # --------------------------------------------------
    # TEXTBOXES (Label + Field)
    # --------------------------------------------------
    def createTextboxes(self, section):
        config = self.sections[section]
        if not config["textboxes"]:
            return

        # Add textboxes after checkboxes
        textboxesFrame = self.sectionFrames[section]
        validate = (self.frame.register(self.isValidNumber), "%P")

        for index, (name, defaultValue) in enumerate(config["textboxes"].items()):
            position = len(config["checkboxes"]) + index
            row = position // OPTIONS_PER_ROW
            column = position % OPTIONS_PER_ROW

            textboxesCell = tk.Frame(textboxesFrame, bg = SECTION_COLOR)
            textboxesCell.grid(row = row, column = column, sticky = "w", padx = (0, 8), pady = 4)

            textboxesLabel = tk.Label(textboxesCell, text = name, font = (FONT, 10),
                bg = SECTION_COLOR, fg = "#E5E7EB", padx = 6, pady = 6)
            textboxesLabel.pack(side = "left")

            savedValues = self.settings["sections"].get(section, {}).get("textboxes", {})
            value = tk.StringVar(value = str(savedValues.get(name, defaultValue)))
            value.trace_add("write", lambda *args: self.onValueChanged(section))

            entry = tk.Entry(textboxesCell, textvariable = value, width = 4, justify = "center",
                font = (FONT, 10), bg = BUTTON_COLOR, fg = TEXT_COLOR, insertbackground = TEXT_COLOR,
                disabledbackground = BUTTON_COLOR, disabledforeground = "#5C626C",
                relief = "flat", highlightthickness = 1, highlightbackground = "#343A43",
                highlightcolor = ACCENT_COLOR, validate = "key", validatecommand = validate)
            entry.pack(side = "left", ipady = 3)

            # Save each text box to enable/disable them if linked checkbox is unticked
            self.textboxesValues[section][name] = value
            self.textboxWidgets[section][name] = (textboxesLabel, entry)

    def isValidNumber(self, newText):
        return newText == "" or newText.isdigit()

    def onValueChanged(self, section):
        if self.onChange: self.onChange(section)

    def getTextboxesValues(self, section = None):
        section = section or self.defaultSection
        values = {}

        for name, variable in self.textboxesValues[section].items():
            text = variable.get()
            values[name] = int(text) if text else self.sections[section]["textboxes"][name]

        return values

    def getPageSettings(self):
        return {
            "sections": {
                section: {
                    "checkboxes": {option: variable.get() for option, variable in self.checkboxValues[section].items()},
                    "optionals": {option: variable.get() for option, variable in self.optionalValues.items()} if section == "Trainer" else {},
                    "textboxes": self.getTextboxesValues(section)
                }
                for section in self.sections
            }
        }


    # --------------------------------------------------
    # COLLAPSIBLE OPTIONAL ZONES
    # --------------------------------------------------
    def toggleOptionals(self):
        self.optionalsVisible = not self.optionalsVisible

        if self.optionalsVisible:
            self.optionalsScrollContainer.pack(fill = "both", expand = True, padx = 24, pady = (12, 0))
            self.toggleArrow.config(text = "▾")
            self.updateOptionalScrollRegion()
        else:
            self.optionalsScrollContainer.pack_forget()
            self.toggleArrow.config(text = "▸")


    # --------------------------------------------------
    # FOOTER
    # --------------------------------------------------
    def createFooter(self):
        self.footerFrame = tk.Frame(self.optionsSection, bg = SECTION_COLOR)
        self.footerFrame.pack(fill = "x", side = "bottom", padx = 18)
        ttk.Separator(self.footerFrame, bootstyle = "secondary").pack(fill = "x", pady = (12, 10))

        footerRow = tk.Frame(self.footerFrame, bg = SECTION_COLOR)
        footerRow.pack(fill = "x", pady = (0, 12))

        self.footerLabel = tk.Label(footerRow, text = "Script currently running... Your changes are automatically saved.",
            font = (FONT, 9), bg = SECTION_COLOR, fg = MUTED_COLOR)
        self.footerLabel.pack(side = "left")

        self.openFolderButton = tk.Label(footerRow, text = "📂 Open Output Folder", font = (FONT, 9),
            bg = BUTTON_COLOR, fg = MUTED_COLOR, cursor = "hand2", padx = 14, pady = 6)
        self.openFolderButton.pack(side = "right")
        self.openFolderButton.bind("<Button-1>", lambda event: self.openOutputFolder())
        self.openFolderButton.bind("<Enter>", lambda event: self.openFolderButton.config(bg = BUTTON_HOVER, fg = ACCENT_COLOR))
        self.openFolderButton.bind("<Leave>", lambda event: self.openFolderButton.config(bg = BUTTON_COLOR, fg = MUTED_COLOR))

    def openOutputFolder(self):
        try:
            os.startfile(OUTPUT_FOLDER)
        except Exception as error:
            print(f"Could not open output folder: {error}")