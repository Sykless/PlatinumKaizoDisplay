import file

class Conf:
    @property
    def conf(self):
        return file.readConfFile()

CONFIGURATION = Conf()
DISPLAY_SPRITE_ITEMS = "DISPLAY_SPRITE_ITEMS"
DISPLAY_TRAINER_ITEMS = "DISPLAY_TRAINER_ITEMS"
DISPLAY_TRAINER_BACKGROUND = "DISPLAY_TRAINER_BACKGROUND"
DISPLAY_MULTIPLE_BOXES = "DISPLAY_MULTIPLE_BOXES"
BOX_DISPLAY_TIME = "BOX_DISPLAY_TIME"
DEAD_BOX_SIZE = "DEAD_BOX_SIZE"
ZONE_START_RUN_TRACKING = "ZONE_START_RUN_TRACKING"
LANG = "LANG"

def getLang():
    return CONFIGURATION.conf[LANG] if CONFIGURATION.conf[LANG] in ["EN","FR"] else "EN"

def isItemSpriteDisplayed():
    return CONFIGURATION.conf[DISPLAY_SPRITE_ITEMS] != "N"

def isTrainerItemSpriteDisplayed():
    return CONFIGURATION.conf[DISPLAY_TRAINER_ITEMS] != "N"

def isTrainerBackgroundDisplayed():
    return CONFIGURATION.conf[DISPLAY_TRAINER_BACKGROUND] != "N"

def isDisplayMultipleBoxes():
    return CONFIGURATION.conf[DISPLAY_MULTIPLE_BOXES] != "N"

def getBoxDisplayTime():
    displayTime = CONFIGURATION.conf[BOX_DISPLAY_TIME]

    # Default 5, take user value if number above 0
    if isinstance(displayTime, int) and displayTime > 0:
        return displayTime
    else:
        return 5

def deadBoxSize():
    boxSize = CONFIGURATION.conf[DEAD_BOX_SIZE]

    # Default 6x5, take user value if correctly formatted
    if ("X" in boxSize.upper()):
        columnNumber, rowNumber = boxSize.upper().split("X")
        return (int(columnNumber), int(rowNumber)) if columnNumber.isnumeric() and rowNumber.isnumeric() else (6,5)
    else:
        return (6,5)