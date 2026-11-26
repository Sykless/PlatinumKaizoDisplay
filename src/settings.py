import json
from copy import deepcopy

import file
from file import SETTINGS_FILE

SHOW_HELD_ITEMS = "Show Held Items"
SHOW_BACKGROUND = "Show Background"
SHOW_MULTIPLE_BOXES = "Show Multiple Boxes"
DISPLAY_TIME = "Display Time (s)"
COLUMNS = "Columns"
ROWS = "Rows"

TRAINER = "Trainer"
BOXES = "Boxes"
BOX = "Box"
DEAD = "Dead"
PARTY = "Party"

DEFAULT_SETTINGS = {
    TRAINER: {
        "checkboxes": {SHOW_HELD_ITEMS: True, SHOW_BACKGROUND: True},
        "optionals": {
            "Route 206": False, "Hearthome Gym": False, "Route 209": False, "Route 210 South": False,
            "Café": False, "Route 215": False, "Route 213": False, "Clamberclaw Cliffs": False,
            "Snowpoint Gym": False, "Route 222": False, "Oreburgh Gate": False, "Route 217": False,
            "Fuego Ironworks": False, "Route 216": False, "Route 212": False, "Route 220": False,
            "Route 221": False, "Wayward Cave": False, "Veilstone Warehouse": False, "Galactic HQ": False,
            "Mount Coronet - Room 1": False, "Coronet Highlands - Outside 1": False, "Route 223": False, "Pokémon League": False}
    },
    BOXES: {
        "sections": {
            BOX: {
                "title": "Available Pokémon",
                "checkboxes": {SHOW_HELD_ITEMS: True, SHOW_BACKGROUND: False, SHOW_MULTIPLE_BOXES: False},
                "textboxes": {DISPLAY_TIME: 5}
            },
            DEAD: {
                "title": "Dead Pokémon", 
                "checkboxes": {SHOW_BACKGROUND: False},
                "textboxes": {COLUMNS: 6, ROWS: 5}
            }
        }
    },
    PARTY: {
        "checkboxes": {SHOW_HELD_ITEMS: True, "Show Status": True, "Show HP": True}
    },
    "Logs": {}
}


# --------------------------------------------------
# Settings class
# --------------------------------------------------
class Settings:
    def __init__(self):
        self.defaultSettings = self.loadDefaultSettings()
        self.currentSettings = self.defaultSettings
        self.loadSettings()


    # Build default settings if starting from scratch
    def loadDefaultSettings(self):
        defaultSettings = {}

        for pageName, config in DEFAULT_SETTINGS.items():

            # Retrieve each section or init a single one
            pageSections = config.get("sections") or {
                pageName: {
                    "checkboxes": config.get("checkboxes", {}),
                    "optionals": config.get("optionals", {}),
                    "textboxes": config.get("textboxes", {})
                }
            }

            # Build default settings
            defaultSettings[pageName] = {
                "sections": {
                    sectionName: {
                        "checkboxes": dict(section.get("checkboxes", {})),
                        "optionals": dict(section.get("optionals", {})),
                        "textboxes": dict(section.get("textboxes", {}))
                    }
                    for sectionName, section in pageSections.items()
                }
            }

        return defaultSettings


    # Load currently saved settings
    def loadSettings(self):

        # Settings file does not exist : create the file with default values
        if not SETTINGS_FILE.exists():
            self.currentSettings = self.resetToDefaults()

        # Try to retrieve settings from file
        try:
            savedSettings = json.loads(file.safeReadFile(SETTINGS_FILE))
        except (TypeError, json.JSONDecodeError) as error:
            print(f"Could not read {SETTINGS_FILE.name}, using defaults : {error}")
            self.currentSettings = self.resetToDefaults()

        # Merge saved values into defaults : new options get their default value, removed ones are dropped
        mergedData = self.mergeSettings(self.defaultSettings, savedSettings)

        # Rewrite the file if the structure changed (new/removed options)
        if mergedData != savedSettings:
            self.saveSettings(mergedData)

        self.currentSettings = mergedData


    # Save provided settings in settings.json file
    def saveSettings(self, settings):
        jsonSettings = json.dumps(settings, indent = 4, ensure_ascii = False)
        file.safeWriteTextFile(jsonSettings, file.SETTINGS_FILE)


    # Override current settings with default values
    def resetToDefaults(self):
        defaultSettings = deepcopy(self.defaultSettings)
        self.saveSettings(defaultSettings)
        return defaultSettings


    # Recursively keep the defaults structure, but use saved values when they have the same type
    def mergeSettings(self, defaultValue, savedValue):

        # Provided a dict, call self with each setting
        if (isinstance(defaultValue, dict)):
            savedValue = savedValue if isinstance(savedValue, dict) else {}

            return {key: self.mergeSettings(value, savedValue[key]) if key in savedValue else deepcopy(value)
                for key, value in defaultValue.items()}

        # Provided a value, merge if same type
        else:
            if isinstance(defaultValue, bool) and isinstance(savedValue, bool):
                return savedValue
            elif isinstance(defaultValue, int) and isinstance(savedValue, int):
                return savedValue
            elif isinstance(savedValue, type(defaultValue)):
                return savedValue
            else:
                return defaultValue


    # Retrieve page settings
    def getPageSettings(self, pageName):
        return self.currentSettings.get(pageName, {"sections": {}})


    # Replace page settings with provided ones
    def updatePageSettings(self, pageName, newValues):
        if pageName not in self.defaultSettings:
            return

        self.currentSettings[pageName] = self.mergeSettings(self.defaultSettings[pageName], newValues)
        self.saveSettings(self.currentSettings)


    # Global accesser + option-specific methods
    def getOption(self, section, option):
        pageName = BOXES if section in [BOX, DEAD] else section

        for optionType, optionsDict in self.currentSettings[pageName]["sections"][section].items():
            for optionName, optionValue in optionsDict.items():
                if (optionName == option):
                    return optionValue

    def isPartyItemSpriteDisplayed(self):
        return self.getOption(TRAINER, SHOW_HELD_ITEMS)

    def isBoxItemSpriteDisplayed(self):
        return self.getOption(BOX, SHOW_HELD_ITEMS)

    def isTrainerItemSpriteDisplayed(self):
        return self.getOption(TRAINER, SHOW_HELD_ITEMS)

    def isBoxBackgroundDisplayed(self):
        return self.getOption(BOX, SHOW_BACKGROUND)

    def isDeadBackgroundDisplayed(self):
        return self.getOption(DEAD, SHOW_BACKGROUND)

    def isTrainerBackgroundDisplayed(self):
        return self.getOption(TRAINER, SHOW_BACKGROUND)

    def isDisplayMultipleBoxes(self):
        return self.getOption(BOX, SHOW_MULTIPLE_BOXES)

    def getBoxDisplayTime(self):
        displayTime = self.getOption(BOX, DISPLAY_TIME)
        return displayTime if displayTime > 0 else 5

    def deadBoxSize(self):
        columnNumber, rowNumber = self.getOption(DEAD, COLUMNS), self.getOption(DEAD, ROWS)
        return (columnNumber, rowNumber) if columnNumber * rowNumber else (6,5)


# Global settings object, updated by interface and read by image generator
SETTINGS = Settings()