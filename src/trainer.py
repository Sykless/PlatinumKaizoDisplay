import os
import copy
from PIL import Image, ImageEnhance

import conf
from parse import PokemonData
from settings import SETTINGS

TRAINERS_START = 0xD076
TRAINER_END = 0xE1E0

TURTWIG = 387
CHIMCHAR = 390
PIPLUP = 393

SPRITE_FOLDER = "sprites"
POKEMONSPRITE_FOLDER = SPRITE_FOLDER + "/pokemon"
ITEMSPRITE_FOLDER = SPRITE_FOLDER + "/items"
TRAINERSPRITE_FOLDER = SPRITE_FOLDER + "/trainers"
BACKGROUNDPRITE_FOLDER = SPRITE_FOLDER + "/background"
MISCSPRITE_FOLDER = SPRITE_FOLDER + "/misc"

BACKGROUND_WIDTH = 656
BACKGROUND_HEIGHT = 256
POKEMON_SPRITE_WIDTH = 40
POKEMON_SPRITE_HEIGHT = 30
TRAINER_SPRITE_SIZE = 80
ITEM_SPRITE_SIZE = 32

TRAINER_CARD_WIDTH = 2 * BACKGROUND_WIDTH
TRAINER_CARD_HEIGHT = 2 * BACKGROUND_HEIGHT

LARGE_GALACTIC_ZONES = {
	"Galactic HQ": [
		"Veilstone Warehouse",
	],
	"Distortion World": [
		"Mount Coronet - Room 1",
		"Coronet Highlands - Outside 1",
		"Coronet Highlands - Room 1",
		"Coronet Highlands - Outside 2",
		"Coronet Highlands - Room 2",
		"Spear Pillar",
	]
}


# --------------------------------------------------
# TrainerData class
# --------------------------------------------------
class BitNumber:
	def __init__(self, value):
		self.value = value

class ExactNumber:
	def __init__(self, value):
		self.value = value

class TrainerData:
	def __init__(self, name, zone, address, bitNumber, pokemonTeam, itemList, spriteName, optional = False, boss = False, superboss = False, path = None, starter = None, levelCap = None, doublePartner = None):
		self.name = name
		self.zone = zone
		self.address = address
		self.bitNumber = bitNumber # Which bit is set to 1 in trainer address if defeated in-game
		self.pokemonTeam = pokemonTeam
		self.itemList = itemList
		self.spriteName = spriteName
		self.trainerId = -1

		# Optional attributes
		self.optional = optional # Only taken into account if set in options
		self.boss = boss # Set all trainers in its zone to defeated if beaten
		self.superboss = superboss # Never included in all processes, just there in case we choose to fight them
		self.path = path # Part of a path that can be taken or skipped for an alternative path
		self.starter = starter # Used to determine which Barry fight to pick
		self.levelCap = levelCap # Updates the level cap if defeated
		self.doublePartner = doublePartner # Trainer in the battle as double partner
		self.defeated = False # Defeated or hardset to True if boss beaten
		self.skipped = False # Not defeated but skipped because an alternative path has been used
		self.deadTeam = False # Only used to avoid displaying the trainer image again

	def isMandatory(self):
		return not self.optional and not self.path and not self.skipped

	def getCompleteName(self):
		return self.name + ((" + " + self.doublePartner.name) if self.doublePartner else "")

	def __str__(self):
		return f'TrainerData("{self.name}", {self.address:#010X}, {self.bitNumber.value}, [{",".join(str(pokedexId) for pokedexId in self.pokemonTeam)}], "{self.spriteName}", defeated = "{self.defeated}", skipped = "{self.skipped}")'

	def __eq__(self, trainer):
		if not isinstance(trainer, TrainerData):
			return False
		return self.name == trainer.name and self.pokemonTeam == trainer.pokemonTeam and self.itemList == trainer.itemList


# --------------------------------------------------
# Dynamic Trainer list shared between files
# --------------------------------------------------
TRAINERLIST = [] # Populated all the way down below
trainerList = []

# Retrieve editable trainer list taking rival potential team into account
def refreshTrainerList(pickedStarter, defeatedTrainers):
	pickedStarter = pickedStarter if pickedStarter in [TURTWIG, CHIMCHAR, TURTWIG] else TURTWIG

	# Reset trainer list
	global trainerList
	trainerList = []
	
	# Extract original trainer list but ignore superboss and rival with different starter
	for trainer in TRAINERLIST:
		if (trainer.superboss or trainer.starter and trainer.starter != pickedStarter):
			continue

		trainerList.append(copy.deepcopy(trainer))

	# First loop : determine which trainers have been defeated by reading emulator data
	for trainer in trainerList:
		trainerByte = defeatedTrainers[trainer.address - TRAINERS_START]
		
		# BitNumber : compare with bit n / ExactNumber : compare with actual value
		if (isinstance(trainer.bitNumber, BitNumber)):
			trainer.defeated = bool((int(trainerByte) >> trainer.bitNumber.value) & 1)
		elif (isinstance(trainer.bitNumber, ExactNumber)):
			trainer.defeated = (int(trainerByte) >= trainer.bitNumber.value)

	trainerId = len(trainerList) - 1
	nextTrainer = trainerList[trainerId]
	currentPathTrainerId = None

	# Second loop for other processes (level cap, skipped mandatory trainer, boss management)
	while (trainerId >= 0):
		trainer = trainerList[trainerId]
		trainer.trainerId = trainerId

		# Next trainer in the zone defeated but current trainer supposedly mandatory, mark it as skipped
		if (not trainer.defeated and trainer.isMandatory() and trainer.zone == nextTrainer.zone and nextTrainer.defeated):
			trainer.skipped = True

		# On Galactic/Gym zones, mark all trainers as defeated if boss is defeated
		if (trainer.boss and trainer.defeated):
			clearedZones = [trainer.zone]

			# Particular cases for large galactic zones (Coronet, HQ), mark all subzones as cleared
			if (trainer.zone in LARGE_GALACTIC_ZONES):
				clearedZones += LARGE_GALACTIC_ZONES[trainer.zone]

			while (trainerList[trainerId].zone in clearedZones):
				trainerList[trainerId].defeated = True
				trainerId -= 1
			trainerId += 1 # Keep end-of-loop logic consistent

		nextTrainer = trainerList[trainerId]
		trainerId -= 1

	# Third loop : manage alternative paths (choice between multiple trainers)
	for trainerId in range(len(trainerList)):
		trainer = trainerList[trainerId]

		# Undefeated trainer in a path : are any alternative paths cleared ?
		if (trainer.path and not trainer.defeated and not trainer.skipped):
			alternativePath = {}

			# Scout trainers in alternative paths before and after, check if all have been defeated
			for step in [-1,1]:
				currentId = trainerId + step
				isCurrentPath = True
				isAlternativePath = False

				while (0 <= currentId < len(trainerList)):
					pathTrainer = trainerList[currentId]

					# Only scout trainers in alternative paths
					if (not pathTrainer.path):
						break

					goToLowerPath = (pathTrainer.path < trainer.path)
					goToSamePath = (pathTrainer.path == trainer.path)
					gotoUpperPath = (pathTrainer.path > trainer.path)

					# Stop looking if going to an upper path going down or a lower path going up
					if (isAlternativePath and goToSamePath or step == -1 and gotoUpperPath or step == 1 and goToLowerPath):
						break

					# Go to a different path : alternative path
					if (isCurrentPath and pathTrainer.path != trainer.path):
						isAlternativePath = True
						isCurrentPath = False

					# Started current path but didn't finish it : might continue if alternative path is not cleared
					if (isCurrentPath and step == -1 and pathTrainer.defeated and not trainer.optional and not trainer.skipped):
						currentPathTrainerId = trainerId

					# Check if trainers are defeated in the alternative path
					if (isAlternativePath and not pathTrainer.optional):
						alternativePath[pathTrainer.path] = alternativePath.get(pathTrainer.path, True) and pathTrainer.defeated and not pathTrainer.skipped

					currentId += step

			# If an alternative path is cleared, mark all trainers in current path as skipped
			for cleared in alternativePath.values():
				if (cleared):
					for step in [-1,1]:
						currentId = trainerId

						# Only set trainers as skipped in this particular path
						while (trainerList[currentId].path == trainer.path):
							trainerList[currentId].skipped = True
							currentId += step
					break

			# If an alternative path is cleared, no need to restart from current path
			if (currentPathTrainerId and trainerList[currentPathTrainerId].skipped):
				currentPathTrainerId = None

	return currentPathTrainerId

def getTrainerList():
    return trainerList


# --------------------------------------------------
# Trainer methods
# --------------------------------------------------

# Retrieve which trainer is next
def getNextTrainer(currentPathTrainerId):
	trainerList = getTrainerList()
	lastDefeatedTrainerId = -1
	veryNextTrainerId = -1
	nextTrainerId = 0

	# Currently in an unfinished path : start from there
	if (currentPathTrainerId):
		veryNextTrainerId = currentPathTrainerId

	# Check which trainer is the next needed to defeat
	for trainerId in range(len(trainerList)):
		trainer = trainerList[trainerId]

		# Defeated trainer
		if (trainer.defeated):
			lastDefeatedTrainerId = trainerId

		# Trainer not defeated
		else:
			if (trainer.optional or trainer.skipped):
				continue

			if (veryNextTrainerId < 0):
				veryNextTrainerId = trainerId

	# Nominal case : next trainer is the first undefeated trainer
	nextTrainerId = veryNextTrainerId

	# Particular case : we defeated a trainer in a later zone
	if (lastDefeatedTrainerId > veryNextTrainerId):
		lastDefeatedTrainer = trainerList[lastDefeatedTrainerId]

		# Stay in the same zone as the last defeated trainer if there are still trainers there
		if (lastDefeatedTrainerId + 1 < len(trainerList) and trainerList[lastDefeatedTrainerId + 1].zone == lastDefeatedTrainer.zone):
			nextTrainerId = lastDefeatedTrainerId + 1

	return trainerList[nextTrainerId]


