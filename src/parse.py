class PokemonData:
    def __init__(self, pokedexId, itemId):
        self.pokedexId = int(pokedexId) if pokedexId else 0
        self.itemId = int(itemId) if itemId else 0

    def __str__(self):
        return self.pokedexId + " - " + self.itemId
    
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
        elif (dataType in ["PARTY", "BOX", "DEAD"]):
            parsedLine.append(PokemonData(*pokemonData.split("¤")))

    return parsedLine