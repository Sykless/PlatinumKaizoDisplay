import time

import conf
import file
import parse
import party

PARTY_LABEL = "party"
BOX_LABEL = "box"
DEAD_LABEL = "dead"

# Main loop
def mainLoop():
    boxClock = 0 # Alternate between every box every 5 seconds
    boxNumber = 0 # Track which box we're currently displaying
    boxDisplayTime = 5 # Default : 5 seconds
    
    while True:
        try:
            # Check file every second
            time.sleep(1)

            # Retrieve data written by lua scipt
            emulatorData = file.readPokemonData()

            if emulatorData:
                lines = emulatorData.splitlines()

                # Retrieve conf file content to check user preferences
                displayMultipleBoxes = conf.isDisplayMultipleBoxes()
                boxDisplayTime = conf.getBoxDisplayTime()
                columnNumber, rowNumber = conf.deadBoxSize()

                # Retrieve each line and parse its data
                for line in lines:
                    if line.startswith("BOX"):
                        fullBox = parse.parseLine(line)
                        numberOfBoxes = int(len(fullBox) / 30) if fullBox else 1

                        # 5th second : display next box
                        if (boxClock == boxDisplayTime - 1):
                            boxNumber = (boxNumber + 1) % numberOfBoxes if displayMultipleBoxes else 0

                        # Take the 30 Pokémon from the provided box
                        boxLine = fullBox[30*boxNumber : 30*(boxNumber + 1)]
                        
                    elif line.startswith("DEAD"):
                        deadLine = parse.parseLine(line)

                    elif line.startswith("PARTY"):
                        partyLine = parse.parseLine(line)

                # Create png images from parsed data
                party.generatePlayerPartyImage(PARTY_LABEL, partyLine, 6, 1)
                party.generatePlayerPartyImage(BOX_LABEL, boxLine, 6, 5)
                party.generatePlayerPartyImage(DEAD_LABEL, deadLine, columnNumber, rowNumber, customSize = True)

            # Every 5 seconds by default, customizable
            boxClock = (boxClock + 1) % boxDisplayTime 
        
        # Don't stop script if an error occurs, just print it in the logs
        except Exception as e:
            print("An error occurred : ", e)


# Start script
if __name__ == "__main__":
    file.ensureSetup()
    mainLoop()