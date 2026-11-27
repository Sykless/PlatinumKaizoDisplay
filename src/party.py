from PIL import Image, ImageDraw

import file
from file import BACKGROUNDPRITE_FOLDER, MISCSPRITE_FOLDER
from parse import PokemonData
from settings import SETTINGS, PARTY, BOX, DEAD

POKEMON_SPRITE_WIDTH = 80
POKEMON_SPRITE_HEIGHT = 60
SPACING_X = -30
SPACING_Y = -10

ITEMS_SPRITE_SIZE = 32
ITEM_X_POSITION = 42
ITEM_Y_POSITION = 28

STATUS_SPRITE_WIDTH = 22
STATUS_SPRITE_HEIGHT = 7
STATUS_X_POSITION = 20
STATUS_Y_POSITION = 48

HEALTHBAR_WIDTH = 40
HEALTHBAR_HEIGHT = 6
HEALTHBAR_X_POSITION = 20
HEALTHBAR_Y_POSITION = 4
OUTLINE = "#EAEAEA"
EMPTY = "#000000"
GREEN = "#0ACA14"
ORANGE = "#F4AF00"
RED = "#FF3802"

# Create images from Pokémon sprites
def generatePlayerPartyImage(label, pokemonList: list[PokemonData | None], columnNumber, rowNumber, customSize = None):

    # Don't update anything if corrupted data has been received
    if (any(pokemon and not pokemon.isValid() for pokemon in pokemonList)):
        return

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

    # Display held items, HP and status if enabled in options
    displayStatus = label == PARTY and SETTINGS.isPartyStatusDisplayed()
    displayHP = label == PARTY and SETTINGS.isPartyHealthDisplayed()
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

        # Display status
        if (displayStatus and pokemonData.status):

            # Retrieve and display status sprite
            statusSpritePath = MISCSPRITE_FOLDER / pokemonData.getStatusImage()
            statusSprite = Image.open(statusSpritePath).convert("RGBA").resize((STATUS_SPRITE_WIDTH, STATUS_SPRITE_HEIGHT), Image.NEAREST)
            outputImage.paste(statusSprite, (x + STATUS_X_POSITION, y + STATUS_Y_POSITION), statusSprite)

        # Display HP
        if (displayHP and pokemonData.currentHp is not None):

            # Draw Pokemon health bar and paste it on top of its sprite
            healthBarImage = drawHealthBar(pokemonData)
            outputImage.paste(healthBarImage, (x + HEALTHBAR_X_POSITION, y + HEALTHBAR_Y_POSITION), healthBarImage)


    # Save final image in output folder
    file.safeWriteFile(outputImage, label)


# Draw Pokemon health bar depending on health ratio
def drawHealthBar(pokemon: PokemonData):
    healthRatio = pokemon.currentHp / pokemon.maxHp

    # Determine number of colored pixels and actual color depending on health ratio
    healthColor = GREEN if healthRatio > 0.5 else (RED if healthRatio < 0.2 else ORANGE)
    filledPixels = pokemon.currentHp * (HEALTHBAR_WIDTH - 2) // pokemon.maxHp

    # Create health bar with empty background
    healthBarImage = Image.new("RGBA", (HEALTHBAR_WIDTH, HEALTHBAR_HEIGHT), (0,0,0,0))
    healthBar = ImageDraw.Draw(healthBarImage)

    # Grey outline and black interior
    healthBar.rectangle((0, 0, HEALTHBAR_WIDTH - 1, HEALTHBAR_HEIGHT - 1), fill = OUTLINE)
    healthBar.rectangle((1, 1, HEALTHBAR_WIDTH - 2, HEALTHBAR_HEIGHT - 2), fill = EMPTY)

    # Transparent corners
    for corner in ((0, 0), (HEALTHBAR_WIDTH - 1, 0), (0, HEALTHBAR_HEIGHT - 1), (HEALTHBAR_WIDTH - 1, HEALTHBAR_HEIGHT - 1)):
        healthBar.point(corner, fill = (0,0,0,0))

    # Actual health bar
    if filledPixels > 0:
        healthBar.rectangle((1, 1, filledPixels, HEALTHBAR_HEIGHT - 2), fill = healthColor)

    return healthBarImage