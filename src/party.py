from PIL import Image

import file
from file import BACKGROUNDPRITE_FOLDER
from parse import PokemonData
from settings import SETTINGS, PARTY, BOX, DEAD

POKEMON_SPRITE_WIDTH = 80
POKEMON_SPRITE_HEIGHT = 60
ITEMS_SPRITE_SIZE = 32

ITEM_X_POSITION = 42
ITEM_Y_POSITION = 28

SPACING_X = -30
SPACING_Y = -10

# Create images from Pokémon sprites
def generatePlayerPartyImage(label, pokemonList: list[PokemonData | None], columnNumber, rowNumber, customSize = None):

    # Remove None Pokemon for custom sizes (basically don't display gaps)
    if (customSize):
        pokemonList = [pokemonData for pokemonData in pokemonList if pokemonData]

    # Initialise transparent image
    imageWidth = POKEMON_SPRITE_WIDTH * columnNumber + SPACING_X * (columnNumber - 1)
    imageHeight = POKEMON_SPRITE_HEIGHT * rowNumber + SPACING_Y * (rowNumber - 1)

    # Custom box background is enabled
    if (label == BOX and SETTINGS.isBoxBackgroundDisplayed() or label == DEAD and SETTINGS.isDeadBackgroundDisplayed()):
        backgroundImagePath = BACKGROUNDPRITE_FOLDER / f"{label}.png"

        # Cannot find background : set background transparent
        if not backgroundImagePath.exists():
            outputImage = Image.new("RGBA", (imageWidth, imageHeight), (0,0,0,0))

        else:
            # Retrieve custom background and set it as background of outputImage
            backgroundImage = Image.open(backgroundImagePath).convert("RGBA").resize((imageWidth, imageHeight), Image.NEAREST)
            outputImage = backgroundImage.copy()

    # Transparent background
    else:
        outputImage = Image.new("RGBA", (imageWidth, imageHeight), (0,0,0,0))

    # Display iteps if enabled in options
    displayItems = (label == PARTY and SETTINGS.isPartyItemSpriteDisplayed()
        or label == BOX and SETTINGS.isBoxItemSpriteDisplayed())

    # Iterate on each non-None Pokémon
    for i, pokemonData in enumerate(pokemonList):
        if pokemonData is None:
            continue

        # Retrieve and resize Pokémon sprite to 80x60 so items can appear small without sizing them down
        pokemonSpritePath = file.getPokemonSprite(pokemonData.pokedexId)
        pokemonSprite = Image.open(pokemonSpritePath).convert("RGBA").resize((POKEMON_SPRITE_WIDTH, POKEMON_SPRITE_HEIGHT), Image.NEAREST)

        # Compute Pokémon sprite position with spacing (sligh overlap between sprites so they appear closer)
        x = (i % columnNumber) * (POKEMON_SPRITE_WIDTH + SPACING_X)
        y = (i // columnNumber) * (POKEMON_SPRITE_HEIGHT + SPACING_Y)

        # Display Pokémon sprite
        outputImage.paste(pokemonSprite, (x, y), pokemonSprite)

        # Display held item
        if (displayItems and pokemonData.itemId):

            # Retrieve and display item sprite
            itemSpritePath = file.getItemSprite(pokemonData.itemId)
            itemSprite = Image.open(itemSpritePath).convert("RGBA").resize((ITEMS_SPRITE_SIZE, ITEMS_SPRITE_SIZE), Image.NEAREST)
            outputImage.paste(itemSprite, (x + ITEM_X_POSITION, y + ITEM_Y_POSITION), itemSprite)

    # Save final image in output folder
    file.safeWriteFile(outputImage, label)