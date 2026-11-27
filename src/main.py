import traceback

import file
import parse
import party
import trainer
from settings import SETTINGS, DEFAULT_SETTINGS, PARTY, BOX, DEAD, TRAINER
from interface import MainInterface, LUA_CHECKING, LUA_RUNNING, LUA_STOPPED

class PlatinumKaizoDisplay:
    def __init__(self):
        self.frames = 0
        self.starter = 0
        self.boxLine, self.deadLine, self.partyLine,  = [], [], []
        self.defeatedTrainers, self.trainerParty, self.doubleTrainerParty = [], [], []
        
        self.clock = 0
        self.boxNumber = 0
        self.luaStopped = 0
        self.currentTrainer = None

        self.interface = MainInterface(pages = DEFAULT_SETTINGS, settings = SETTINGS.currentSettings)
        self.interface.onTrainerPreview = trainer.generateTrainerCard
        self.interface.handleOptionsChanged = self.refreshImage
        self.interface.onSettingsChanged = self.quickRefresh
        self.interface.setLuaStatus(LUA_CHECKING)
        file.onImageReady = self.interface.updatePageImage


    # Call main loop
    def run(self):
        self.interface.root.after(0, self.mainLoop)
        self.interface.run()

    # Main loop, handles exception and self-call infinite loop
    def mainLoop(self):
        try:
            self.updateImages()

        # Show errors in Logs page and continue
        except Exception:
            print("An error occurred :")
            traceback.print_exc()
            print("\n")

        # Self-call itself every second
        finally:
            self.interface.root.after(1000, self.mainLoop)


    # Read emulator data and updates images
    def updateImages(self):
        
        # Read emulator data from Lua script
        dataRead = self.readEmulatorData()

        # Create png images from parsed data
        if (dataRead):
            self.lastValidData = dataRead

            # Refresh settings
            SETTINGS.loadSettings()

            # Generate party, box, dead and trainer images
            self.refreshImage(PARTY)
            self.refreshImage(BOX)
            self.refreshImage(DEAD)
            self.refreshImage(TRAINER)

        self.clock += 1


    # Refresh settings and generate an image on the fly
    def quickRefresh(self, pageName, image, newValues):
        SETTINGS.updatePageSettings(pageName, newValues)
        SETTINGS.loadSettings()
        self.refreshImage(image)


    # Generates image based on argument
    def refreshImage(self, image):
        if (image == TRAINER):
            self.refreshTrainerImage()
        if (image == PARTY):
            party.generatePlayerPartyImage(PARTY, self.partyLine, 6, 1)
        if (image == BOX):
            party.generatePlayerPartyImage(BOX, self.boxLine, 6, 5)
        if (image == DEAD):
            columnNumber, rowNumber = SETTINGS.deadBoxSize()
            party.generatePlayerPartyImage(DEAD, self.deadLine, columnNumber, rowNumber, customSize = True)


    # Display trainer image from retrieved emulator data
    def refreshTrainerImage(self):
        trainerOutputImage = None

        # Refresh trainer list from emulator data
        currentPathTrainerId = trainer.refreshTrainerList(self.starter, self.defeatedTrainers)
        self.trainerList = trainer.getTrainerList()

        # Find the trainer we're currently battling
        inBattle, self.currentTrainer = trainer.findTrainerFromTeam(self.currentTrainer, self.trainerParty, self.doubleTrainerParty)

        # In battle, generate trainer card from currently battled trainer
        if (inBattle):
            self.nextTrainer = self.currentTrainer
            trainerOutputImage = trainer.generateTrainerCard(self.currentTrainer, self.trainerParty, self.doubleTrainerParty)

        # Not in battle, find next trainer to battle from emulator data
        else:
            self.nextTrainer = trainer.getNextTrainer(currentPathTrainerId)
            pinnedTrainer = self.interface.getPinnedTrainer()

            # Pinned trainer, override next trainer
            if (pinnedTrainer and pinnedTrainer != self.nextTrainer):
                trainerOutputImage = trainer.generateTrainerCard(pinnedTrainer)

            # Generate trainer image only if different than current trainer team with dead team
            elif (self.nextTrainer != self.currentTrainer or not self.currentTrainer.deadTeam):
                trainerOutputImage = trainer.generateTrainerCard(self.nextTrainer)

        # Save trainer image in output folder
        if (trainerOutputImage):
            file.safeWriteFile(trainerOutputImage, TRAINER)

        self.interface.setTrainers(trainer.getTrainerList())
        self.interface.setLiveTrainer(self.nextTrainer)


    # Retrieve data written by Lua scipt
    def readEmulatorData(self):      
        emulatorData = file.readPokemonData()

        if emulatorData:
            lines = emulatorData.splitlines()

            # Retrieve conf file content to check user preferences
            displayMultipleBoxes = SETTINGS.isDisplayMultipleBoxes()
            boxDisplayTime = SETTINGS.getBoxDisplayTime()

            # Retrieve each line and parse its data
            for line in lines:
                if line.startswith("FRAMES"):
                    currentFrames = int(parse.parseLine(line)[0])

                    # Set Lua Status in interface
                    if self.frames:
                        framesDifference = currentFrames - self.frames
                        
                        if (framesDifference):
                            self.luaStopped = 0
                            self.interface.setLuaStatus(LUA_RUNNING)
                        else:
                            self.luaStopped += 1
                            if (self.luaStopped >= 3):
                                self.interface.setLuaStatus(LUA_STOPPED)

                    self.frames = currentFrames

                if line.startswith("STARTER"):
                    self.starter = int(parse.parseLine(line)[0])

                if line.startswith("BOX"):
                    fullBox = parse.parseLine(line)
                    numberOfBoxes = int(len(fullBox) / 30) if fullBox else 1

                    # 5th second : display next box
                    if (self.clock % boxDisplayTime == boxDisplayTime - 1):
                        self.boxNumber = (self.boxNumber + 1) % numberOfBoxes if displayMultipleBoxes else 0

                    # Take the 30 Pokémon from the provided box
                    self.boxLine = fullBox[30 * self.boxNumber : 30 * (self.boxNumber + 1)]
                    
                elif line.startswith("DEAD"):
                    self.deadLine = parse.parseLine(line)

                elif line.startswith("PARTY"):
                    self.partyLine = parse.parseLine(line)

                elif line.startswith("TRAINERPARTY"):
                    self.trainerParty = parse.parseLine(line)

                elif line.startswith("DOUBLETRAINERPARTY"):
                    self.doubleTrainerParty = parse.parseLine(line)

                elif line.startswith("TRAINERS"):
                    self.defeatedTrainers = parse.parseLine(line)

        return emulatorData


# Start script
if __name__ == "__main__":
    file.ensureSetup()

    try:
        app = PlatinumKaizoDisplay()
        app.run()
        
    # Don't stop script if an error occurs, just print it in the logs
    except Exception as e:
        print("An error occurred : ", e)