from data import POKEMON_LIST, ITEM_LIST, FORMS

SLEEP = "sleep.png"
POISON = "poison.png"
BURN = "burn.png"
FREEZE = "freeze.png"
PARALYSIS = "paralysis.png"

class PokemonData:
    def __init__(self, pokedexId, itemId, currentHp = None, maxHp = None, status = None):
        self.pokedexId = int(pokedexId) if pokedexId else 0
        self.itemId = int(itemId) if itemId else 0
        self.currentHp = int(currentHp) if currentHp is not None else None
        self.maxHp = int(maxHp) if maxHp is not None else None
        self.status = int(status) if status is not None else 0

    def getStatusImage(self):
        statusBits = [(self.status >> i) & 1 for i in range(7, -1, -1)][::-1]

        if statusBits[0] or statusBits[1] or statusBits[2]:
            return SLEEP
        elif statusBits[3] or statusBits[7]:
            return POISON
        elif statusBits[4]:
            return BURN
        elif statusBits[5]:
            return FREEZE
        elif statusBits[6]:
            return PARALYSIS
        else:
            return None

    def isValid(self):
        return ((self.pokedexId < len(POKEMON_LIST) or self.pokedexId in FORMS)
            and (self.itemId < len(ITEM_LIST))
            and (self.status <= 5 or self.status in [8,16,32,64,128])
            and (self.currentHp is None or self.currentHp < 999)
            and (self.maxHp is None or self.maxHp < 999)
        )

    def __str__(self):
        return str(self.pokedexId) + " - " + str(self.itemId)
    
    def __repr__(self):
        return str(self)

# Parse PARTY|1¤10¤1|2¤25¤2|3¤3¤0 style lines into Pokémon data
def parseLine(line):
    parsedLine = []
    pokemonList = line.split("|")[1:]
    dataType = line.split("|")[0]

    for pokemonData in pokemonList:

        # No Pokémon, most likely gap in a box
        if not pokemonData:
            parsedLine.append(None)

        # No "¤" in line : raw data, add it directly
        elif ("¤" not in pokemonData):
            parsedLine.append(pokemonData)

        # Multiple attributes, store them in PokemonData object
        elif (dataType in ["PARTY", "BOX", "DEAD", "TRAINERPARTY", "DOUBLETRAINERPARTY"]):
            parsedLine.append(PokemonData(*pokemonData.split("¤")))

    return parsedLine