# Generate an image displaying the trainer sprite, Pokémon team and items
def generateTrainerCard(trainer: TrainerData, trainerParty: list[PokemonData] = [], doubleTrainerParty: list[PokemonData] = []):
	pokemonSprites = [None] * (12 if trainer.doublePartner else 6)
	itemSprites = [None] * (12 if trainer.doublePartner else 6)
	
	trainerSizeMultiplier = 4 if trainer.doublePartner else 6
	pokemonSizeMultiplier = 6 if trainer.doublePartner else 8
	itemSizeMultiplier = 3 if trainer.doublePartner else 4

	TRAINER_SIZE = trainerSizeMultiplier * TRAINER_SPRITE_SIZE
	TRAINER_POKEMON_SPRITE_WIDTH = pokemonSizeMultiplier * POKEMON_SPRITE_WIDTH
	TRAINER_POKEMON_SPRITE_HEIGHT = pokemonSizeMultiplier * POKEMON_SPRITE_HEIGHT
	TRAINER_ITEMS_SPRITE_SIZE = itemSizeMultiplier * ITEM_SPRITE_SIZE

	# Custom trainer background is enabled
	if (SETTINGS.isTrainerBackgroundDisplayed()):
		backgroundImagePath = os.path.join(BACKGROUNDPRITE_FOLDER, f"{trainer.zone}.png")

		# Cannot find background : set background transparent
		if not os.path.exists(backgroundImagePath):
			outputImage = Image.new("RGBA", (TRAINER_CARD_WIDTH, TRAINER_CARD_HEIGHT), (0,0,0,0))

		else:
			# Retrieve custom background from trainer zone
			backgroundImage = Image.open(backgroundImagePath).convert("RGBA").resize((TRAINER_CARD_WIDTH, TRAINER_CARD_HEIGHT), Image.NEAREST)

			# Darken it and set it as background of outputImage
			enhancer = ImageEnhance.Brightness(backgroundImage)
			backgroundImage = enhancer.enhance(0.5)
			outputImage = backgroundImage.copy()

	# Transparent background
	else:
		outputImage = Image.new("RGBA", (TRAINER_CARD_WIDTH, TRAINER_CARD_HEIGHT), (0,0,0,0))

	# Make sure trainer sprite exists, else don't paste it
	trainerPath = os.path.join(TRAINERSPRITE_FOLDER, f"{trainer.spriteName}.png")
	if os.path.exists(trainerPath):

		# Paste the trainer sprite
		trainerSprite = Image.open(trainerPath).convert("RGBA").resize((TRAINER_SIZE, TRAINER_SIZE), Image.NEAREST)
		outputImage.paste(trainerSprite, (0, (TRAINER_CARD_HEIGHT - 6 * TRAINER_SPRITE_SIZE) // 2), trainerSprite)

		# Double battle : display both trainer sprites in smaller size
		if (trainer.doublePartner):
			doubleSpritePath = os.path.join(TRAINERSPRITE_FOLDER, f"{trainer.doublePartner.spriteName}.png")
			
			if os.path.exists(doubleSpritePath):
				doubleSprite = Image.open(doubleSpritePath).convert("RGBA").resize((TRAINER_SIZE, TRAINER_SIZE), Image.NEAREST)
				outputImage.paste(doubleSprite, (2 * TRAINER_SPRITE_SIZE, 2 * TRAINER_SPRITE_SIZE), doubleSprite)

	# Build pokemon team and item list
	pokemonTeam = trainer.pokemonTeam + [None] * (6 - len(trainer.pokemonTeam))
	itemList = trainer.itemList + [0] * (6 - len(trainer.itemList))

	if (trainer.doublePartner):
		pokemonTeam += trainer.doublePartner.pokemonTeam + [None] * (6 - len(trainer.doublePartner.pokemonTeam))
		itemList += trainer.doublePartner.itemList + [0] * (6 - len(trainer.doublePartner.itemList))

	# Retrieve each Pokémon and held item sprites in trainer team
	for i in range(len(pokemonTeam)):
		pokedexId = pokemonTeam[i]
		itemId = itemList[i]
		pokemonKo = False

		# Currently battling a trainer, check if each Pokémon still has HP
		if (trainerParty):
			for party in [trainerParty, doubleTrainerParty]:
				for pokemonData in party:
					if (pokemonData.pokedexId == pokedexId and pokemonData.itemId == itemId):
						pokemonKo = (pokemonData.currentHp == 0)
						break

		# Retrieve Pokémon sprite from pokedexId and display it
		if (pokedexId):
			pokemonSpritePath = os.path.join(POKEMONSPRITE_FOLDER, f"{pokedexId}.png")
			if not os.path.exists(pokemonSpritePath):
				pokemonSpritePath = os.path.join(POKEMONSPRITE_FOLDER, "0.png")

			pokemonSprites[i] = Image.open(pokemonSpritePath).convert("RGBA").resize((TRAINER_POKEMON_SPRITE_WIDTH, TRAINER_POKEMON_SPRITE_HEIGHT), Image.NEAREST)
			pokemonSprites[i] = ImageEnhance.Brightness(pokemonSprites[i]).enhance(0.3 if pokemonKo else 1)

		# Retrieve item sprite from itemId and display it
		if (itemId and SETTINGS.isTrainerItemSpriteDisplayed()):
			itemSpritePath = os.path.join(ITEMSPRITE_FOLDER, f"{itemId}.png")
			if not os.path.exists(itemSpritePath):
				itemSpritePath = os.path.join(ITEMSPRITE_FOLDER, "0.png")

			itemSprites[i] = Image.open(itemSpritePath).convert("RGBA").resize((TRAINER_ITEMS_SPRITE_SIZE, TRAINER_ITEMS_SPRITE_SIZE), Image.NEAREST)
			itemSprites[i] = ImageEnhance.Brightness(itemSprites[i]).enhance(0.3 if pokemonKo else 1)

	# Set positions depending on team size and if double battle
	baseX = int(7/8 * TRAINER_SPRITE_SIZE * 6)
	baseY = 0
	pokemonPerLine = 3
	xPadding = 0.85
	xEvenPadding = 0
	yEvenPadding = 0

	if (trainer.doublePartner):
		baseY = 5
		pokemonPerLine = 6
		xPadding = [0.7, 0.7, 0.7, 0.7, 0.65, 0.55][len(trainer.pokemonTeam) - 1]
		xPaddingDouble = [0.7, 0.7, 0.7, 0.7, 0.65, 0.55][len(trainer.doublePartner.pokemonTeam) - 1]
		xEvenPadding = TRAINER_POKEMON_SPRITE_WIDTH // 20
		yEvenPadding = TRAINER_POKEMON_SPRITE_WIDTH // 4
	
	# Paste Pokémon team and items
	for i, poke in enumerate(pokemonSprites):
		if (poke):
			x = baseX + (i % pokemonPerLine) * int((xPadding if i < 6 else xPaddingDouble) * TRAINER_POKEMON_SPRITE_WIDTH) + (i % 2) * xEvenPadding
			y = baseY + (i // pokemonPerLine) * (8 * POKEMON_SPRITE_HEIGHT) + (i % 2) * yEvenPadding
			outputImage.paste(poke, (x,y), poke)

			if (itemSprites[i]):
				x = x + int(1.4 * TRAINER_ITEMS_SPRITE_SIZE)
				y = y + int(0.95 * TRAINER_ITEMS_SPRITE_SIZE)
				outputImage.paste(itemSprites[i], (x,y), itemSprites[i])

	return outputImage


# Find which trainer we're battling from the provided trainer team
def findTrainerFromTeam(oldTrainer: TrainerData, trainerParty: list[PokemonData], doubleTrainerParty: list[PokemonData]):
	
	# Not battling a trainer, can't match one, return old battleOver value
	if (not trainerParty):
		return False, oldTrainer

	# Search a match with both trainer and double trainer team
	for currentParty in [trainerParty, doubleTrainerParty]:

		# Extract Pokémons with held items and create a pairs set
		trainerPokemons = [pokemonData.pokedexId for pokemonData in currentParty]
		trainerItems = [pokemonData.itemId for pokemonData in currentParty]
		battledTrainerPairs = set(zip(trainerPokemons, trainerItems))

		# Iterate on each trainer to find a matching team
		for trainer in TRAINERLIST:

			# Not even the same number of Pokémons, skip
			if (len(trainer.pokemonTeam) != len(trainerPokemons)):
				continue

			# Create a pairs set from trainer database for easier comparison
			trainerPairs = set(zip(trainer.pokemonTeam, trainer.itemList))

			# Found a match, check if trainer team is KO and return it
			if (battledTrainerPairs == trainerPairs):
				battledTrainer = copy.deepcopy(trainer)
				battledTrainer.deadTeam = all(trainerData.currentHp == 0 for trainerData in trainerParty + doubleTrainerParty)
				return True, battledTrainer

	return False, oldTrainer


# Find id in current trainer list
def getTrainerId(trainer: TrainerData):
	trainerList = getTrainerList()

	for trainerId in range(len(trainerList)):
		if (trainerList[trainerId] == trainer):
			return trainerId

	# Not found
	return -1


# Fill trainer list with data retrieved from documentation
TRAINERLIST = [
	TrainerData("Youngster Tristan", "Route 202", 0xE08A, BitNumber(1), [263,161,16], [251,251,244], "youngster-gen4dp"),
	TrainerData("Lass Natalie", "Route 202", 0xE08A, BitNumber(3), [191,396,261], [155,155,155], "lass-gen4dp"),
	TrainerData("Bug Catcher Logan", "Route 202", 0xE08A, BitNumber(2), [13,10,265,401], [0,0,0,0], "bugcatcher-gen4dp"),
	TrainerData("Clown Moe", "Jubilife City", 0xDFFD, BitNumber(5), [296,440,175], [158,213,203], "clown"),
	TrainerData("Clown Mickey", "Jubilife City", 0xDFFD, BitNumber(6), [172,238,174], [43,43,43], "clown"),
	TrainerData("Clown Ronald", "Jubilife City", 0xDFFD, BitNumber(7), [439,209,173], [269,326,155], "clown"),
	TrainerData("Lass Samantha", "Route 204 South", 0xE08B, BitNumber(3), [422,37,406], [187,185,184], "lass-gen4dp"),
	TrainerData("Youngster Tyler", "Route 204 South", 0xE08B, BitNumber(2), [349,129,54], [285,275,285], "youngster-gen4dp"),
	TrainerData("Lass Sarah", "Route 204 South", 0xE08B, BitNumber(4), [403,300,52], [0,251,251], "lass-gen4dp"),
	TrainerData("Barry #2 - Turtwig", "Route 203", 0xDEB0, ExactNumber(1), [190,276,287,56,239,390], [251,273,220,268,268,43], "barry", starter = TURTWIG),
	TrainerData("Barry #2 - Chimchar", "Route 203", 0xDEB0, ExactNumber(1), [190,276,287,56,239,393], [251,273,220,268,268,43], "barry", starter = CHIMCHAR),
	TrainerData("Barry #2 - Piplup", "Route 203", 0xDEB0, ExactNumber(1), [190,276,287,56,239,387], [251,273,220,268,268,43], "barry", starter = PIPLUP),
	TrainerData("Youngster Dallas", "Route 203", 0xE0B6, BitNumber(3), [4,158,252,293], [249,243,239,251], "youngster-gen4dp"),
	TrainerData("Youngster Michael", "Route 203", 0xE08A, BitNumber(4), [152,255,7,19], [269,249,243,273], "youngster-gen4dp"),
	TrainerData("Bug Catcher Sebastian", "Route 203", 0xE0B6, BitNumber(4), [1412,268,266,14,11], [43,43,43,43,43], "bugcatcher-gen4dp"),
	TrainerData("Lass Kaitlin", "Route 203", 0xE0B2, BitNumber(3), [209,58,309,447], [251,268,106,221], "lass-gen4dp"),
	TrainerData("Lass Madeline", "Route 203", 0xE0B2, BitNumber(2), [179,393,390,387], [242,243,249,239], "lass-gen4dp"),
	TrainerData("Camper Curtis", "Oreburgh Gate", 0xE0AB, BitNumber(1), [216,325,27,278,32], [272,270,237,186,245], "camper"),
	TrainerData("Picnicker Diana", "Oreburgh Gate", 0xE0B3, BitNumber(1), [133,433,41,280,29], [251,248,244,210,276], "picnicker"),
	TrainerData("Worker Mason", "Oreburgh Mine", 0xE0A2, BitNumber(4), [415,231,74,399], [222,266,185,43], "worker-gen4"),
	TrainerData("Worker Colin", "Oreburgh Mine", 0xE0A2, BitNumber(3), [206,111,218,66], [155,270,149,0], "worker-gen4"),
	TrainerData("Scientist Jonathon", "Oreburgh Gym", 0xE0A8, BitNumber(4), [304,66,138,347,95], [158,234,253,0,288], "scientist-gen4dp"),
	TrainerData("Ruin Maniac Darius", "Oreburgh Gym", 0xE0A8, BitNumber(5), [410,140,246,240,299], [43,201,272,234,157], "ruinmaniac"),
	TrainerData("Leader Roark", "Oreburgh Gym", 0xD076, BitNumber(0), [438,345,443,222,213,408], [275,296,150,187,43,157], "roark", boss = True, levelCap = 28),
	TrainerData("Galacticf Venus", "Jubilife City", 0xDE8E, ExactNumber(4), [322,434,102,109], [284,275,270,265], "galacticgruntf",
		doublePartner = TrainerData("Galactic Luna", "Jubilife City", 0xDE8E, ExactNumber(4), [35,353,374,299], [43,151,43,151], "galacticgrunt")),
	TrainerData("Twins Liv & Liz", "Route 204 North", 0xE08B, BitNumber(7), [285,417,60,453], [285,43,243,193], "twins-gen4dp"),
	TrainerData("Bug Catcher Brandon", "Route 204 North", 0xE08B, BitNumber(5), [167,165,290,48,341], [155,155,155,155,275], "bugcatcher-gen4dp"),
	TrainerData("Aroma Lady Taylor", "Route 204 North", 0xE08B, BitNumber(6), [406,420,43,187,69], [284,43,296,284,265], "aromalady"),
	TrainerData("Galactic Mercury", "Floaroma Meadow", 0xDF72, ExactNumber(1), [431,360,451,120], [251,43,230,213], "galacticgrunt"),
	TrainerData("Galacticf Terra", "Floaroma Meadow", 0xDF72, ExactNumber(1), [328,72,96,46], [43,267,43,275], "galacticgruntf"),
	TrainerData("Galactic Pluto", "Valley Windworks", 0xE011, BitNumber(6), [425,459,137,215,63], [158,184,269,275,270], "galacticgrunt"),
	TrainerData("Galactic Squad Deimos", "Valley Windworks", 0xE0AF, BitNumber(2), [235,200,228,42,371], [269,267,157,275,287], "galacticsquad"),
	TrainerData("Galactic Squad Phobos", "Valley Windworks", 0xE0AF, BitNumber(3), [355,337,198,197,168], [158,204,270,221,217], "galacticsquad"),
	TrainerData("Commander Mars", "Valley Windworks", 0xDF3E, ExactNumber(2), [227,449,338,444,207,432], [157,43,213,188,188,234], "mars", boss = True),
	TrainerData("Camper Jacob", "Route 205 South", 0xE08C, BitNumber(0), [273,86,77,33], [217,221,268,0], "camper"),
	TrainerData("Hiker Daniel", "Route 205 South", 0xE08C, BitNumber(2), [296,50,21,74], [273,238,266,275], "hiker-gen4"),
	TrainerData("Aroma Lady Elizabeth", "Route 205 South", 0xE08C, BitNumber(5), [188,270,12,440], [234,296,195,234], "aromalady"),
	TrainerData("Picnicker Siena", "Route 205 South", 0xE08C, BitNumber(1), [30,298,177,363], [245,266,270,246], "picnicker"),
	TrainerData("Camper Zackary", "Route 205 South", 0xE0B9, BitNumber(1), [418,267,161,403], [243,244,251,242], "camper"),
	TrainerData("Hiker Nicholas", "Route 205 South", 0xE08C, BitNumber(3), [104,316,163,446], [258,281,158,234], "hiker-gen4"),
	TrainerData("Picnicker Karina", "Route 205 South", 0xE0C3, BitNumber(0), [23,216,325,263], [158,273,89,158], "picnicker"),
	TrainerData("Battle Girl Kelsey", "Route 205 South", 0xE08C, BitNumber(4), [236,84,427,307], [275,160,266,214], "battlegirl-gen4"),
	TrainerData("Galacticf Ophelia", "Eterna Forest", 0xE0A3, BitNumber(1), [353,2413,305], [247,157,255], "galacticgruntf", 
		doublePartner = TrainerData("Galacticf Bianca", "Eterna Forest", 0xE0A3, BitNumber(4), [39,316,320], [251,270,266], "galacticgruntf")),
	TrainerData("Galactic Prospero", "Eterna Forest", 0xE0C3, BitNumber(7), [436,292,111], [269,275,230], "galacticgrunt", path = 1,
		doublePartner = TrainerData("Galacticf Miranda", "Eterna Forest", 0xE0C4, BitNumber(0), [425,88,446], [214,214,273], "galacticgruntf", path = 1)),
	TrainerData("Galactic Setebos", "Eterna Forest", 0xE0C3, BitNumber(5), [204,100,299], [184,270,214], "galacticgrunt", path = 2,
		doublePartner = TrainerData("Galacticf Sycorax", "Eterna Forest", 0xE0C3, BitNumber(6), [355,345,200], [234,200,247], "galacticgruntf", path = 2)),
	TrainerData("Galactic Puck", "Eterna Forest", 0xE0BD, BitNumber(3), [109,375,343,185], [210,157,270,214], "galacticgrunt", path = 1),
	TrainerData("Galactic Trinculo", "Eterna Forest", 0xE0BD, BitNumber(5), [92,90,81,108], [245,246,313,251], "galacticgrunt", path = 2),
	TrainerData("Galacticf Venus", "Eterna Forest", 0xE0A3, BitNumber(3), [15,247,372,434,455], [221,275,221,234,296], "galacticgruntf", path = 1),
	TrainerData("Galactic Mercury", "Eterna Forest", 0xE0A3, BitNumber(2), [218,102,274,95,431], [275,194,270,187,251], "galacticgrunt", path = 2),
	TrainerData("Galacticf Uranus", "Eterna Forest", 0xE0A3, BitNumber(6), [459,1413,64], [275,213,273], "galacticgruntf", path = 1,
		doublePartner = TrainerData("Galactic Francisco", "Eterna Forest", 0xE0C0, BitNumber(0), [35,361,220], [270,230,230], "galacticgrunt", path = 1)),
	TrainerData("Galactic Triton", "Eterna Forest", 0xE0BB, BitNumber(3), [138,347,170], [187,221,150], "galacticgrunt", path = 2,
		doublePartner = TrainerData("Galactic Neptune", "Eterna Forest", 0xE0BB, BitNumber(6), [148,120,140], [150,270,221], "galacticgrunt", path = 2)),
	TrainerData("Galacticf Terra", "Eterna Forest", 0xE013, BitNumber(3), [235,123,307,93], [275,157,270,214], "galacticgruntf", boss = True,
		doublePartner = TrainerData("Galactic Luna", "Eterna Forest", 0xE013, BitNumber(3), [96,193,329,36], [269,221,270,270], "galacticgrunt", boss = True)),
	TrainerData("Fisherman Joseph", "Route 205 North", 0xE08C, BitNumber(7), [79,72,60,318,194], [221,191,43,240,43], "fisherman-gen4"),
	TrainerData("Fisherman Andrew", "Route 205 North", 0xE08C, BitNumber(6), [422,339,147,118,116], [285,187,201,243,267], "fisherman-gen4"),
	TrainerData("Fisherman Zachary", "Route 205 North", 0xE08D, BitNumber(0), [456,170,458,223,98], [285,285,285,210,275], "fisherman-gen4"),
	TrainerData("Lass Caroline", "Eterna Gym", 0xDEFC, ExactNumber(2), [388,253,153,2,271], [157,214,296,265,268], "lass-gen4dp"),
	TrainerData("Aroma Lady Jenna", "Eterna Gym", 0xDEFC, ExactNumber(3), [322,421,70,44,185], [275,239,214,157,266], "aromalady"),
	TrainerData("Artist Angel", "Eterna Gym", 0xDEFC, ExactNumber(5), [235,357,286,192,455], [275,234,275,296,214], "artist-gen4"),
	TrainerData("Leader Gardenia", "Eterna Gym", 0xD076, BitNumber(1), [241,5479,272,350,407,389], [157,267,266,234,234,157], "gardenia", boss = True, levelCap = 38),
	TrainerData("Galactic Amalthia", "Team Galactic Eterna Building", 0xE0BE, BitNumber(5), [324,166,305,110,281], [185,269,275,281,210], "galacticgrunt"),
	TrainerData("Scientist Galileo", "Team Galactic Eterna Building", 0xE0F1, BitNumber(7), [375,120,132,125,75], [217,270,154,265,275], "scientist-gen4dp"),
	TrainerData("Galactic Callisto", "Team Galactic Eterna Building", 0xE0BD, BitNumber(2), [449,299,64,331,35], [157,234,230,213,272], "galacticgrunt"),
	TrainerData("Galactic Europa", "Team Galactic Eterna Building", 0xE0BE, BitNumber(7), [459,471,364,36,178], [275,255,234,202,314], "galacticgrunt"),
	TrainerData("Galactic Ganymede", "Team Galactic Eterna Building", 0xE0BD, BitNumber(4), [15,202,82,51,197], [275,234,191,221,234], "galacticgrunt"),
	TrainerData("Galactic Io", "Team Galactic Eterna Building", 0xE0BE, BitNumber(6), [168,372,126,93,233], [217,214,203,191,267], "galacticgrunt"),
	TrainerData("Commander Jupiter", "Team Galactic Eterna Building", 0xE01F, BitNumber(5), [435,101,130,308,337,465], [210,201,186,214,265,272], "jupiter", boss = True),
	TrainerData("Cyclist Axel", "Route 206", 0xE08D, BitNumber(3), [311,327], [242,265], "cyclist-gen4",
		doublePartner = TrainerData("Cyclist John", "Route 206", 0xE08D, BitNumber(1), [312,397], [267,244], "cyclist-gen4")),
	TrainerData("CyclistF Megan", "Route 206", 0xE08D, BitNumber(6), [162,404], [255,266], "cyclistf-gen4",
		doublePartner = TrainerData("CyclistF Nicole", "Route 206", 0xE08D, BitNumber(5), [61,256], [158,230], "cyclistf-gen4")),
	TrainerData("Cyclist James", "Route 206", 0xE08D, BitNumber(2), [183,237,77,33,305], [243,221,249,240,189], "cyclist-gen4", optional = True),
	TrainerData("CyclistF Rachel", "Route 206", 0xE08E, BitNumber(0), [17,444,364,156,30], [160,249,246,217,265], "cyclistf-gen4", optional = True),
	TrainerData("Cyclist Ryan", "Route 206", 0xE08D, BitNumber(4), [75,81,391,84,288], [210,210,203,160,203], "cyclist-gen4"),
	TrainerData("CyclistF Karen", "Route 206", 0xE08D, BitNumber(7), [109,435,22,264,232], [210,191,201,220,201], "cyclistf-gen4"),
	TrainerData("Roughneck Robert", "Route 207", 0xE08E, BitNumber(7), [95,130,208,73], [287,268,278,281], "roughneck-gen4"),
	TrainerData("Pokefan Stewart", "Route 207", 0xE090, BitNumber(2), [439,172,174,414], [269,242,270,222], "pokefan-gen4"),
	TrainerData("Pokefan Martha", "Route 207", 0xE090, BitNumber(3), [438,35,320,238], [185,158,158,248], "pokefanf-gen4"),
	TrainerData("Blackbelt Kyle", "Route 208", 0xE08F, BitNumber(2), [57,394,125,126], [326,230,268,268], "blackbelt-gen4dp"),
	TrainerData("Aroma Lady Hannah", "Route 208", 0xE08F, BitNumber(4), [189,114,182,45,71], [269,255,318,276,214], "aromalady"),
	TrainerData("Hiker Alexander", "Route 208", 0xE08F, BitNumber(0), [320,454,441,294,402], [277,221,204,267,276], "hiker-gen4"),
	TrainerData("Hiker Jonathan", "Route 208", 0xE08F, BitNumber(1), [42,75,446,221,259], [212,275,273,211,187], "hiker-gen4"),
	TrainerData("Dragon Tamer Drax", "Route 208", 0xE08F, BitNumber(3), [193,253,334,159,5], [277,326,205,327,249], "dragontamer"),
	TrainerData("Artist William", "Route 208", 0xE08F, BitNumber(5), [235,324,8,388,67], [251,253,253,253,193], "artist-gen4"),
	TrainerData("Ninja Boy Donny", "Hearthome Gym", 0xE0B6, BitNumber(5), [207,168,93,19,123,132], [255,213,312,275,306,154], "ninjaboy", optional = True),
	TrainerData("Policeman Morton", "Hearthome Gym", 0xE0B2, BitNumber(5), [457,229,164,313,171], [265,210,213,213,234], "policeman-gen4", optional = True),
	TrainerData("Psychic Tony", "Hearthome Gym", 0xE08E, BitNumber(2), [49,200,64,173,121], [308,234,275,275,270], "psychic-gen4", optional = True),
	TrainerData("Idol Catherine", "Hearthome Gym", 0xE0AD, BitNumber(4), [53,336,222,295,441,200], [214,327,210,251,270,211], "idol"),
	TrainerData("Clown Chance", "Hearthome Gym", 0xE0B4, BitNumber(4), [101,199,262,108], [269,276,157,210], "clown", optional = True),
	TrainerData("Artist Allen", "Hearthome Gym", 0xE0AD, BitNumber(0), [235,105,354,97,201], [210,258,217,157,267], "artist-gen4", optional = True),
	TrainerData("Idol Amber", "Hearthome Gym", 0xE08E, BitNumber(1), [432,282,370,314], [327,217,157,222], "idol", optional = True),
	TrainerData("Leader Fantina ?", "Hearthome Gym", 0xE033, BitNumber(4), [356,426,292,302,354,429], [234,0,275,0,0,0], "fantina"),
	TrainerData("Clown Justin", "Hearthome Gym", 0xE08E, BitNumber(5), [405,51,342,94], [269,255,286,270], "clown", optional = True),
	TrainerData("Policeman Kevin", "Hearthome Gym", 0xE08E, BitNumber(4), [235,197,47,303], [275,208,234,209], "policeman-gen4", optional = True),
	TrainerData("Psychic Helen", "Hearthome Gym", 0xE08E, BitNumber(6), [337,31,479,36], [157,281,213,270], "psychicf-gen4", optional = True),
	TrainerData("Psychic Theodore", "Hearthome Gym", 0xE0C2, BitNumber(3), [178,355,198,338], [270,234,275,265], "psychic-gen4", optional = True),
	TrainerData("Ninja Boy Drew", "Hearthome Gym", 0xE0AB, BitNumber(2), [291,89,215,24], [214,214,275,327], "ninjaboy", optional = True),
	TrainerData("Idol Catherine", "Hearthome Gym", 0xE0AE, BitNumber(3), [53,336,222,200], [214,327,210,211], "idol", optional = True),
	TrainerData("Clown Luigi", "Hearthome Gym", 0xE08E, BitNumber(3), [425,122,424,317,181,463], [158,269,327,286,270,272], "clown"),
	TrainerData("Ninja Boy Donny", "Hearthome Gym", 0xE0B7, BitNumber(5), [207,168,93,19,123,132], [255,213,312,275,306,154], "ninjaboy", optional = True),
	TrainerData("Psychic Cheyenne", "Hearthome Gym", 0xE0B3, BitNumber(2), [359,332,196,93,157], [275,213,265,255,211], "psychic-gen4"),
	TrainerData("Leader Fantina ?", "Hearthome Gym", 0xE0B4, BitNumber(7), [356,426,292,302,354,429], [234,0,275,0,0,0], "fantina", optional = True),
	TrainerData("Leader Fantina", "Hearthome Gym", 0xD076, BitNumber(4), [478,426,94,442,4479,429], [275,201,265,234,198,157], "fantina", boss = True, levelCap = 42),
	TrainerData("Barry #3 - Turtwig", "Hearthome City", 0xDE96, ExactNumber(2), [277,424,466,289,272,392], [272,270,157,214,234,270], "barry", levelCap = 47, starter = TURTWIG),
	TrainerData("Barry #3 - Chimchar", "Hearthome City", 0xDE96, ExactNumber(2), [277,424,466,289,51,395], [272,214,268,270,275,158], "barry", levelCap = 47, starter = CHIMCHAR),
	TrainerData("Barry #3 - Piplup", "Hearthome City", 0xDE96, ExactNumber(2), [277,424,466,289,57,389], [272,251,270,157,268,234], "barry", levelCap = 47, starter = PIPLUP),
	TrainerData("Pkmn Breeder Albert", "Route 209", 0xE08F, BitNumber(6), [122,400,195,80], [158,203,234,154], "pokemonbreeder-gen4"),
	TrainerData("Jogger Richard", "Route 209", 0xE090, BitNumber(1), [82,85,51], [191,186,188], "jogger"),
	TrainerData("Twins Emma & Lil", "Route 209", 0xE0AE, BitNumber(6), [203,319,405,59,446], [327,243,327,327,272], "twins-gen4dp"),
	TrainerData("Poké Kid Danielle", "Route 209", 0xE090, BitNumber(5), [172,132,25,185,15], [275,257,236,150,221], "pokekid"),
	TrainerData("Pkmn BreederF Jennifer", "Route 209", 0xE08F, BitNumber(7), [113,366,83,105], [256,227,259,258], "pokemonbreederf-gen4"),
	TrainerData("Jogger Raul", "Route 209", 0xE0B0, BitNumber(4), [327], [277], "jogger", optional = True),
	TrainerData("Cowgirl Shelley", "Route 209", 0xE090, BitNumber(0), [78,241,176,181], [265,234,16,191], "cowgirl"),
	TrainerData("Young Couple Ty & Sue", "Route 209", 0xE090, BitNumber(7), [124,334,40,136,31,370], [209,188,234,156,156,221], "youngcouple-gen4dp"),
	TrainerData("Rancher Marco", "Route 210 South", 0xE0AE, BitNumber(4), [164,257,332,128], [265,268,194,214], "rancher"),
	TrainerData("Jogger Wyatt", "Route 210 South", 0xE0B0, BitNumber(2), [432,59], [326,212], "jogger", optional = True),
	TrainerData("Belle & Pa Ava & Matt", "Route 210 South", 0xE0AE, BitNumber(2), [428,326,182,25,289], [251,214,238,236,234], "bellepa"),
	TrainerData("Pkmn Breeder Johnny", "Route 210 South", 0xE091, BitNumber(1), [219,126,114,463,39,238], [275,207,204,207,230,230], "pokemonbreeder-gen4"),
	TrainerData("Waitress Kati", "Café", 0xE0B7, BitNumber(6), [242,241], [158,157], "waitress-gen4", optional = True),
	TrainerData("Gambler John Keating", "Café", None, BitNumber(None), [241,122,250,398,99,467], [205,202,202,230,217,298], "gambler", superboss = True),
	TrainerData("Ruin Maniac Calvin", "Route 215", 0xE0B0, BitNumber(0), [346,347,140,138,366], [234,201,187,187,226], "ruinmaniac"),
	TrainerData("CyclistF Cecelia", "Route 215", 0xE0B0, BitNumber(3), [457,101,284,436], [222,267,195,215], "cyclistf-gen4"),
	TrainerData("Twins Teri & Tia", "Route 215", 0xE092, BitNumber(1), [312,311,314,313,279,119], [270,270,150,270,186,243], "twins-gen4dp"),
	TrainerData("Rancher Gregory", "Route 215", 0xE099, BitNumber(7), [186,310,3,400], [149,269,281,214], "rancher"),
	TrainerData("Blackbelt Derek", "Route 215", 0xE09A, BitNumber(0), [475,454,125,62,286], [241,281,268,296,192], "blackbelt-gen4dp"),
	TrainerData("Jogger Scott", "Route 215", 0xE09A, BitNumber(2), [205,237,110], [150,266,217], "jogger", optional = True),
	TrainerData("Beauty Jasmine", "Route 215", 0xE09A, BitNumber(1), [73,446,26,375,231,357], [281,189,270,157,234,214], "beauty-gen4dp"),
	TrainerData("Double Team Nate & Lisa", "Route 215", 0xE0AC, BitNumber(6), [466,419,448,407,429,478], [268,299,275,234,157,270], "doubleteam"),
	TrainerData("Galactic Uranus", "Veilstone City", 0xDF8A, ExactNumber(1), [460,121,478,282,91,351], [184,234,213,234,210,270], "galacticgrunt",
		doublePartner = TrainerData("Galactic Cupid", "Veilstone City", 0xDF8A, ExactNumber(1), [36,124,471,1413,350], [234,213,213,213,234], "galacticgrunt")),
	TrainerData("Battle Girl Carly", "Veilstone Gym", 0xE0B0, BitNumber(5), [210,202,59,475,214], [157,234,214,192,203], "battlegirl-gen4"),
	TrainerData("Blackbelt Daniel", "Veilstone Gym", 0xE0B0, BitNumber(6), [392,123,57,206,424], [249,275,266,157,251], "blackbelt-gen4dp"),
	TrainerData("Roughneck Rafael", "Veilstone Gym", 0xE0B0, BitNumber(7), [237,232,430,217,297], [214,157,232,273,234], "roughneck-gen4"),
	TrainerData("Battle Girl Jedrzejczyk", "Veilstone Gym", 0xE0B1, BitNumber(0), [62,115,454,215,428], [157,214,275,275,251], "battlegirl-gen4"),
	TrainerData("BirdKeeper Kahlil", "Veilstone Gym", 0xE091, BitNumber(0), [83,398,257,107,275], [259,266,270,221,214], "birdkeeper-gen4dp"),
	TrainerData("Roughneck Magnus", "Veilstone Gym", 0xE0B9, BitNumber(6), [342,68,202,335,76], [275,157,210,251,210], "roughneck-gen4"),
	TrainerData("Leader Maylene", "Veilstone Gym", 0xD076, BitNumber(2), [115,392,85,106,308,448], [157,157,272,272,192,275], "maylene", boss = True, levelCap = 54),
	TrainerData("PsychicF Abigail", "Route 214", 0xE099, BitNumber(0), [302,124,308], [150,198,214], "psychicf-gen4",
		doublePartner = TrainerData("Psychic Mitchell", "Route 214", 0xE098, BitNumber(7), [358,203,26], [269,158,268], "psychic-gen4")),
	TrainerData("Gambler Carlos", "Route 214", 0xE099, BitNumber(1), [53,67,82,365,113], [326,230,213,154,256], "gambler"),
	TrainerData("Ruin Maniac Bryan", "Route 214", 0xE098, BitNumber(1), [411,442,389,141], [189,234,234,187], "ruinmaniac"),
	TrainerData("Collector Ripper", "Route 214", 0xE0AC, BitNumber(0), [197,196,134,471,135,470], [207,205,207,206,202,204], "collector"),
	TrainerData("Beauty Cyndy", "Route 214", 0xE0B5, BitNumber(2), [267,334,428,303], [275,188,214,212], "beauty-gen4dp"),
	TrainerData("Ruin Maniac Jones", "Route 214", 0xE098, BitNumber(2), [436,409,356,139], [157,278,210,278], "ruinmaniac"),
	TrainerData("Collector Brady", "Route 214", 0xE0AC, BitNumber(1), [476,132,344,233,354,479], [189,154,268,251,310,196], "collector"),
	TrainerData("Interviewers Molly & Shannon", "Valor Lakefront", 0xE0DF, BitNumber(7), [358,82,426,327], [150,150,157,150], "interviewers"),
	TrainerData("BirdKeeper Billie", "Valor Lakefront", 0xDF94, ExactNumber(2), [178,441], [273,150], "birdkeeper-gen4dp",
		doublePartner = TrainerData("Ruin Maniac Bruno", "Valor Lakefront", 0xDF94, ExactNumber(2), [105,112], [258,275], "ruinmaniac")),
	TrainerData("Sailor Gene", "Valor Lakefront", 0xDF94, ExactNumber(3), [279,134], [150,150], "sailor",
		doublePartner = TrainerData("PokéKid Jerry", "Valor Lakefront", 0xDF94, ExactNumber(3), [26,25], [150,236], "pokekid")),
	TrainerData("Guitarist Kenny", "Valor Lakefront", 0xDF94, ExactNumber(4), [310,362], [150,150], "guitarist-gen4",
		doublePartner = TrainerData("Idol Dolly", "Valor Lakefront", 0xDF94, ExactNumber(4), [184,40], [150,150], "idol")),
	TrainerData("Beauty Britney", "Valor Lakefront", 0xDF94, ExactNumber(5), [303,38], [150,272], "beauty-gen4dp",
		doublePartner = TrainerData("Dragon Tamer Elton", "Valor Lakefront", 0xDF94, ExactNumber(5), [334,352], [150,150], "dragontamer")),
	TrainerData("Double Team Stevie and Lindsey", "Valor Lakefront", 0xE0E1, BitNumber(0), [317,463,402,53,326,288], [150,272,150,150,150,234], "doubleteam"),
	TrainerData("Tuber Jared", "Route 213", 0xE097, BitNumber(3), [349,422], [208,158], "tuber", optional = True),
	TrainerData("TuberF Chelsea", "Route 213", 0xE097, BitNumber(4), [129,422], [201,151], "tuberf", optional = True),
	TrainerData("SwimmerF Mary", "Route 213", 0xE097, BitNumber(2), [26,55,224], [265,276,232], "swimmerf-gen4dp"),
	TrainerData("Swimmer Sheltin", "Route 213", 0xE096, BitNumber(7), [68,319,117], [285,327,206], "swimmer-gen4dp"),
	TrainerData("SwimmerF Haley", "Route 213", 0xE097, BitNumber(1), [119,62,226], [285,266,267], "swimmerf-gen4dp"),
	TrainerData("Fisherman Kenneth", "Route 213", 0xE097, BitNumber(7), [457,367,171,369], [285,327,222,186], "fisherman-gen4"),
	TrainerData("Sailor Paul", "Route 213", 0xE097, BitNumber(6), [210,279,67,87], [158,276,241,203], "sailor"),
	TrainerData("Beauty Chelle", "Route 213", 0xDF94, ExactNumber(9), [112,301,123,327,171,154], [275,251,275,161,234,42], "beauty-gen4dp"),
	TrainerData("PKMN Breeder Frank", "Pastoria City", None, BitNumber(None), [107,369,143,357,229,334], [230,230,202,204,230,202], "pokemonbreeder-gen4", superboss = True),
	TrainerData("Barry #4 - Turtwig", "Pastoria City", 0xDE98, ExactNumber(2), [398,424,466,289,254,392], [214,157,157,157,266,275], "barry", starter = TURTWIG),
	TrainerData("Barry #4 - Chimchar", "Pastoria City", 0xDE98, ExactNumber(2), [398,424,466,289,260,395], [251,270,268,214,268,201], "barry", starter = CHIMCHAR),
	TrainerData("Barry #4 - Piplup", "Pastoria City", 0xDE98, ExactNumber(2), [398,424,466,289,257,389], [157,214,157,214,266,234], "barry", starter = PIPLUP),
	TrainerData("Roughneck Walter", "Pastoria Gym", 0xE0BC, BitNumber(1), [452,455,130,160,454,342], [270,213,186,214,234,275], "roughneck-gen4"),
	TrainerData("Fisherman Josh", "Pastoria Gym", 0xE095, BitNumber(4), [101,119,99,319,340,80], [269,157,326,214,214,234], "fisherman-gen4"),
	TrainerData("Tuber Jacky", "Pastoria Gym", 0xE0C8, BitNumber(1), [463,47,426,195,26,55], [272,217,211,234,275,157], "tuber"),
	TrainerData("Parasol Lady Monet", "Pastoria Gym", 0xE0B4, BitNumber(3), [164,45,283,465,351,400], [244,267,204,150,270,214], "parasollady-gen4"),
	TrainerData("TuberF Caitlyn", "Pastoria Gym", 0xE0C8, BitNumber(2), [184,40,317,25,186,71], [243,189,214,236,157,270], "tuberf"),
	TrainerData("Pkmn Ranger Erick", "Pastoria Gym", 0xE0AE, BitNumber(5), [489,423,3,6,9,254], [221,234,267,275,243,214], "pokemonranger-gen4"),
	TrainerData("Pkmn Ranger Sam", "Pastoria Gym", 0xE0C6, BitNumber(3), [68,289,134,154,350,423], [157,234,203,234,157,234], "pokemonrangerf-gen4"),
	TrainerData("Leader CrasherWake", "Pastoria Gym", 0xD076, BitNumber(3), [211,260,272,62,143,419], [275,187,158,214,234,270], "crasherwake", boss = True, levelCap = 65),
	TrainerData("Galactic Io", "Valor Lakefront", 0xDE98, ExactNumber(6), [323,103,94,275,467,474], [275,149,270,214,150,230], "galacticgrunt"),
	TrainerData("Policeman Bobby", "Pokemon Mansion - Exterior", 0xE095, BitNumber(0), [326], [214], "policeman-gen4"),
	TrainerData("Lady Melissa", "Pokemon Mansion - Exterior", 0xE094, BitNumber(3), [416], [297], "lady-gen4"),
	TrainerData("Rich Boy Jason", "Pokemon Mansion - Exterior", 0xE094, BitNumber(2), [302], [234], "richboy-gen4"),
	TrainerData("Socialite Reina", "Pokemon Mansion - Exterior", 0xE094, BitNumber(5), [131], [234], "madame-gen4"),
	TrainerData("Gentleman Jeremy", "Pokemon Mansion - Exterior", 0xE094, BitNumber(4), [128], [220], "gentleman-gen4dp"),
	TrainerData("Artist Alexander", "Pokemon Mansion - Exterior", 0xE095, BitNumber(1), [235], [158], "artist-gen4"),
	TrainerData("Gambler Nicky", "Pokemon Mansion - Exterior", 0xE0B3, BitNumber(0), [430], [326], "gambler"),
	TrainerData("Beauty Elle", "Pokemon Mansion - Exterior", 0xE0B3, BitNumber(4), [232], [220], "beauty-gen4dp"),
	TrainerData("Lady Celeste", "Pokemon Mansion - Exterior", 0xE0F9, BitNumber(5), [189], [234], "lady-gen4"),
	TrainerData("Socialite Scarlet", "Pokemon Mansion - Exterior", 0xE0F9, BitNumber(4), [143], [189], "madame-gen4"),
	TrainerData("Policeman Caleb", "Pokemon Mansion - Exterior", 0xE096, BitNumber(6), [59], [220], "policeman-gen4"),
	TrainerData("Rich Boy Liam", "Pokemon Mansion - Exterior", 0xE095, BitNumber(3), [199], [157], "richboy-gen4"),
	TrainerData("Waiter Affogato (Left Side)", "Pokemon Mansion", 0xE0FA, BitNumber(3), [474], [287], "waiter-gen4dp"),
	TrainerData("Waiter Doppio (Right Side)", "Pokemon Mansion", 0xE0FA, BitNumber(1), [436], [184], "waiter-gen4dp"),
	TrainerData("Maid Latte (Left Side)", "Pokemon Mansion", 0xE0FA, BitNumber(4), [242], [189], "maid-gen4"),
	TrainerData("Maid Mocha (Right Side)", "Pokemon Mansion", 0xE0FA, BitNumber(2), [429], [275], "maid-gen4"),
	TrainerData("Gentleman Butler", "Pokemon Mansion", 0xE031, BitNumber(3), [149], [220], "gentleman-gen4dp"),
	TrainerData("Policeman Danny", "Pokemon Mansion - Exterior", None, BitNumber(None), [59,229,110,411,310,306], [270,270,270,270,270,270], "policeman-gen4", superboss = True),
	TrainerData("Galacticf Luna", "Clamberclaw Cliffs", 0xE092, BitNumber(2), [34,197,36,184,217,337], [255,234,158,299,230,210], "galacticgruntf"),
	TrainerData("Galactic Valetudo", "Clamberclaw Cliffs", 0xE092, BitNumber(7), [34,199,289,230,405,99], [214,230,234,230,221,203], "galacticgrunt", optional = True),
	TrainerData("Galacticf Terra", "Clamberclaw Cliffs", 0xE092, BitNumber(3), [205,389,426,409,321,351], [184,194,211,213,234,270], "galacticgruntf"),
	TrainerData("Galacticf Venus", "Clamberclaw Cliffs", 0xE093, BitNumber(1), [435,3,242,350,429,229], [270,281,202,202,203,230], "galacticgruntf"),
	TrainerData("Galactic Squad Leda", "Clamberclaw Cliffs", 0xE093, BitNumber(3), [110,463,85,254,423,59], [255,234,230,214,187,265], "galacticsquad"),
	TrainerData("Galacticf Amalthia", "Clamberclaw Cliffs", 0xE0C7, BitNumber(2), [324,213,335,212,342,282], [217,234,326,265,326,270], "galacticgruntf"),
	TrainerData("Galactic Metis", "Clamberclaw Cliffs", 0xE0C7, BitNumber(1), [76,416,94,436,463,62], [230,255,281,150,272,158], "galacticgrunt"),
	TrainerData("Galactic Themisto", "Clamberclaw Cliffs", 0xE092, BitNumber(4), [47,97,257,73,338,354], [230,234,217,281,214,203], "galacticgrunt"),
	TrainerData("Galacticf Dia", "Clamberclaw Cliffs", 0xE093, BitNumber(0), [196,1413,121,36,93,82], [203,217,230,202,255,230], "galacticgruntf", optional = True),
	TrainerData("Galactic Thebe", "Clamberclaw Cliffs", 0xE094, BitNumber(1), [317,468,286,442,51,181], [214,149,192,213,201,157], "galacticgrunt"),
	TrainerData("Galactic Squad Himalia", "Clamberclaw Cliffs", 0xE093, BitNumber(7), [49,359,306,121,18,105], [230,213,275,270,204,258], "galacticsquad"),
	TrainerData("Galactic Callisto", "Clamberclaw Cliffs", 0xE092, BitNumber(5), [476,332,65,195,6,68], [163,230,198,154,203,157], "galacticgrunt"),
	TrainerData("Galacticf Europa", "Clamberclaw Cliffs", 0xE093, BitNumber(4), [31,478,365,346,124,80], [265,267,234,276,207,255], "galacticgruntf"),
	TrainerData("Galactic Pluto", "Clamberclaw Cliffs", 0xE093, BitNumber(2), [362,24,448,356,131,105], [210,276,213,234,234,258], "galacticgrunt"),
	TrainerData("Galactic Ganymede", "Clamberclaw Cliffs", 0xE093, BitNumber(6), [91,208,94,202,297,143], [212,278,281,234,158,255], "galacticgrunt"),
	TrainerData("Galacticf Io", "Clamberclaw Cliffs", 0xE1E0, ExactNumber(1), [168,467,452,373,94,474], [230,221,326,188,281,251], "galacticgruntf"),
	TrainerData("Commander Jupiter", "Clamberclaw Cliffs", 0xE1E0, ExactNumber(2), [128,130,462,308,377,465], [214,186,276,270,157,276], "jupiter", boss = True),
	TrainerData("Galactic Mercury", "Celestic Town", 0xE015, BitNumber(7), [344,430,169,472,469], [214,270,221,188,195], "galacticgrunt"),
	TrainerData("Leader Cyrus", "Celestic Town", 0xDE88, ExactNumber(1), [3386,376,3479,245,373,461], [157,270,158,213,197,230], "cyrus", boss = True),
	TrainerData("Barry #5 - Turtwig", "Canalave City", 0xDE90, ExactNumber(1), [398,424,466,289,254,392], [157,251,268,214,204,241], "barry", levelCap = 65, starter = TURTWIG),
	TrainerData("Barry #5 - Chimchar", "Canalave City", 0xDE90, ExactNumber(1), [398,424,466,289,260,395], [157,251,268,214,187,270], "barry", levelCap = 65, starter = CHIMCHAR),
	TrainerData("Barry #5 - Piplup", "Canalave City", 0xDE90, ExactNumber(1), [398,424,466,289,257,389], [157,251,268,214,157,270], "barry", levelCap = 65, starter = PIPLUP),
	TrainerData("Galacticf Calypso", "Iron Island", 0xE0C2, BitNumber(5), [423,141,205,351], [234,187,222,268], "galacticgruntf",
		doublePartner = TrainerData("Galactic Thalassa", "Iron Island", 0xE0C2, BitNumber(4), [437,348,139,73], [278,327,187,234], "galacticgrunt")),
	TrainerData("Galacticf Despina", "Iron Island", 0xE0C9, BitNumber(1), [49,475,464,227], [213,326,185,244], "galacticgruntf",
		doublePartner = TrainerData("Galacticf Galatea", "Iron Island", 0xE0C9, BitNumber(0), [36,282,468,241], [234,270,221,214], "galacticgruntf")),
	TrainerData("Galactic Hippocamp", "Iron Island", 0xE0C3, BitNumber(1), [450,346,230,121], [237,217,234,157], "galacticgrunt", path = 1,
		doublePartner = TrainerData("Galactic Psamanthe", "Iron Island", 0xE0C9, BitNumber(2), [476,332,445,222], [192,230,213,187], "galacticgrunt", path = 1)),
	TrainerData("Galactic Sao", "Iron Island", 0xE0B0, BitNumber(1), [357,421,78,203], [184,255,214,270], "galacticgrunt", path = 1,
		doublePartner = TrainerData("Galactic Neso", "Iron Island", 0xE0AE, BitNumber(1), [323,103,338,351], [185,265,149,298], "galacticgrunt", path = 1)),
	TrainerData("Galacticf Halimede", "Iron Island", 0xE0C1, BitNumber(6), [416,409,199,477], [215,309,221,198], "galacticgruntf", path = 2,
		doublePartner = TrainerData("Galactic Proteus", "Iron Island", 0xE0B8, BitNumber(4), [80,365,132,376], [157,278,217,278], "galacticgrunt", path = 2)),
	TrainerData("Galactic Naid", "Iron Island", 0xE0B9, BitNumber(2), [148,272,283,340], [311,221,267,187], "galacticgrunt", path = 2,
		doublePartner = TrainerData("Galacticf Nereid", "Iron Island", 0xE0B9, BitNumber(3), [211,87,367,368], [214,243,270,243], "galacticgruntf", path = 2)),
	TrainerData("Galacticf Larissa", "Iron Island", 0xE0BA, BitNumber(4), [337,436,344,462], [199,269,198,242], "galacticgruntf",
		doublePartner = TrainerData("Galacticf Laomedeia", "Iron Island", 0xE0BB, BitNumber(0), [330,142,472,178], [188,157,237,270], "galacticgruntf")),
	TrainerData("Galactic Triton", "Iron Island", 0xDEC4, ExactNumber(2), [119,230,99,395], [265,197,221,214], "galacticgrunt", boss = True,
		doublePartner = TrainerData("Galactic Neptune", "Iron Island", 0xDEC4, ExactNumber(2), [121,131,260,369], [266,234,187,187], "galacticgrunt", boss = True)),
	TrainerData("Sailor Cesar", "Canalave Gym", 0xDED0, BitNumber(0), [437,319,226,462,369], [214,270,186,267,266], "sailor"),
	TrainerData("Scientist Bill", "Canalave Gym", 0xDED0, BitNumber(0), [101,142,436,409,233], [269,221,158,238,158], "scientist-gen4dp"),
	TrainerData("Idol Skylar", "Canalave Gym", 0xDED0, BitNumber(0), [330,306,227,12,472,205], [188,234,244,244,213,210], "idol"),
	TrainerData("Hiker David", "Canalave Gym", 0xDED0, BitNumber(0), [297,206,76,302,181], [273,221,275,234,157], "hiker-gen4"),
	TrainerData("Leader Byron", "Canalave Gym", 0xD076, BitNumber(5), [376,365,149,462,208,385], [191,234,158,210,270,157], "byron", boss = True, levelCap = 74),
	TrainerData("Galactic Pan", "Lake Valor", 0xE0BB, BitNumber(7), [47,454,423,272], [192,281,234,265], "galacticgrunt",
		doublePartner = TrainerData("Galactic Daphnis", "Lake Valor", 0xE0BF, BitNumber(1), [55,226,283,489], [243,186,270,267], "galacticgrunt")),
	TrainerData("Galactic Epimetheus", "Lake Valor", 0xE0C8, BitNumber(4), [45,457,455,110], [158,221,214,158], "galacticgrunt",
		doublePartner = TrainerData("Galactic Prometheus", "Lake Valor", 0xE0C1, BitNumber(7), [219,338,275,71], [275,214,270,265], "galacticgrunt")),
	TrainerData("Galacticf Phoebe", "Lake Valor", 0xE0BC, BitNumber(0), [94,426,2479], [198,204,196], "galacticgruntf",
		doublePartner = TrainerData("Galactic Iapetus", "Lake Valor", 0xE0BB, BitNumber(5), [205,91,211,101,463], [278,214,220,220,251], "galacticgrunt")),
	TrainerData("Galactic Enceladus", "Lake Valor", 0xE0BA, BitNumber(2), [121,473,131], [275,213,270], "galacticgrunt",
		doublePartner = TrainerData("Galacticf Mimas", "Lake Valor", 0xE0B8, BitNumber(5), [460,36,351,478], [217,326,270,234], "galacticgruntf")),
	TrainerData("Galacticf Pandora", "Lake Valor", 0xE0BB, BitNumber(2), [130,416,169], [270,244,281], "galacticgruntf",
		doublePartner = TrainerData("Galacticf Dione", "Lake Valor", 0xE0BA, BitNumber(6), [112,115,127], [275,214,286], "galacticgruntf")),
	TrainerData("Galactic Atlas", "Lake Valor", 0xE0C8, BitNumber(3), [323,76,103], [157,187,194], "galacticgrunt",
		doublePartner = TrainerData("Galactic Hyperion", "Lake Valor", 0xE0AE, BitNumber(0), [189,6,93], [275,195,275], "galacticgrunt")),
	TrainerData("Galacticf Tethys", "Lake Valor", 0xE0BE, BitNumber(2), [55,87,186,139], [270,232,157,187], "galacticgruntf",
		doublePartner = TrainerData("Galacticf Rhea", "Lake Valor", 0xE0BE, BitNumber(1), [407,105,212,368], [255,258,158,157], "galacticgruntf")),
	TrainerData("Commander Saturn", "Lake Valor", 0xDEC0, ExactNumber(3), [482,488,321,373,376], [270,234,157,270,157], "saturn", boss = True,
		doublePartner = TrainerData("Galactic Titan", "Lake Valor", 0xDEC0, ExactNumber(3), [297,130,208,143], [273,186,185,234], "galacticgrunt", boss = True)),
	TrainerData("Galactic Mercury", "Lake Verity", 0xE0BE, BitNumber(3), [432,338,351,94], [151,157,210,157], "galacticgrunt",
		doublePartner = TrainerData("Galacticf Venus", "Lake Verity", 0xE0BF, BitNumber(2), [323,3,435,455], [191,270,157,265], "galacticgruntf")),
	TrainerData("Galactic Luna", "Lake Verity", 0xE0AD, BitNumber(2), [337,478,36,282], [234,198,158,210], "galacticgrunt",
		doublePartner = TrainerData("Galactic Pluto", "Lake Verity", 0xE0AD, BitNumber(6), [460,221,471,365], [184,203,157,286], "galacticgrunt")),
	TrainerData("Galactic Squad Deimos", "Lake Verity", 0xDEC0, ExactNumber(4), [235,229,178,442,97,452], [234,234,270,210,234,200], "galacticsquad",
		doublePartner = TrainerData("Galactic Squad Phobos", "Lake Verity", 0xDEC0, ExactNumber(4), [330,332,472,430,429,337], [255,230,188,234,234,157], "galacticsquad")),
	TrainerData("Commander Mars", "Lake Verity", 0xDEC0, ExactNumber(5), [450, 445,260,385,38,481], [214,188,187,157,270,234], "mars", boss = True,
		doublePartner = TrainerData("Galacticf Terra", "Lake Verity", 0xDEC0, ExactNumber(5), [462,5479,389,344], [269,300,270,158], "galacticgruntf", boss = True)),
	TrainerData("Skier Edward", "Route 216", 0xE09B, BitNumber(1), [221,22,203,234], [275,234,272,234], "skier"),
	TrainerData("Skier Kaitlyn", "Route 216", 0xE09B, BitNumber(2), [225,335,18,182], [275,189,188,189], "skierf-gen4dp"),
	TrainerData("Blackbelt Philip", "Route 216", 0xE0AA, BitNumber(0), [57,352,122,83], [234,266,234,259], "blackbelt-gen4dp"),
	TrainerData("Guitarist Garrett", "Route 216", 0xE09A, BitNumber(5), [101,295,124,441], [269,234,275,251], "guitarist-gen4"),
	TrainerData("Ace Trainer Laura", "Route 216", 0xE09A, BitNumber(6), [362,154,241,448,373], [255,234,234,234,234], "acetrainersnowf"),
	TrainerData("Ace Trainer Olivia", "Route 217", 0xE09B, BitNumber(5), [260,164,53,478,124,395], [187,234,251,230,230,234], "acetrainersnowf", optional = True),
	TrainerData("Ninja Boy Ethan", "Route 217", 0xE09C, BitNumber(3), [1413,110,398,356,471,352], [230,281,214,234,234,255], "ninjaboy", optional = True),
	TrainerData("Skier Madison", "Route 217", 0xE09C, BitNumber(0), [351,441,295,432,28,196], [270,234,234,234,234,234], "skierf-gen4dp", optional = True),
	TrainerData("Blackbelt Luke", "Route 217", 0xE09C, BitNumber(4), [83,210,424,297,475,365], [259,234,234,273,234,234], "blackbelt-gen4dp", optional = True),
	TrainerData("Ace Trainer Dalton", "Route 217", 0xE09B, BitNumber(4), [392,217,277,473,103,230], [234,273,273,270,194,234], "acetrainersnow", optional = True),
	TrainerData("Ninja Boy Matthew", "Route 217", 0xE09C, BitNumber(2), [292,106,461,463,94,22], [275,272,221,272,281,234], "ninjaboy", optional = True),
	TrainerData("Skier Bjorn", "Route 217", 0xE09B, BitNumber(7), [254], [0], "skier", optional = True),
	TrainerData("Skier Shawn", "Route 217", 0xE09B, BitNumber(6), [225,206,18,260,335,182], [275,205,244,217,202,217], "skier", optional = True),
	TrainerData("Veteran Anton", "Snowpoint Gym", 0xE0F1, BitNumber(3), [473,121,376,321,135], [214,270,234,234,234], "veteran-gen4", optional = True),
	TrainerData("Ace Trainer Tenzing", "Snowpoint Gym", 0xE0F1, BitNumber(4), [362,365,65,3479,248], [214,186,275,234,234], "acetrainersnow"),
	TrainerData("Skier Mirabelle", "Snowpoint Gym", 0xE0AB, BitNumber(4), [242,478,351,122,467], [211,234,270,234,267], "skierf-gen4dp", optional = True),
	TrainerData("Skier Anas", "Snowpoint Gym", 0xE0AB, BitNumber(5), [80,221,234,124,395], [234,203,158,275,243], "skier", optional = True),
	TrainerData("Skier Savannah", "Snowpoint Gym", 0xE0AB, BitNumber(6), [28,199,471,59,73], [270,234,234,234,281], "skierf-gen4dp", optional = True),
	TrainerData("Ace Trainer Alicia", "Snowpoint Gym", 0xE0AB, BitNumber(7), [91,282,461,38,149], [270,234,275,270,234], "acetrainersnowf"),
	TrainerData("Leader Candice", "Snowpoint Gym", 0xD076, BitNumber(6), [478,131,144,378,473,436], [275,157,195,158,234,158], "candice", boss = True, levelCap = 84),
	TrainerData("Guitarist Cole", "Route 222", 0xE09F, BitNumber(7), [295,103,76], [157,157,157], "guitarist-gen4",
		doublePartner = TrainerData("BirdKeeper Nicola", "Route 222", 0xE0C7, BitNumber(4), [334,441,18], [265,265,270], "birdkeeper-gen4dp")),
	TrainerData("Pokefan June", "Route 222", 0xE09F, BitNumber(6), [185,36,321,124,136], [275,189,158,265,270], "pokefanf-gen4"),
	TrainerData("Rich Boy Trey", "Route 222", 0xE0B3, BitNumber(5), [6,275,326], [92,92,92], "richboy-gen4",
		doublePartner = TrainerData("Policeman Thomas", "Route 222", 0xE0B3, BitNumber(7), [59,310,210], [191,267,189], "policeman-gen4")),
	TrainerData("Belle & Pa Scout & Atticus", "Route 222", 0xE09F, BitNumber(4), [128,241,181,182,78], [266,214,191,232,191], "bellepa"),
	TrainerData("Aroma Lady Carolina", "Route 222", 0xE0A0, BitNumber(0), [324,114,45,455], [158,184,184,184], "aromalady"),
	TrainerData("Pokefan Sheen", "Route 222", 0xE0A0, BitNumber(1), [25,162,122,237], [236,275,269,232], "pokefan-gen4"),
	TrainerData("Sailor Jack", "Route 222", 0xE0B4, BitNumber(1), [279,357,20], [275,188,273], "sailor",
		doublePartner = TrainerData("Lady Rose", "Route 222", 0xE0B6, BitNumber(7), [105,134,31], [258,187,265], "lady-gen4")),
	TrainerData("Interviewers Barbara & Walter", "Route 222", 0xE0A0, BitNumber(6), [102,426,51,85,82], [265,158,270,232,275], "interviewers"),
	TrainerData("Socialite Alec", "Route 222", 0xE09F, BitNumber(5), [182,135,196], [275,242,267], "madame-gen4",
		doublePartner = TrainerData("Gentleman Luther", "Route 222", 0xE0A0, BitNumber(4), [289,34,199], [221,221,158], "gentleman-gen4dp")),
	TrainerData("TuberF Holly", "Route 222", 0xE0B7, BitNumber(1), [223,363,98,418], [230,217,217,230], "tuberf", optional = True),
	TrainerData("Pokefan Liz", "Sunyshore Gym", 0xDE68, ExactNumber(1), [130,80,468], [214,234,157], "pokefanf-gen4",
		doublePartner = TrainerData("Pokefan RJ", "Sunyshore Gym", 0xDE68, ExactNumber(1), [105,310,26], [258,157,157], "pokefan-gen4")),
	TrainerData("Clown Forrest", "Sunyshore Gym", 0xDE68, ExactNumber(2), [476,199,122,94,101], [191,209,270,270,211], "clown"),
	TrainerData("Pokekid Maggie", "Sunyshore Gym", 0xDE68, ExactNumber(3), [426,354,25,40,224], [207,247,236,157,157], "pokekid"),
	TrainerData("Cowgirl Meghan", "Sunyshore Gym", 0xDE68, ExactNumber(4), [59,181,241,468,326,210], [286,270,208,221,198,251], "cowgirl"),
	TrainerData("Worker Hugh", "Sunyshore Gym", 0xDE68, ExactNumber(5), [232,171,464], [275,234,187], "worker-gen4",
		doublePartner = TrainerData("Waiter Reynolds", "Sunyshore Gym", 0xDE68, ExactNumber(5), [135,462,1479], [275,184,208], "waiter-gen4dp"),),
	TrainerData("Psychic Destiny", "Sunyshore Gym", 0xDE68, ExactNumber(6), [197,196,135,429,475,178], [234,327,157,270,234,270], "psychic-gen4"),
	TrainerData("Gambler Ace", "Sunyshore Gym", 0xDE68, ExactNumber(7), [302,306,206,430,97], [213,275,157,221,213], "gambler"),
	TrainerData("Guitarist Preston", "Sunyshore Gym", 0xDE68, ExactNumber(8), [76,428,405,359,203,4479], [275,251,270,327,272,221], "guitarist-gen4"),
	TrainerData("Leader Volkner", "Sunyshore Gym", 0xD076, BitNumber(7), [260,145,462,230,243,466], [187,157,189,157,157,270], "volkner", boss = True, levelCap = 100),
	TrainerData("Veteran Grant", "Oreburgh Gate", 0xE0A8, BitNumber(0), [442,89,417,262,185], [212,234,202,275,220], "veteran-gen4", optional = True),
	TrainerData("Worker Holden", "Fuego Ironworks", 0xE0F3, BitNumber(5), [303,208,257,59,78], [275,208,270,234,270], "worker-gen4", optional = True),
	TrainerData("Worker Conrad", "Fuego Ironworks", 0xE0F3, BitNumber(6), [229,479,9,454,448], [213,275,210,230,297], "worker-gen4", optional = True),
	TrainerData("Worker Dillan", "Fuego Ironworks", 0xE0F3, BitNumber(4), [227,68,6,306,323], [234,234,195,189,217], "worker-gen4", optional = True),
	TrainerData("Ace Trainer Blake", "Route 216", 0xE09A, BitNumber(4), [424,137,352,143], [0, 0, 0, 0], "acetrainersnow", optional = True),
	TrainerData("Skier Bradley", "Route 216", 0xE09B, BitNumber(0), [361,220,459], [0, 0, 0], "skier", optional = True),
	TrainerData("Ace Trainer Maria", "Route 216", 0xE09A, BitNumber(7), [55,78,185,22], [0, 0, 0, 0], "acetrainersnowf", optional = True),
	TrainerData("Skier Andrea", "Route 216", 0xE09A, BitNumber(3), [108,110,153,64], [0, 0, 0, 0], "skierf-gen4dp", optional = True),
	TrainerData("Pkmn Ranger Allison", "Route 212", 0xE096, BitNumber(0), [57], [220], "pokemonrangerf-gen4", optional = True),
	TrainerData("Pkmn Ranger Jeffrey", "Route 212", 0xE095, BitNumber(7), [59], [217], "pokemonranger-gen4", optional = True),
	TrainerData("Pkmn Ranger Taylor", "Route 212", 0xE095, BitNumber(6), [260], [230], "pokemonranger-gen4", optional = True),
	TrainerData("SwimmerF Wang", "Route 220", 0xE0A2, BitNumber(1), [230,134,283,87], [297,234,275,158], "swimmerf-gen4dp", optional = True),
	TrainerData("SwimmerF Wang", "Route 220", 0xE0A2, BitNumber(2), [230,134,283,87], [243,234,230,189], "swimmerf-gen4dp", optional = True),
	TrainerData("SwimmerF Wang", "Route 220", 0xE09E, BitNumber(5), [230,134,283,87], [220,234,275,186], "swimmerf-gen4dp", optional = True),
	TrainerData("SwimmerF Wang", "Route 220", 0xE09E, BitNumber(4), [230,134,283,87], [297,234,275,234], "swimmerf-gen4dp", optional = True),
	TrainerData("Sis and Bro Dora & Diego", "Route 221", 0xE09E, BitNumber(6), [57,419,94,190,37], [230,450,442,166,261], "sisandbro", optional = True),
	TrainerData("Fisherman Greg", "Route 221", 0xE09F, BitNumber(0), [9,36,130,260,214,149], [157,158,186,221,203,157], "fisherman-gen4", optional = True),
	TrainerData("Collector Gerald", "Wayward Cave", 0xE0C1, BitNumber(3), [466,279,308], [158,221,203], "collector", optional = True,
		doublePartner = TrainerData("Clown Bob", "Wayward Cave", 0xE0B9, BitNumber(7), [426,195,57], [189,187,92], "clown", optional = True)),
	TrainerData("Camper Parker", "Wayward Cave", 0xE0B9, BitNumber(4), [289,352], [189,270], "camper",  optional = True,
		doublePartner = TrainerData("Picnicker Tori", "Wayward Cave", 0xE0C3, BitNumber(2), [12,193], [275,275], "picnicker", optional = True)),
	TrainerData("Lass Cassidy", "Wayward Cave", 0xE0C2, BitNumber(2), [407,139], [230,205], "lass-gen4dp",  optional = True,
		doublePartner = TrainerData("Youngster Butch", "Wayward Cave", 0xE0C8, BitNumber(0), [227,269], [158,213], "youngster-gen4dp", optional = True)),
	TrainerData("Bug Catcher Adalbert", "Wayward Cave", 0xE0C3, BitNumber(3), [414,267], [213,287], "bugcatcher-gen4dp",  optional = True,
		doublePartner = TrainerData("Camper Mike", "Wayward Cave", 0xE0C3, BitNumber(4), [342,329], [189,270], "camper", optional = True)),
	TrainerData("Hiker Reginald", "Wayward Cave", 0xE0C2, BitNumber(6), [262,234,178], [275,202,208], "hiker-gen4",  optional = True,
		doublePartner = TrainerData("Hiker Lorenzo", "Wayward Cave", 0xE0C2, BitNumber(7), [122,327,448], [270,217,326], "hiker-gen4", optional = True)),
	TrainerData("Castle Valet Darach", "Wayward Cave", 0xDEC2, ExactNumber(2), [475,395,244], [326,217,202], "darach",  optional = True,
		doublePartner = TrainerData("Lady Caitlin", "Wayward Cave", 0xDEC2, ExactNumber(2), [282,65,376], [232,267,270], "caitlin", optional = True)),
	TrainerData("Scientist Caliban", "Veilstone Warehouse", 0xE0CE, BitNumber(3), [260,411,295,317,302,130], [214,230,270,286,234,186], "scientist-gen4dp"),
	TrainerData("Galacticf Portia", "Veilstone Warehouse", 0xE0CD, BitNumber(3), [168,376,224], [230,157,270], "galacticgruntf", 
		doublePartner = TrainerData("Galacticf Cressida", "Veilstone Warehouse", 0xE0CD, BitNumber(4), [148,131,233], [270,221,189], "galacticgruntf")),
	TrainerData("Galactic Trinculo", "Veilstone Warehouse", 0xE0CE, BitNumber(5), [232,463,97,184,237], [212,272,265,299,221], "galacticgrunt"),
	TrainerData("Galacticf Umbriel", "Veilstone Warehouse", 0xE0CD, BitNumber(5), [97,89,197], [209,286,234], "galacticgruntf",
		doublePartner = TrainerData("Galactic Francisco", "Veilstone Warehouse", 0xE0CD, BitNumber(6), [463,465,395], [270,270,214], "galacticgrunt")),
	TrainerData("Galacticf Miranda", "Veilstone Warehouse", 0xE0CF, BitNumber(4), [337,462,3479], [211,270,289], "galacticgruntf",
		doublePartner = TrainerData("Galactic Ferdinand", "Veilstone Warehouse", 0xE0CF, BitNumber(5), [450,260,389], [156,156,156], "galacticgrunt")),
	TrainerData("Galactic Squad Juliet", "Veilstone Warehouse", 0xE0CE, BitNumber(1), [47,464,143,89,292,282], [213,230,234,234,275,290], "galacticsquad"),
	TrainerData("Galacticf Margaret", "Veilstone Warehouse", 0xE0CD, BitNumber(7), [323,149,59], [156,234,234], "galacticgruntf",
		doublePartner = TrainerData("Galacticf Cupid", "Veilstone Warehouse", 0xE0CE, BitNumber(0), [421,468,36], [213,293,234], "galacticgruntf")),
	TrainerData("Galactic Squad Perdita", "Veilstone Warehouse", 0xE0D0, BitNumber(1), [460,134,221,2413,471], [213,234,230,204,234], "galacticsquad"),
	TrainerData("Galactic Setebos", "Veilstone Warehouse", 0xE0CE, BitNumber(7), [437,222,91,103], [270,309,292,270], "galacticgrunt", path = 1,
		doublePartner = TrainerData("Galacticf Sycorax", "Veilstone Warehouse", 0xE0CF, BitNumber(0), [429,4479], [291,290], "galacticgruntf", path = 1)),
	TrainerData("Galacticf Ariel", "Veilstone Warehouse", 0xE0CF, BitNumber(1), [131,475,242], [265,289,211], "galacticgruntf", path = 2,
		doublePartner = TrainerData("Galacticf Bianca", "Veilstone Warehouse", 0xE0CF, BitNumber(2), [437,340,134], [150,234,234], "galacticgruntf", path = 2)),
	TrainerData("Galactic Squad Mab", "Veilstone Warehouse", 0xE0CF, BitNumber(3), [115,176,334,416,31], [150,150,272,150,150], "galacticsquad"),
	TrainerData("Galacticf Rosalind", "Veilstone Warehouse", 0xE0C9, BitNumber(5), [407,173,398,338,282], [234,275,70,234,270], "galacticgruntf"),
	TrainerData("Galactic Squad Belinda", "Veilstone Warehouse", 0xE0CE, BitNumber(2), [148,303,342,212,472,452], [294,156,157,157,293,278], "galacticsquad", optional = True),
	TrainerData("Galacticf Bebhionn", "Veilstone Warehouse", 0xE0DA, BitNumber(1), [134,184,2479], [211,270,291], "galacticgruntf", optional = True),
	TrainerData("Galactic Erripaus", "Veilstone Warehouse", 0xE0DA, BitNumber(0), [437,160,80], [211,299,253], "galacticgrunt", optional = True),
	TrainerData("Galactic Janus", "Veilstone Warehouse", 0xE0DA, BitNumber(4), [436,203,476,110,103], [205,293,270,211,270], "galacticgrunt"),
	TrainerData("Galactic Oberon", "Veilstone Warehouse", 0xE0DA, BitNumber(6), [460,248,199], [270,234,234], "galacticgrunt",
		doublePartner = TrainerData("Galactic Puck", "Veilstone Warehouse", 0xE0DA, BitNumber(7), [173,220,94], [275,275,154], "galacticgrunt")),
	TrainerData("Scientist Stephano", "Veilstone Warehouse", 0xE0CE, BitNumber(4), [450,395,332,185,436], [212,214,230,270,184], "scientist-gen4dp", optional = True),
	TrainerData("Galactic Prospero", "Veilstone Warehouse", 0xE0CE, BitNumber(6), [219,409,465,475,6,477], [275,230,270,293,215,214], "galacticgrunt"),
	TrainerData("Galactic Alborix", "Galactic HQ", 0xE0DB, BitNumber(3), [227,475,317,94], [234,209,281,206], "galacticgrunt", optional = True),
	TrainerData("Galactic Skymir", "Galactic HQ", 0xE0DA, BitNumber(6), [201,356,442], [297,234,221], "galacticgrunt", optional = True),
	TrainerData("Galactic Loge", "Galactic HQ", 0xE0DA, BitNumber(5), [219,435,426], [270,270,206], "galacticgrunt", optional = True),
	TrainerData("Galactic Hyperion", "Galactic HQ", 0xE0D8, BitNumber(4), [219,338,192], [221,291,270], "galacticgrunt", path = 1,
		doublePartner = TrainerData("Galactic Prometheus", "Galactic HQ", 0xE0D8, BitNumber(5), [257,217,136], [293,71,205], "galacticgrunt", path = 1)),
	TrainerData("Galacticf Tethys", "Galactic HQ", 0xE0D9, BitNumber(6), [131,340,171], [211,187,202], "galacticgruntf", path = 2,
		doublePartner = TrainerData("Galacticf Dione", "Galactic HQ", 0xE0D9, BitNumber(0), [437,199,366], [269,234,226], "galacticgruntf", path = 2)),
	TrainerData("Galactic Titan", "Galactic HQ", 0xE0DB, BitNumber(4), [143,208,321,297,149,389], [202,278,205,221,289,205], "galacticgrunt"),
	TrainerData("Galactic Epimetheus", "Galactic HQ", 0xE0D0, BitNumber(4), [306,217,297], [270,234,234], "galacticgrunt",
		doublePartner = TrainerData("Galacticf Pandora", "Galactic HQ", 0xE0D0, BitNumber(5), [97,442,317], [205,312,286], "galacticgruntf")),
	TrainerData("Galactic Enceladus", "Galactic HQ", 0xE0D0, BitNumber(7), [460,365,473], [270,205,293], "galacticgrunt", path = 1,
		doublePartner = TrainerData("Galacticf Mimas", "Galactic HQ", 0xE0D0, BitNumber(6), [73,131,471], [215,221,234], "galacticgruntf", path = 1)),
	TrainerData("Galacticf Daphnis", "Galactic HQ", 0xE0D8, BitNumber(7), [241,181,326], [292,202,211], "galacticgruntf", path = 2,
		doublePartner = TrainerData("Galacticf Pan", "Galactic HQ", 0xE0D8, BitNumber(6), [28,275,295], [214,278,270], "galacticgruntf", path = 2)),
	TrainerData("Galactic Kari", "Galactic HQ", 0xE0DB, BitNumber(1), [450,282,139,195,82], [286,230,187,302,275], "galacticgrunt", path = 1),
	TrainerData("Galactic Geirrod", "Galactic HQ", 0xE0DA, BitNumber(2), [454,47,423], [281,234,234], "galacticgrunt", path = 1,
		doublePartner = TrainerData("Galactic Greip", "Galactic HQ", 0xE0DA, BitNumber(3), [148,134,9], [270,299,289], "galacticgrunt", path = 1)),
	TrainerData("Galactic Iapetus", "Galactic HQ", 0xE0D1, BitNumber(1), [344,476,205], [214,70,232], "galacticgrunt", path = 2,
		doublePartner = TrainerData("Galacticf Phoebe", "Galactic HQ", 0xE0D8, BitNumber(3), [5479,426,355], [292,202,230], "galacticgruntf", path = 2)),
	TrainerData("Galactic Atlas", "Galactic HQ", 0xE0D1, BitNumber(0), [323,76,68,465,214], [298,187,206,209,201], "galacticgrunt", path = 2, optional = True),
	TrainerData("Galacticf Rhea", "Galactic HQ", 0xE0D9, BitNumber(7), [437,115,154,350,423], [205,294,291,202,205], "galacticgruntf", path = 2),
	TrainerData("Galacticf Uranus", "Galactic HQ", 0xE0D0, BitNumber(0), [144,91,245,208,282,471], [215,214,234,212,234,230], "galacticgruntf"),
	TrainerData("Leader Cyrus", "Galactic HQ", 0xDF4C, ExactNumber(1), [2386,409,485,379,477,486], [234,70,158,234,70,278], "cyrus"),
	TrainerData("Galactic Io", "Galactic HQ", 0xDF4C, ExactNumber(2), [323,241,452,373,474,467], [270,278,294,215,290,292], "galacticgrunt"),
	TrainerData("Commander Saturn", "Galactic HQ", 0xDFF5, BitNumber(5), [480,145,376,112,321,488], [157,215,157,275,234,234], "saturn", boss = True),
	TrainerData("Galactic Ganymede", "Mount Coronet - Room 1", 0xE0CB, BitNumber(4), [208,328,82], [278,275,278], "galacticgrunt",
		doublePartner = TrainerData("Galacticf Halimede", "Mount Coronet - Room 1", 0xE0CB, BitNumber(3), [199,416,409], [217,217,270], "galacticgruntf")),
	TrainerData("Galacticf Squad Phobos", "Mount Coronet - Room 1", 0xE0CB, BitNumber(5), [330,337,430,332,452,472], [213,234,255,275,213,230], "galacticsquad"),
	TrainerData("Galacticf Squad Deimos", "Mount Coronet - Room 1", 0xE0CC, BitNumber(5), [235,97,229,442,45,51], [275,157,253,157,221,275], "galacticsquad", optional = True),
	TrainerData("Galacticf Despina", "Coronet Highlands - Outside 1", 0xE0C9, BitNumber(3), [203,78,277], [214,234,272], "galacticgruntf",
		doublePartner = TrainerData("Galacticf Bianca", "Coronet Highlands - Outside 1", 0xE0C9, BitNumber(4), [28,71,424], [234,234,234], "galacticgruntf")),
	TrainerData("Galactic Ferdinand", "Coronet Highlands - Outside 1", 0xE0C9, BitNumber(6), [411,319,210,128,3], [234,270,234,234,234], "galacticgrunt", path = 1),
	TrainerData("Galacticf Rosalind", "Coronet Highlands - Outside 1", 0xE0C9, BitNumber(5), [407,173,398,338,282], [234,275,70,234,270], "galacticgruntf", path = 2),
	TrainerData("Galactic Squad Perdita", "Coronet Highlands - Outside 1", 0xE0CA, BitNumber(5), [471,135,134,432,448,359], [230,234,234,234,234,234], "galacticsquad", optional = True),
	TrainerData("Galactic Valetudo", "Coronet Highlands - Outside 1", 0xE0CA, BitNumber(0), [234,463,395,34,475], [234,272,234,281,234], "galacticgrunt"),
	TrainerData("Galactic Cupid", "Coronet Highlands - Outside 1", 0xE0CA, BitNumber(1), [45,468,36], [234,234,158], "galacticgrunt", path = 1,
		doublePartner = TrainerData("Galacticf Cressida", "Coronet Highlands - Outside 1", 0xE0C9, BitNumber(7), [474,131,217], [234,221,272], "galacticgruntf", path = 1)),
	TrainerData("Galacticf Cordelia", "Coronet Highlands - Outside 1", 0xE0CA, BitNumber(2), [477,103,115,31,260,131], [234,270,234,281,234,265], "galacticgruntf", path = 2),
	TrainerData("Galactic Puck", "Coronet Highlands - Outside 1", 0xE0CF, BitNumber(7), [173,220,94], [275,275,154], "galacticgrunt", optional = True),
	TrainerData("Galactic Oberon", "Coronet Highlands - Outside 1", 0xDF4C, ExactNumber(3), [289,248,365,286,448,26], [214,234,217,213,270,191], "galacticgrunt",
		doublePartner = TrainerData("Galacticf Titania", "Coronet Highlands - Outside 1", 0xDF4C, ExactNumber(3), [468,334,178,189,251,469], [188,188,230,234,234,213], "galacticgruntf")),
	TrainerData("Galactic Proteus", "Coronet Highlands - Room 1", 0xE0CA, BitNumber(3), [132,53,392,97,461,235], [154,157,154,213,230,217], "galacticgrunt"),
	TrainerData("Galacticf Laomedeia", "Coronet Highlands - Room 1", 0xE0CA, BitNumber(4), [131,78,149], [0,0,0], "galacticgruntf", optional = True),
	TrainerData("Galacticf Larissa", "Coronet Highlands - Room 1", 0xE0CA, BitNumber(6), [435,436,442,233,110], [255,234,213,234,193], "galacticgruntf"),
	TrainerData("Galacticf Terra", "Coronet Highlands - Room 1", 0xDF4C, ExactNumber(4), [9,206,257,389,405,376], [186,265,270,208,270,213], "galacticgruntf",
		doublePartner = TrainerData("Galactic Luna", "Coronet Highlands - Room 1", 0xDF4C, ExactNumber(4), [291,426,169,227,373,337], [230,70,265,157,311,234], "galacticgrunt")),
	TrainerData("Galacticf Europa", "Coronet Highlands - Outside 2", 0xE0CA, BitNumber(7), [221,465,365,73,478], [234,296,234,281,234], "galacticgruntf"),
	TrainerData("Galactic Pluto", "Coronet Highlands - Outside 2", 0xE0CB, BitNumber(0), [302,461,121,208,85,171], [234,270,265,217,272,234], "galacticgrunt"),
	TrainerData("Galactic Prospero", "Coronet Highlands - Outside 2", 0xE0CB, BitNumber(6), [36,65,206,254,351,38], [234,270,234,234,157,270], "galacticgrunt"),
	TrainerData("Galactic Squad Amalthia", "Coronet Highlands - Outside 2", 0xE0CC, BitNumber(6), [373,128,59,18,24], [188,214,270,270,213], "galacticsquad", path = 1),
	TrainerData("Galacticf Miranda", "Coronet Highlands - Outside 2", 0xE0CB, BitNumber(2), [242,362,473,143,101], [234,210,270,270,270], "galacticgruntf", path = 2),
	TrainerData("Galacticf Angrboda", "Coronet Highlands - Outside 2", 0xE0DB, BitNumber(2), [40,442,80,132,286], [71,210,208,310,241], "galacticgruntf", path = 3),
	TrainerData("Galacticf Ariel", "Coronet Highlands - Outside 2", 0xE0CB, BitNumber(1), [196,295,154], [234,234,234], "galacticgruntf"),
	TrainerData("Galacticf Umbriel", "Coronet Highlands - Outside 2", 0xE0CB, BitNumber(2), [197,164,124], [234,234,230], "galacticgruntf"),
	TrainerData("Galactic Callisto", "Coronet Highlands - Room 2", 0xE0CC, BitNumber(3), [121,346,82], [230,234,213], "galacticgrunt",
		doublePartner = TrainerData("Galactic Hippocamp", "Coronet Highlands - Room 2", 0xE0CC, BitNumber(4), [450,78,230], [217,265,265], "galacticgrunt")),
	TrainerData("Galactic Neptune", "Coronet Highlands - Room 2", 0xDF4C, ExactNumber(6), [395,260,160,376,131,321], [214,237,70,217,189,217], "galacticgrunt",
		doublePartner = TrainerData("Galactic Triton", "Coronet Highlands - Room 2", 0xDF4C, ExactNumber(6), [145,149,82,2479,226,130], [269,270,189,213,221,70], "galacticgrunt")),
	TrainerData("Galactic Mercury", "Spear Pillar", 0xDED0, ExactNumber(1), [432,149,94], [251,158,265], "galacticgrunt",
		doublePartner = TrainerData("Galactic Venus", "Spear Pillar", 0xDED0, ExactNumber(1), [146,3,435], [298,301,270], "galacticgrunt")),
	TrainerData("Commander Mars", "Spear Pillar", 0xDED0, ExactNumber(2), [445,142,260,385,38,380], [188,214,158,157,270,198], "mars",
		doublePartner = TrainerData("Commander Jupiter", "Spear Pillar", 0xDED0, ExactNumber(2), [130,465,462,248,377,381], [275,211,191,70,210,198], "jupiter")),
	TrainerData("Cyrus", "Distortion World", 0xDED0, BitNumber(0), [484,483,1386,461,485,486], [136,135,270,70,191,157], "cyrus"),
	TrainerData("Cyrus", "Distortion World", 0xDED0, BitNumber(0), [1487], [112], "cyrus", boss = True),
	TrainerData("SwimmerF Miranda", "Route 223", 0xE0A1, BitNumber(5), [457,489,368,199], [255,213,213,255], "swimmerf-gen4dp", optional = True),
	TrainerData("SwimmerF Aubree", "Route 223", 0xE0A1, BitNumber(6), [227,184,186,400], [213,217,213,202], "swimmerf-gen4dp", optional = True),
	TrainerData("SwimmerF Paige", "Route 223", 0xE0A1, BitNumber(7), [350,461,143,91], [202,221,205,221], "swimmerf-gen4dp", optional = True),
	TrainerData("Swimmer Wesley", "Route 223", 0xE0A0, BitNumber(7), [419,73,117,367], [213,234,265,266], "swimmer-gen4dp", optional = True),
	TrainerData("Sailor Zachariah", "Route 223", 0xE0C6, BitNumber(2), [462,68,423,121], [189,230,187,266], "sailor", optional = True),
	TrainerData("Swimmer Francisco", "Route 223", 0xE0A1, BitNumber(1), [26,279,211,248], [251,202,230,270], "swimmer-gen4dp", optional = True),
	TrainerData("SwimmerF Ledecky", "Route 223", 0xE0A1, BitNumber(3), [80,199,54], [205,202,230], "swimmerf-gen4dp"),
	TrainerData("Cameraman Matt", "Victory Road", 0xE0A7, BitNumber(1), [199,135,282,428,38,189], [158,275,255,213,158,275], "cameraman"),
	TrainerData("Roughneck Wyatt", "Victory Road", 0xE0A7, BitNumber(2), [473,373,230,466,392,197], [275,253,270,157,270,157], "roughneck-gen4"),
	TrainerData("Blackbelt Roku", "Victory Road", 0xE0A6, BitNumber(2), [302,344,430,229,248,160], [157,157,241,149,194,157], "blackbelt-gen4dp"),
	TrainerData("Beauty Jasmine", "Victory Road", 0xE0A5, BitNumber(6), [376,38,143,171,232,429], [184,191,234,213,270,268], "beauty-gen4dp"),
	TrainerData("Aroma Lady Fadel", "Victory Road", 0xE0A6, BitNumber(0), [101,184,448,469,148,328], [269,158,157,270,234,230], "aromalady"),
	TrainerData("Collector Tobias", "Victory Road", 0xE0A6, BitNumber(3), [321,389,477,474,149,59], [0,0,0,0,0,0], "collector"),
	TrainerData("Clown Julia", "Victory Road", 0xE0A6, BitNumber(5), [437,395,461,272,454,91], [234,189,268,275,270,202], "clown"),
	TrainerData("Hiker J.J Ahern", "Victory Road", 0xE0A7, BitNumber(5), [26,143,94,142,9,6], [300,221,265,217,268,249], "hiker-gen4"),
	TrainerData("Bug Catcher Ford", "Victory Road", 0xE0A7, BitNumber(3), [135,143,121,80,51,142], [275,189,234,217,232,221], "bugcatcher-gen4dp"),
	TrainerData("Ruin Maniac Greg", "Victory Road", 0xE0A6, BitNumber(6), [450,465,442,199,202,472], [187,272,234,157,217,213], "ruinmaniac"),
	TrainerData("Idol Zoe", "Victory Road", 0xE0A7, BitNumber(4), [221,193,203,201,200,427], [213,213,213,213,213,262], "idol"),
	TrainerData("Dragon Tamer Clinton", "Victory Road", 0xE0A6, BitNumber(7), [373,196,89,149,124,357], [188,196,234,205,275,255], "dragontamer"),
	TrainerData("Sinister Hooded Figure", "Pokémon League", 0xE0DD, BitNumber(2), [208,233,68,321,354,378], [205,202,157,202,157,157], "sinister", optional = True),
	TrainerData("Barry #6 - Turtwig", "Pokémon League", 0xDF7E, ExactNumber(1), [289,398,466,424,254,392], [202,306,270,275,214,298], "barry", starter = TURTWIG),
	TrainerData("Barry #6 - Chimchar", "Pokémon League", 0xDF7E, ExactNumber(1), [289,398,466,424,260,395], [202,306,270,275,187,299], "barry", starter = CHIMCHAR),
	TrainerData("Barry #6 - Piplup", "Pokémon League", 0xDF7E, ExactNumber(1), [289,398,466,424,257,389], [202,306,270,275,268,301], "barry", starter = PIPLUP),
	TrainerData("Elite Four Aaron (Permanent Rain)", "Aaron Room", 0xDFF6, BitNumber(0), [205,469,416,283,330,99], [158,195,270,275,188,157], "aaron"),
	TrainerData("Elite Four Bertha (Permanent Sandstorm)", "Bertha Room", 0xDFF6, BitNumber(1), [213,473,389,445,464,142], [234,270,234,188,158,270], "bertha"),
	TrainerData("Elite Four Flint", "Flint Room", 0xDFF6, BitNumber(2), [383,480,103,229,6,467], [203,269,157,270,195,249], "flint"),
	TrainerData("Elite Four Lucian", "Lucian Room", 0xDFF6, BitNumber(3), [151,199,94,249,488,380], [205,202,275,157,157,225], "lucian"),
	TrainerData("Champion Cynthia", "Cynthia Room", 0xDFF6, BitNumber(4), [445,490,1492,491,487,493], [275,157,270,210,234,157], "cynthia-gen4")
]