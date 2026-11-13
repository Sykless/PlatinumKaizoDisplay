-- Dev by Sykless
-- Credits for Platinum data structure : https://github.com/yling/yPokeStats
-- Credits for Platinum Kaizo addresses : https://github.com/anastarawneh/PKLuaScript

function getHexValue(intValue)
    return string.format("%x", intValue)
end

local lastTime = os.clock()

local PARTY_POKEMON_SIZE = 0xEC
local BOX_POKEMON_SIZE = 0x88

local SPECIES_NAMES = {"Bulbasaur", "Ivysaur", "Venusaur", "Charmander", "Charmeleon", "Charizard", "Squirtle", "Wartortle", "Blastoise", "Caterpie", "Metapod", "Butterfree", "Weedle", "Kakuna", "Beedrill", "Pidgey", "Pidgeotto", "Pidgeot", "Rattata", "Raticate", "Spearow", "Fearow", "Ekans", "Arbok", "Pikachu", "Raichu", "Sandshrew", "Sandslash", "Nidoran-F", "Nidorina", "Nidoqueen", "Nidoran-M", "Nidorino", "Nidoking", "Clefairy", "Clefable", "Vulpix", "Ninetales", "Jigglypuff", "Wigglytuff", "Zubat", "Golbat", "Oddish", "Gloom", "Vileplume", "Paras", "Parasect", "Venonat", "Venomoth", "Diglett", "Dugtrio", "Meowth", "Persian", "Psyduck", "Golduck", "Mankey", "Primeape", "Growlithe", "Arcanine", "Poliwag", "Poliwhirl", "Poliwrath", "Abra", "Kadabra", "Alakazam", "Machop", "Machoke", "Machamp", "Bellsprout", "Weepinbell", "Victreebel", "Tentacool", "Tentacruel", "Geodude", "Graveler", "Golem", "Ponyta", "Rapidash", "Slowpoke", "Slowbro", "Magnemite", "Magneton", "Farfetch’d", "Doduo", "Dodrio", "Seel", "Dewgong", "Grimer", "Muk", "Shellder", "Cloyster", "Gastly", "Haunter", "Gengar", "Onix", "Drowzee", "Hypno", "Krabby", "Kingler", "Voltorb", "Electrode", "Exeggcute", "Exeggutor", "Cubone", "Marowak", "Hitmonlee", "Hitmonchan", "Lickitung", "Koffing", "Weezing", "Rhyhorn", "Rhydon", "Chansey", "Tangela", "Kangaskhan", "Horsea", "Seadra", "Goldeen", "Seaking", "Staryu", "Starmie", "Mr. Mime", "Scyther", "Jynx", "Electabuzz", "Magmar", "Pinsir", "Tauros", "Magikarp", "Gyarados", "Lapras", "Ditto", "Eevee", "Vaporeon", "Jolteon", "Flareon", "Porygon", "Omanyte", "Omastar", "Kabuto", "Kabutops", "Aerodactyl", "Snorlax", "Articuno", "Zapdos", "Moltres", "Dratini", "Dragonair", "Dragonite", "Mewtwo", "Mew", "Chikorita", "Bayleef", "Meganium", "Cyndaquil", "Quilava", "Typhlosion", "Totodile", "Croconaw", "Feraligatr", "Sentret", "Furret", "Hoothoot", "Noctowl", "Ledyba", "Ledian", "Spinarak", "Ariados", "Crobat", "Chinchou", "Lanturn", "Pichu", "Cleffa", "Igglybuff", "Togepi", "Togetic", "Natu", "Xatu", "Mareep", "Flaaffy", "Ampharos", "Bellossom", "Marill", "Azumarill", "Sudowoodo", "Politoed", "Hoppip", "Skiploom", "Jumpluff", "Aipom", "Sunkern", "Sunflora", "Yanma", "Wooper", "Quagsire", "Espeon", "Umbreon", "Murkrow", "Slowking", "Misdreavus", "Unown", "Wobbuffet", "Girafarig", "Pineco", "Forretress", "Dunsparce", "Gligar", "Steelix", "Snubbull", "Granbull", "Qwilfish", "Scizor", "Shuckle", "Heracross", "Sneasel", "Teddiursa", "Ursaring", "Slugma", "Magcargo", "Swinub", "Piloswine", "Corsola", "Remoraid", "Octillery", "Delibird", "Mantine", "Skarmory", "Houndour", "Houndoom", "Kingdra", "Phanpy", "Donphan", "Porygon2", "Stantler", "Smeargle", "Tyrogue", "Hitmontop", "Smoochum", "Elekid", "Magby", "Miltank", "Blissey", "Raikou", "Entei", "Suicune", "Larvitar", "Pupitar", "Tyranitar", "Lugia", "Ho-Oh", "Celebi", "Treecko", "Grovyle", "Sceptile", "Torchic", "Combusken", "Blaziken", "Mudkip", "Marshtomp", "Swampert", "Poochyena", "Mightyena", "Zigzagoon", "Linoone", "Wurmple", "Silcoon", "Beautifly", "Cascoon", "Dustox", "Lotad", "Lombre", "Ludicolo", "Seedot", "Nuzleaf", "Shiftry", "Taillow", "Swellow", "Wingull", "Pelipper", "Ralts", "Kirlia", "Gardevoir", "Surskit", "Masquerain", "Shroomish", "Breloom", "Slakoth", "Vigoroth", "Slaking", "Nincada", "Ninjask", "Shedinja", "Whismur", "Loudred", "Exploud", "Makuhita", "Hariyama", "Azurill", "Nosepass", "Skitty", "Delcatty", "Sableye", "Mawile", "Aron", "Lairon", "Aggron", "Meditite", "Medicham", "Electrike", "Manectric", "Plusle", "Minun", "Volbeat", "Illumise", "Roselia", "Gulpin", "Swalot", "Carvanha", "Sharpedo", "Wailmer", "Wailord", "Numel", "Camerupt", "Torkoal", "Spoink", "Grumpig", "Spinda", "Trapinch", "Vibrava", "Flygon", "Cacnea", "Cacturne", "Swablu", "Altaria", "Zangoose", "Seviper", "Lunatone", "Solrock", "Barboach", "Whiscash", "Corphish", "Crawdaunt", "Baltoy", "Claydol", "Lileep", "Cradily", "Anorith", "Armaldo", "Feebas", "Milotic", "Castform", "Kecleon", "Shuppet", "Banette", "Duskull", "Dusclops", "Tropius", "Chimecho", "Absol", "Wynaut", "Snorunt", "Glalie", "Spheal", "Sealeo", "Walrein", "Clamperl", "Huntail", "Gorebyss", "Relicanth", "Luvdisc", "Bagon", "Shelgon", "Salamence", "Beldum", "Metang", "Metagross", "Regirock", "Regice", "Registeel", "Latias", "Latios", "Kyogre", "Groudon", "Rayquaza", "Jirachi", "Deoxys", "Turtwig", "Grotle", "Torterra", "Chimchar", "Monferno", "Infernape", "Piplup", "Prinplup", "Empoleon", "Starly", "Staravia", "Staraptor", "Bidoof", "Bibarel", "Kricketot", "Kricketune", "Shinx", "Luxio", "Luxray", "Budew", "Roserade", "Cranidos", "Rampardos", "Shieldon", "Bastiodon", "Burmy", "Wormadam", "Mothim", "Combee", "Vespiquen", "Pachirisu", "Buizel", "Floatzel", "Cherubi", "Cherrim", "Shellos", "Gastrodon", "Ambipom", "Drifloon", "Drifblim", "Buneary", "Lopunny", "Mismagius", "Honchkrow", "Glameow", "Purugly", "Chingling", "Stunky", "Skuntank", "Bronzor", "Bronzong", "Bonsly", "Mime Jr.", "Happiny", "Chatot", "Spiritomb", "Gible", "Gabite", "Garchomp", "Munchlax", "Riolu", "Lucario", "Hippopotas", "Hippowdon", "Skorupi", "Drapion", "Croagunk", "Toxicroak", "Carnivine", "Finneon", "Lumineon", "Mantyke", "Snover", "Abomasnow", "Weavile", "Magnezone", "Lickilicky", "Rhyperior", "Tangrowth", "Electivire", "Magmortar", "Togekiss", "Yanmega", "Leafeon", "Glaceon", "Gliscor", "Mamoswine", "Porygon-Z", "Gallade", "Probopass", "Dusknoir", "Froslass", "Rotom", "Uxie", "Mesprit", "Azelf", "Dialga", "Palkia", "Heatran", "Regigigas", "Giratina", "Cresselia", "Phione", "Manaphy", "Darkrai", "Shaymin", "Arceus"}
local ABILITIES_NAMES = {"Stench", "Drizzle", "Speed Boost", "Battle Armor", "Sturdy", "Damp", "Limber", "Sand Veil", "Static", "Volt Absorb", "Water Absorb", "Oblivious", "Cloud Nine", "Compound Eyes", "Insomnia", "Color Change", "Immunity", "Flash Fire", "Shield Dust", "Own Tempo", "Suction Cups", "Intimidate", "Shadow Tag", "Rough Skin", "Wonder Guard", "Levitate", "Effect Spore", "Synchronize", "Clear Body", "Natural Cure", "Lightning Rod", "Serene Grace", "Swift Swim", "Chlorophyll", "Illuminate", "Trace", "Huge Power", "Poison Point", "Inner Focus", "Magma Armor", "Water Veil", "Magnet Pull", "Soundproof", "Rain Dish", "Sand Stream", "Pressure", "Thick Fat", "Early Bird", "Flame Body", "Run Away", "Keen Eye", "Hyper Cutter", "Pickup", "Truant", "Hustle", "Cute Charm", "Plus", "Minus", "Forecast", "Sticky Hold", "Shed Skin", "Guts", "Marvel Scale", "Liquid Ooze", "Overgrow", "Blaze", "Torrent", "Swarm", "Rock Head", "Drought", "Arena Trap", "Vital Spirit", "White Smoke", "Pure Power", "Shell Armor", "Air Lock", "Tangled Feet", "Motor Drive", "Rivalry", "Steadfast", "Snow Cloak", "Gluttony", "Anger Point", "Unburden", "Heatproof", "Simple", "Dry Skin", "Download", "Iron Fist", "Poison Heal", "Adaptability", "Skill Link", "Hydration", "Solar Power", "Quick Feet", "Normalize", "Sniper", "Magic Guard", "No Guard", "Stall", "Technician", "Leaf Guard", "Klutz", "Mold Breaker", "Super Luck", "Aftermath", "Anticipation", "Forewarn", "Unaware", "Tinted Lens", "Filter", "Slow Start", "Scrappy", "Storm Drain", "Ice Body", "Solid Rock", "Snow Warning", "Honey Gather", "Frisk", "Reckless", "Multitype", "Flower Gift", "Bad Dreams"}
local LOCATIONS_NAMES = {"Twinleaf Town", "Sandgem Town", "Floaroma Town", "Solaceon Town", "Celestic Town", "Jubilife City", "Canalave City", "Oreburgh City", "Eterna City", "Hearthome City", "Pastoria City", "Veilstone City", "Sunyshore City", "Snowpoint City", "Pokémon League", "Route 201", "Route 202", "Route 203", "Route 204", "Route 205", "Route 206", "Route 207", "Route 208", "Route 209", "Route 210", "Route 211", "Route 212", "Route 213", "Route 214", "Route 215", "Route 216", "Route 217", "Route 218", "Route 219", "Route 220", "Route 221", "Route 222", "Route 223", "Route 224", "Route 225", "Route 226", "Route 227", "Route 228", "Route 229", "Route 230", "Oreburgh Mine", "Valley Windworks", "Eterna Forest", "Fuego Ironworks", "Mt. Coronet", "Spear Pillar", "Great Marsh", "Solaceon Ruins", "Victory Road", "Pal Park", "Amity Square", "Ravaged Path", "Floaroma Meadow", "Oreburgh Gate", "Fullmoon Island", "Sendoff Spring", "Turnback Cave", "Flower Paradise", "Snowpoint Temple", "Wayward Cave", "Ruin Maniac Cave", "Maniac Tunnel", "Trophy Garden", "Iron Island", "Old Chateau", "Galactic HQ", "Verity Lakefront", "Valor Lakefront", "Acuity Lakefront", "Spring Path", "Lake Verity", "Lake Valor", "Lake Acuity", "Newmoon Island", "Battle Tower", "Fight Area", "Survival Area", "Resort Area", "Stark Mountain", "Seabreak Path", "Hall of Origin", "Verity Cavern", "Valor Cavern", "Acuity Cavern", "Jubilife TV", "Pokétch Co.", "Clamberclaw Cliffs", "Trainers' School", "Mining Museum", "Flower Shop", "Cycle Shop", "Contest Hall", "Poffin House", "Celestica Ruins", "Pokémon Day Care", "Veilstone Store", "Casino", "Canalave Library", "Vista Lighthouse", "Distortion World (Zone 2)", "Pokémon Mansion", "Distortion World (Zone 1)", "Café", "Grand Lake", "Restaurant", "Battle Park", "Battle Frontier", "Battle Factory", "Battle Castle", "Coronet Highlands", "Battle Hall", "Distortion World", "Lost Tower", "The Underground", "Distortion World (Zone 3)", "ROTOM's Room", "T.G. Eterna Bldg", "Iron Ruins", "Iceberg Ruins", "Rock Peak Ruins", [2001] = "Link Trade"}
local NATURES_NAMES = {"Hardy", "Lonely", "Brave", "Adamant", "Naughty", "Bold", "Docile", "Relaxed", "Impish", "Lax", "Timid", "Hasty", "Serious", "Jolly", "Naive", "Modest", "Mild", "Quiet", "Bashful", "Rash", "Calm", "Gentle", "Sassy", "Careful", "Quirky"}
local MOVES_NAMES = {"Pound", "Karate Chop", "Double Slap", "Weather Ball Water", "Mega Punch", "Pay Day", "Fire Punch", "Ice Punch", "Thunder Punch", "Scratch", "Vise Grip", "Guillotine", "Razor Wind", "Swords Dance", "Cut", "Gust", "Wing Attack", "Whirlwind", "Fly", "Mystical Fire", "Slam", "Vine Whip", "Stomp", "Double Kick", "Mega Kick", "Jump Kick", "Rolling Kick", "Sand Attack", "Headbutt", "Weather Ball Fire", "Fury Attack", "Horn Drill", "Tackle", "Body Slam", "Wrap", "Take Down", "Thrash", "Double-Edge", "Tail Whip", "Poison Sting", "Twineedle", "Pin Missile", "Leer", "Bite", "Growl", "Roar", "Sing", "Supersonic", "Sonic Boom", "Disable", "Acid", "Ember", "Flamethrower", "Mist", "Water Gun", "Hydro Pump", "Surf", "Ice Beam", "Blizzard", "Psybeam", "Bubble Beam", "Aurora Beam", "Hyper Beam", "Peck", "Drill Peck", "Submission", "Low Kick", "Counter", "Seismic Toss", "Strength", "Absorb", "Mega Drain", "Leech Seed", "Growth", "Razor Leaf", "Solar Beam", "Poison Powder", "Stun Spore", "Sleep Powder", "Petal Dance", "String Shot", "Dragon Rage", "Fire Spin", "Thunder Shock", "Thunderbolt", "Thunder Wave", "Thunder", "Rock Throw", "Earthquake", "Fissure", "Dig", "Toxic", "Confusion", "Psychic", "Hypnosis", "Meditate", "Agility", "Quick Attack", "Rage", "Teleport", "Night Shade", "Mimic", "Screech", "Double Team", "Recover", "Harden", "Minimize", "Smokescreen", "Confuse Ray", "Withdraw", "Weather Ball Rock", "Barrier", "Light Screen", "Haze", "Reflect", "Focus Energy", "Bide", "Metronome", "Mirror Move", "Self-Destruct", "Egg Bomb", "Lick", "Smog", "Sludge", "Bone Club", "Fire Blast", "Waterfall", "Clamp", "Swift", "Solar-Beam", "Weather Ball Ice", "Constrict", "Amnesia", "Kinesis", "Soft-Boiled", "High Jump Kick", "Glare", "Dream Eater", "Poison Gas", "Hurricane", "Leech Life", "Lovely Kiss", "Sky Attack", "Transform", "Bubble", "Dizzy Punch", "Spore", "Flash", "Triple Axel", "Hidden Power Water", "Acid Armor", "Crabhammer", "Explosion", "Fury Swipes", "Bonemerang", "Rest", "Rock Slide", "Hyper Fang", "Sharpen", "Hidden Power Ice", "Tri Attack", "Super Fang", "Slash", "Substitute", "Struggle", "Sketch", "Triple Kick", "Thief", "Spider Web", "Mind Reader", "Hidden Power Ghost", "Flame Wheel", "Snore", "Curse", "Flail", "Conversion 2", "Aeroblast", "Cotton Spore", "Reversal", "Spite", "Powder Snow", "Protect", "Mach Punch", "Scary Face", "Feint Attack", "Sweet Kiss", "Belly Drum", "Sludge Bomb", "Mud-Slap", "Octazooka", "Spikes", "Zap Cannon", "Foresight", "Destiny Bond", "Perish Song", "Icy Wind", "Detect", "Bone Rush", "Lock-On", "Outrage", "Sandstorm", "Giga Drain", "Endure", "Charm", "Accelerock", "False Swipe", "Swagger", "Milk Drink", "Wild Charge", "Fury Cutter", "Steel Wing", "Mean Look", "Attract", "Sleep Talk", "Heal Bell", "Return", "Present", "Frustration", "Safeguard", "Pain Split", "Sacred Fire", "Bulldoze", "Dynamic Punch", "Megahorn", "Dragon Breath", "Baton Pass", "Encore", "Pursuit", "Hidden Power Fire", "Sweet Scent", "Iron Tail", "Metal Claw", "Vital Throw", "Morning Sun", "Synthesis", "Moonlight", "Hidden Power", "Cross Chop", "Twister", "Rain Dance", "Sunny Day", "Crunch", "Mirror Coat", "Psych Up", "Extreme Speed", "Ancient Power", "Shadow Ball", "Future Sight", "Rock Smash", "Whirlpool", "Beat Up", "Fake Out", "Uproar", "Stockpile", "Hidden Power Rock", "Swallow", "Heat Wave", "Hail", "Torment", "Flatter", "Will-O-Wisp", "Memento", "Facade", "Focus Punch", "Smelling Salts", "Follow Me", "Nature Power", "Charge", "Hidden Power Dark", "Helping Hand", "Hidden Power Psychic", "Role Play", "Wish", "Assist", "Ingrain", "Superpower", "Magic Coat", "Recycle", "Revenge", "Brick Break", "Yawn", "Knock Off", "Endeavor", "Eruption", "Skill Swap", "Imprison", "Refresh", "Grudge", "Drill Run", "Secret Power", "Dive", "Hidden Power Fighting", "Camouflage", "Tail Glow", "Luster Purge", "Mist Ball", "Feather Dance", "Teeter Dance", "Blaze Kick", "Hidden Power Ground", "Ice Ball", "Needle Arm", "Slack Off", "Hyper Voice", "Poison Fang", "Crush Claw", "Blast Burn", "Hydro Cannon", "Meteor Mash", "Astonish", "Weather Ball", "Aromatherapy", "Fake Tears", "Air Cutter", "Overheat", "Odor Sleuth", "Rock Tomb", "Silver Wind", "Metal Sound", "Grass Whistle", "Tickle", "Cosmic Power", "Water Spout", "Signal Beam", "Shadow Punch", "Extrasensory", "Sky Uppercut", "Sand Tomb", "Sheer Cold", "Muddy Water", "Bullet Seed", "Aerial Ace", "Icicle Spear", "Iron Defense", "Block", "Howl", "Dragon Claw", "Frenzy Plant", "Bulk Up", "Bounce", "Mud Shot", "Poison Tail", "Hidden Power Grass", "Volt Tackle", "Magical Leaf", "Scald", "Calm Mind", "Leaf Blade", "Dragon Dance", "Rock Blast", "Shock Wave", "Water Pulse", "Doom Desire", "Psycho Boost", "Roost", "Gravity", "Miracle Eye", "Wake-Up Slap", "Hammer Arm", "Gyro Ball", "Hidden Power Electric", "Brine", "Natural Gift", "Feint", "Pluck", "Tailwind", "Acupressure", "Metal Burst", "U-turn", "Close Combat", "Payback", "Assurance", "Embargo", "Fling", "Psycho Shift", "Trump Card", "Aqua Cutter", "Wring Out", "Power Trick", "Gastro Acid", "Lucky Chant", "Me First", "Copycat", "Power Swap", "Guard Swap", "Punishment", "Last Resort", "Worry Seed", "Sucker Punch", "Toxic Spikes", "Heart Swap", "Aqua Ring", "Magnet Rise", "Flare Blitz", "Force Palm", "Aura Sphere", "Rock Polish", "Poison Jab", "Dark Pulse", "Night Slash", "Aqua Tail", "Seed Bomb", "Air Slash", "X-Scissor", "Bug Buzz", "Dragon Pulse", "Dragon Rush", "Power Gem", "Drain Punch", "Vacuum Wave", "Focus Blast", "Energy Ball", "Brave Bird", "Earth Power", "Hidden Power Flying", "Giga Impact", "Nasty Plot", "Bullet Punch", "Avalanche", "Ice Shard", "Shadow Claw", "Thunder Fang", "Ice Fang", "Fire Fang", "Shadow Sneak", "Mud Bomb", "Psycho Cut", "Zen Headbutt", "Mirror Shot", "Flash Cannon", "Rock Climb", "Defog", "Trick Room", "Draco Meteor", "Discharge", "Lava Plume", "Leaf Storm", "Power Whip", "Rock Wrecker", "Cross Poison", "Gunk Shot", "Iron Head", "Magnet Bomb", "Stone Edge", "Captivate", "Stealth Rock", "Grass Knot", "Chatter", "Judgment", "Bug Bite", "Charge Beam", "Wood Hammer", "Aqua Jet", "Attack Order", "Defend Order", "Heal Order", "Head Smash", "Double Hit", "Roar of Time", "Spacial Rend", "Lunar Dance", "Crush Grip", "Magma Storm", "Dark Void", "Seed Flare", "Ominous Wind", "Shadow Force"}
local CHARACTERS = {[0x0121] = "0", [0x0122] = "1", [0x0123] = "2", [0x0124] = "3", [0x0125] = "4", [0x0126] = "5", [0x0127] = "6", [0x0128] = "7", [0x0129] = "8", [0x012A] = "9", [0x012B] = "A", [0x012C] = "B", [0x012D] = "C", [0x012E] = "D", [0x012F] = "E", [0x0130] = "F", [0x0131] = "G", [0x0132] = "H", [0x0133] = "I", [0x0134] = "J", [0x0135] = "K", [0x0136] = "L", [0x0137] = "M", [0x0138] = "N", [0x0139] = "O", [0x013A] = "P", [0x013B] = "Q", [0x013C] = "R", [0x013D] = "S", [0x013E] = "T", [0x013F] = "U", [0x0140] = "V", [0x0141] = "W", [0x0142] = "X", [0x0143] = "Y", [0x0144] = "Z", [0x0145] = "a", [0x0146] = "b", [0x0147] = "c", [0x0148] = "d", [0x0149] = "e", [0x014A] = "f", [0x014B] = "g", [0x014C] = "h", [0x014D] = "i", [0x014E] = "j", [0x014F] = "k", [0x0150] = "l", [0x0151] = "m", [0x0152] = "n", [0x0153] = "o", [0x0154] = "p", [0x0155] = "q", [0x0156] = "r", [0x0157] = "s", [0x0158] = "t", [0x0159] = "u", [0x015A] = "v", [0x015B] = "w", [0x015C] = "x", [0x015D] = "y", [0x015E] = "z", [0x015F] = "À", [0x0160] = "Á", [0x0161] = "Â", [0x0162] = "Ã", [0x0163] = "Ä", [0x0164] = "Å", [0x0165] = "Æ", [0x0166] = "Ç", [0x0167] = "È", [0x0168] = "É", [0x0169] = "Ê", [0x016A] = "Ë", [0x016B] = "Ì", [0x016C] = "Í", [0x016D] = "Î", [0x016E] = "Ï", [0x016F] = "Ð", [0x0170] = "Ñ", [0x0171] = "Ò", [0x0172] = "Ó", [0x0173] = "Ô", [0x0174] = "Õ", [0x0175] = "Ö", [0x0176] = "×", [0x0177] = "Ø", [0x0178] = "Ù", [0x0179] = "Ú", [0x017A] = "Û", [0x017B] = "Ü", [0x017C] = "Ý", [0x017D] = "Þ", [0x017E] = "ß", [0x017F] = "à", [0x0180] = "á", [0x0181] = "â", [0x0182] = "ã", [0x0183] = "ä", [0x0184] = "å", [0x0185] = "æ", [0x0186] = "ç", [0x0187] = "è", [0x0188] = "é", [0x0189] = "ê", [0x018A] = "ë", [0x018B] = "ì", [0x018C] = "í", [0x018D] = "î", [0x018E] = "ï", [0x018F] = "ð", [0x0190] = "ñ", [0x0191] = "ò", [0x0192] = "ó", [0x0193] = "ô", [0x0194] = "õ", [0x0195] = "ö", [0x0196] = "÷", [0x0197] = "ø", [0x0198] = "ù", [0x0199] = "ú", [0x019A] = "û", [0x019B] = "ü", [0x019C] = "ý", [0x019D] = "þ", [0x019E] = "ÿ", [0x019F] = "Œ", [0x01A0] = "œ", [0x01A1] = "Ş", [0x01A2] = "ş", [0x01A3] = "ª", [0x01A4] = "º", [0x01A5] = "er", [0x01A6] = "re", [0x01A7] = "r", [0x01A8] = "Pokémon Dollar", [0x01A9] = "¡", [0x01AA] = "¿", [0x01AB] = "!", [0x01AC] = "?", [0x01AD] = ",", [0x01AE] = ".", [0x01AF] = "…", [0x01B0] = "･", [0x01B1] = "/", [0x01B2] = "‘", [0x01B3] = "'", [0x01B4] = "“", [0x01B5] = "”", [0x01B6] = "„", [0x01B7] = "«", [0x01B8] = "»", [0x01B9] = "(", [0x01BA] = ")", [0x01BB] = "♂", [0x01BC] = "♀", [0x01BD] = "+", [0x01BE] = "-", [0x01BF] = "*", [0x01C0] = "#", [0x01C1] = "=", [0x01C2] = "&", [0x01C3] = "~", [0x01C4] = ":", [0x01C5] = ";", [0x01C6] = "♠", [0x01C7] = "♣", [0x01C8] = "♥", [0x01C9] = "♦", [0x01CA] = "★", [0x01CB] = "◎", [0x01CC] = "○", [0x01CD] = "□", [0x01CE] = "△", [0x01CF] = "◇", [0x01D0] = "@", [0x01D1] = "♪", [0x01D2] = "%", [0x01D3] = "☀", [0x01D4] = "☁", [0x01D5] = "☂", [0x01D6] = "☃", [0x01D7] = "😑︎", [0x01D8] = "☺", [0x01D9] = "☹", [0x01DA] = "😠︎", [0x01DB] = "⤴︎", [0x01DC] = "⤵︎", [0x01DD] = "💤︎", [0x01DE] = " "}

local SPECIES_CURVES = {3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 4, 4, 0, 0, 4, 4, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 5, 5, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 5, 5, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 3, 3, 3, 5, 0, 0, 0, 0, 0, 0, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 0, 0, 0, 0, 0, 0, 5, 5, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 4, 4, 4, 4, 0, 5, 5, 0, 4, 4, 4, 4, 0, 0, 3, 3, 3, 3, 4, 4, 0, 3, 3, 3, 3, 4, 3, 3, 0, 0, 0, 0, 0, 3, 0, 4, 0, 5, 0, 0, 0, 0, 3, 5, 4, 4, 0, 0, 3, 5, 3, 0, 0, 0, 0, 5, 5, 4, 0, 0, 4, 5, 5, 5, 5, 0, 0, 0, 0, 5, 4, 0, 0, 0, 0, 0, 5, 4, 5, 5, 5, 5, 5, 5, 5, 5, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 5, 5, 5, 0, 0, 2, 2, 5, 5, 5, 1, 1, 1, 3, 3, 3, 2, 2, 4, 0, 1, 1, 3, 4, 5, 5, 5, 0, 0, 5, 5, 0, 0, 1, 2, 3, 2, 2, 5, 5, 2, 2, 0, 0, 0, 4, 4, 4, 3, 3, 3, 3, 3, 1, 1, 1, 2, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1, 1, 1, 1, 1, 0, 3, 4, 4, 4, 4, 5, 4, 3, 5, 0, 0, 3, 3, 3, 1, 1, 1, 5, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 0, 0, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0, 4, 2, 2, 0, 0, 4, 3, 1, 1, 4, 0, 0, 0, 0, 0, 0, 4, 3, 0, 5, 5, 5, 5, 3, 3, 5, 5, 5, 5, 0, 0, 5, 1, 1, 5, 5, 5, 3, 0, 0, 5, 0, 0, 0, 4, 0, 0, 0, 3, 5, 0, 5, 0, 4, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 5}
local LEVEL_UP_CURVES = {{0, 0, 0, 0, 0, 0, 0}, {8, 15, 4, 9, 6, 10, 8}, {27, 52, 13, 57, 21, 33, 27}, {64, 122, 32, 96, 51, 80, 64}, {125, 237, 65, 135, 100, 156, 125}, {216, 406, 112, 179, 172, 270, 216}, {343, 637, 178, 236, 274, 428, 343}, {512, 942, 276, 314, 409, 640, 512}, {729, 1326, 393, 419, 583, 911, 729}, {1000, 1800, 540, 560, 800, 1250, 1000}, {1331, 2369, 745, 742, 1064, 1663, 1331}, {1728, 3041, 967, 973, 1382, 2160, 1728}, {2197, 3822, 1230, 1261, 1757, 2746, 2197}, {2744, 4719, 1591, 1612, 2195, 3430, 2744}, {3375, 5737, 1957, 2035, 2700, 4218, 3375}, {4096, 6881, 2457, 2535, 3276, 5120, 4096}, {4913, 8155, 3046, 3120, 3930, 6141, 4913}, {5832, 9564, 3732, 3798, 4665, 7290, 5832}, {6859, 11111, 4526, 4575, 5487, 8573, 6859}, {8000, 12800, 5440, 5460, 6400, 10000, 8000}, {9261, 14632, 6482, 6458, 7408, 11576, 9261}, {10648, 16610, 7666, 7577, 8518, 13310, 10648}, {12167, 18737, 9003, 8825, 9733, 15208, 12167}, {13824, 21012, 10506, 10208, 11059, 17280, 13824}, {15625, 23437, 12187, 11735, 12500, 19531, 15625}, {17576, 26012, 14060, 13411, 14060, 21970, 17576}, {19683, 28737, 16140, 15244, 15746, 24603, 19683}, {21952, 31610, 18439, 17242, 17561, 27440, 21952}, {24389, 34632, 20974, 19411, 19511, 30486, 24389}, {27000, 37800, 23760, 21760, 21600, 33750, 27000}, {29791, 41111, 26811, 24294, 23832, 37238, 29791}, {32768, 44564, 30146, 27021, 26214, 40960, 32768}, {35937, 48155, 33780, 29949, 28749, 44921, 35937}, {39304, 51881, 37731, 33084, 31443, 49130, 39304}, {42875, 55737, 42017, 36435, 34300, 53593, 42875}, {46656, 59719, 46656, 40007, 37324, 58320, 46656}, {50653, 63822, 50653, 43808, 40522, 63316, 50653}, {54872, 68041, 55969, 47846, 43897, 68590, 54872}, {59319, 72369, 60505, 52127, 47455, 74148, 59319}, {64000, 76800, 66560, 56660, 51200, 80000, 64000}, {68921, 81326, 71677, 61450, 55136, 86151, 68921}, {74088, 85942, 78533, 66505, 59270, 92610, 74088}, {79507, 90637, 84277, 71833, 63605, 99383, 79507}, {85184, 95406, 91998, 77440, 68147, 106480, 85184}, {91125, 100237, 98415, 83335, 72900, 113906, 91125}, {97336, 105122, 107069, 89523, 77868, 121670, 97336}, {103823, 110052, 114205, 96012, 83058, 129778, 103823}, {110592, 115015, 123863, 102810, 88473, 138240, 110592}, {117649, 120001, 131766, 109923, 94119, 147061, 117649}, {125000, 125000, 142500, 117360, 100000, 156250, 125000}, {132651, 131324, 151222, 125126, 106120, 165813, 132651}, {140608, 137795, 163105, 133229, 112486, 175760, 140608}, {148877, 144410, 172697, 141677, 119101, 186096, 148877}, {157464, 151165, 185807, 150476, 125971, 196830, 157464}, {166375, 158056, 196322, 159635, 133100, 207968, 166375}, {175616, 165079, 210739, 169159, 140492, 219520, 175616}, {185193, 172229, 222231, 179056, 148154, 231491, 185193}, {195112, 179503, 238036, 189334, 156089, 243890, 195112}, {205379, 186894, 250562, 199999, 164303, 256723, 205379}, {216000, 194400, 267840, 211060, 172800, 270000, 216000}, {226981, 202013, 281456, 222522, 181584, 283726, 226981}, {238328, 209728, 300293, 234393, 190662, 297910, 238328}, {250047, 217540, 315059, 246681, 200037, 312558, 250047}, {262144, 225443, 335544, 259392, 209715, 327680, 262144}, {274625, 233431, 351520, 272535, 219700, 343281, 274625}, {287496, 241496, 373744, 286115, 229996, 359370, 287496}, {300763, 249633, 390991, 300140, 240610, 375953, 300763}, {314432, 257834, 415050, 314618, 251545, 393040, 314432}, {328509, 267406, 433631, 329555, 262807, 410636, 328509}, {343000, 276458, 459620, 344960, 274400, 428750, 343000}, {357911, 286328, 479600, 360838, 286328, 447388, 357911}, {373248, 296358, 507617, 377197, 298598, 466560, 373248}, {389017, 305767, 529063, 394045, 311213, 486271, 389017}, {405224, 316074, 559209, 411388, 324179, 506530, 405224}, {421875, 326531, 582187, 429235, 337500, 527343, 421875}, {438976, 336255, 614566, 447591, 351180, 548720, 438976}, {456533, 346965, 639146, 466464, 365226, 570666, 456533}, {474552, 357812, 673863, 485862, 379641, 593190, 474552}, {493039, 367807, 700115, 505791, 394431, 616298, 493039}, {512000, 378880, 737280, 526260, 409600, 640000, 512000}, {531441, 390077, 765275, 547274, 425152, 664301, 531441}, {551368, 400293, 804997, 568841, 441094, 689210, 551368}, {571787, 411686, 834809, 590969, 457429, 714733, 571787}, {592704, 423190, 877201, 613664, 474163, 740880, 592704}, {614125, 433572, 908905, 636935, 491300, 767656, 614125}, {636056, 445239, 954084, 660787, 508844, 795070, 636056}, {658503, 457001, 987754, 685228, 526802, 823128, 658503}, {681472, 467489, 1035837, 710266, 545177, 851840, 681472}, {704969, 479378, 1071552, 735907, 563975, 881211, 704969}, {729000, 491346, 1122660, 762160, 583200, 911250, 729000}, {753571, 501878, 1160499, 789030, 602856, 941963, 753571}, {778688, 513934, 1214753, 816525, 622950, 973360, 778688}, {804357, 526049, 1254796, 844653, 643485, 1005446, 804357}, {830584, 536557, 1312322, 873420, 664467, 1038230, 830584}, {857375, 548720, 1354652, 902835, 685900, 1071718, 857375}, {884736, 560922, 1415577, 932903, 707788, 1105920, 884736}, {912673, 571333, 1460276, 963632, 730138, 1140841, 912673}, {941192, 583539, 1524731, 995030, 752953, 1176490, 941192}, {970299, 591882, 1571884, 1027103, 776239, 1212873, 970299}, {1000000, 600000, 1640000, 1059860, 800000, 1250000, 1000000}}
local SPECIES_FORMS = {
    [201] = {"", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""},
    [386] = {"-Attack", "-Defense", "-Speed"},
    [412] = {"-Sandy", "-Trash"},
    [413] = {"-Sandy", "-Trash"},
    [414] = {"", ""},
    [422] = {""},
    [423] = {""},
    [479] = {"-Heat", "-Wash", "-Frost", "-Fan", "-Mow"},
    [487] = {"-Origin"},
    [492] = {"-Sky"}
}

-- Used to decrypt Pokémon data
local SHUFFLE = {
    {0x08, 0x28, 0x48, 0x68}, {0x08, 0x28, 0x68, 0x48}, {0x08, 0x48, 0x28, 0x68}, {0x08, 0x68, 0x28, 0x48},
    {0x08, 0x48, 0x68, 0x28}, {0x08, 0x68, 0x48, 0x28}, {0x28, 0x08, 0x48, 0x68}, {0x28, 0x08, 0x68, 0x48},
    {0x48, 0x08, 0x28, 0x68}, {0x68, 0x08, 0x28, 0x48}, {0x48, 0x08, 0x68, 0x28}, {0x68, 0x08, 0x48, 0x28},
    {0x28, 0x48, 0x08, 0x68}, {0x28, 0x68, 0x08, 0x48}, {0x48, 0x28, 0x08, 0x68}, {0x68, 0x28, 0x08, 0x48},
    {0x48, 0x68, 0x08, 0x28}, {0x68, 0x48, 0x08, 0x28}, {0x28, 0x48, 0x68, 0x08}, {0x28, 0x68, 0x48, 0x08},
    {0x48, 0x28, 0x68, 0x08}, {0x68, 0x28, 0x48, 0x08}, {0x48, 0x68, 0x28, 0x08}, {0x68, 0x48, 0x28, 0x08}}


-- Get lua script version from VERSION file
function getVersion()
    local version = "?"
    local f = io.open("./VERSION", "r")

    if f then
        version = f:read("*a")
        f:close()
    end

    return version
end


-------------------------------------------------------------------
-- Decrypt Pokemon attributes and convert them to Pokemon object --
-------------------------------------------------------------------
function mult32(a, b)
    local c = bit.band(bit.rshift(a,16), 0xFFFF)
    local d = bit.band(a, 0xFFFF)
    local e = bit.band(bit.rshift(b,16), 0xFFFF)
    local f = bit.band(b, 0xFFFF)
    local g = bit.band(c * f + d * e, 0xFFFF)
    local h = d * f
    return bit.band(g * 0x10000 + h, 0xFFFFFFFF) 
end

function decryptData(address, length, seed)
    local data = {}
    for i = address, address + length - 2, 2 do
        seed = bit.band(mult32(seed, 0x41C64E6D) + 0x6073, 0xFFFFFFFF)
        encryptedWord = memory.readword(i)
        decryptedWord = bit.bxor(encryptedWord, bit.rshift(seed, 16))
        data[i - address] = decryptedWord
    end
    return data
end

function decryptPokemon(pokemonAddress, isBox)
    local pid = memory.readdword(pokemonAddress)
    local checksum = memory.readword(pokemonAddress + 0x6)
    local decryptedTables = decryptData(pokemonAddress + 0x8, 0x80, checksum)
    local decrypted = {}

    -- Read uncrypted Pokemon attribute
    for i = pokemonAddress, pokemonAddress + 0x6, 2 do
        decrypted[i - pokemonAddress] = memory.readword(i)
    end 

    -- Decrypt each attribute
    for i = 0x8, 0x86, 2 do
        decrypted[i] = decryptedTables[i - 0x8]
    end

    -- Party Pokemon : decrypt further attributes 
    if not isBox then
        local decryptedBattle = decryptData(pokemonAddress + 0x88, 0x64, pid)
        for i = 0x88, 0xEA, 2 do
            decrypted[i] = decryptedBattle[i - 0x88]
        end
    end

    return decrypted
end

function getPartyPokemon(pokemonAddress)
    local decrypted = decryptPokemon(pokemonAddress)
    local pid = decrypted[0x2] * 0x10000 + decrypted[0x0]

    -- Retrieve pokedexId
    local shuffleKey = bit.rshift(bit.band(pid, 0x3E000), 0xD) % 24 + 1
    local blockA = SHUFFLE[shuffleKey][1]
    local pokedexId = decrypted[blockA]

    -- PokedexId above 493, data is apparently not encrypted (manually added ?)
    if pokedexId > 493 then
        for i = pokemonAddress, pokemonAddress + PARTY_POKEMON_SIZE, 2 do
            decrypted[i - pokemonAddress] = memory.readword(i)
        end
    end

    return createPokemonObject(decrypted, pokemonAddress)
end

function getBoxPokemon(boxSlot)
    local pcAddress = memory.readdword(0x021C0794) + 0x14 + 0xCF2C + 0x4
    local pokemonAddress = pcAddress + (BOX_POKEMON_SIZE * boxSlot)

    -- No Pokemon in box slot
    if not memory.readdword(pokemonAddress) then
       return false
    end

    local decrypted = decryptPokemon(pokemonAddress, true)
    return createPokemonObject(decrypted, pokemonAddress, true)
end

function getTrainerPokemon(pokemonAddress)
    local decrypted = decryptPokemon(pokemonAddress)
    return createPokemonObject(decrypted, pokemonAddress)
end

function createPokemonObject(decrypted, pokemonAddress, isBox)
    local pokemon = {}
    local pid = decrypted[0x2] * 0x10000 + decrypted[0x0]

    -- Shuffle data to retrieve decrypted data
    local shuffleKey = bit.rshift(bit.band(pid, 0x3E000), 0xD) % 24 + 1
    local blockA = SHUFFLE[shuffleKey][1]
    local blockB = SHUFFLE[shuffleKey][2]
    local blockC = SHUFFLE[shuffleKey][3]
    local blockD = SHUFFLE[shuffleKey][4]

    pokemon.pid = pid
    pokemon.speciesId = decrypted[blockA]
    if pokemon.speciesId == 0 then
        return false
    end

    -- Retrieve Pokémon attributes
    pokemon.species = SPECIES_NAMES[pokemon.speciesId]
    pokemon.heldItem = decrypted[blockA + 0x2]
    pokemon.ability = ABILITIES_NAMES[bit.rshift(decrypted[blockA + 0xC], 8)]

    local genderFormeByte = decrypted[blockB + 0x18]
    local form = bit.rshift(genderFormeByte, 3)

    if form > 0 then
        local forms = SPECIES_FORMS[pokemon.speciesId]

        if forms ~= nil and form <= #forms then
            pokemon.species = pokemon.species .. forms[form]
            pokemon.speciesId = pokemon.speciesId + 1000 * form -- 1386 for Deoxys-A, 2386 for Deoxys-D, etc
        end
    end
    
    local ivData = decrypted[blockB + 0x12] * 0x10000 + decrypted[blockB + 0x10]
    local isEgg = bit.band(bit.rshift(ivData, 30), 1) == 1
    local location
    if not isEgg then
        location = LOCATIONS_NAMES[decrypted[blockB + 0x1E]]
    end

    pokemon.isEgg = isEgg
    pokemon.exp = decrypted[blockA + 0xA] * 0x10000 + decrypted[blockA + 0x8]
    pokemon.nature = NATURES_NAMES[pid % 25 + 1]
    pokemon.ivHp = bit.band(ivData, 0x1F)
    pokemon.ivAtk = bit.band(ivData, 0x3E0) / 0x20
    pokemon.ivDef = bit.band(ivData, 0x7C00) / 0x400
    pokemon.ivSpe = bit.band(ivData, 0xF8000) / 32768
    pokemon.ivSpa = bit.band(ivData, 0x1F00000) / 0x100000
    pokemon.ivSpd = bit.band(ivData, 0x3E000000) / 0x2000000
    pokemon.move1 = MOVES_NAMES[decrypted[blockB + 0x0]]
    pokemon.move2 = MOVES_NAMES[decrypted[blockB + 0x2]]
    pokemon.move3 = MOVES_NAMES[decrypted[blockB + 0x4]]
    pokemon.move4 = MOVES_NAMES[decrypted[blockB + 0x6]]

    pokemon.gender = "M"
    if bit.band(bit.rshift(genderFormeByte, 1), 1) == 1 then
        pokemon.gender = "F"
    end
    if bit.band(bit.rshift(genderFormeByte, 2), 1) == 1 then
        pokemon.gender = "N"
    end

    if not isBox then
        local currentSeed = bit.band(mult32(pokemon.pid, 0x41C64E6D) + 0x6073, 0xFFFFFFFF)

        for battleOffset = 0x88, 0x9A, 2 do
            local key = bit.band(bit.rshift(currentSeed, 16), 0xFFFF)
            local encryptedValue = memory.readword(pokemonAddress + battleOffset)
            local decryptedValue = bit.bxor(encryptedValue, key)

            if battleOffset == 0x88 then pokemon.status = bit.band(decryptedValue, 0xFF) end
            if battleOffset == 0x8E then pokemon.currentHp = decryptedValue end
            if battleOffset == 0x90 then pokemon.maxHp = decryptedValue end
            if battleOffset == 0x92 then pokemon.atk = decryptedValue end
            if battleOffset == 0x94 then pokemon.def = decryptedValue end
            if battleOffset == 0x96 then pokemon.spe = decryptedValue end
            if battleOffset == 0x98 then pokemon.spa = decryptedValue end
            if battleOffset == 0x9A then pokemon.spd = decryptedValue end

            currentSeed = bit.band(mult32(currentSeed, 0x41C64E6D) + 0x6073, 0xFFFFFFFF)
        end
    end

    return pokemon
end

function retrieveTrainerTeam(trainerData, opponentAddress, opponentBattleAddress)
    local opponentParty = {}
    local opponentPartySize = memory.readbyte(opponentAddress - 4)

    -- First loop : retrieve trainer team original state
    for partySlot = 0, opponentPartySize - 1 do
        originalMon = getTrainerPokemon(opponentAddress + PARTY_POKEMON_SIZE * partySlot)

        if (originalMon and originalMon.speciesId ~= 0) then
            opponentParty[originalMon.pid] = originalMon
        end
    end

    -- Second loop : retrieve trainer team current state in battle (we want to keep original item but get current HP)
    for partySlot = 0, opponentPartySize - 1 do
        battleMon = getTrainerPokemon(opponentBattleAddress + PARTY_POKEMON_SIZE * partySlot)

        if (battleMon and battleMon.speciesId ~= 0 and opponentParty[battleMon.pid]) then
            opponentParty[battleMon.pid].currentHp = battleMon.currentHp
        end
    end

    -- Final loop : copy trainer team data in file
    for pid, pokemon in pairs(opponentParty) do
        trainerData = trainerData .. "|" .. pokemon.speciesId .. "¤" .. pokemon.heldItem .. "¤" .. pokemon.currentHp
    end

    return trainerData
end


-------------------------------------
-- Main loop, triggered each frame --
-------------------------------------
function sendPokemonData()
    local now = os.clock()

	-- Execute script logic every second
    if now - lastTime >= 1 then
        lastTime = now

        local BASE_ADDRESS = memory.readdword(0x02101D2C)
        local PARTY_ADDRESS = BASE_ADDRESS + 0xD094
        local TRAINERS_START = BASE_ADDRESS + 0xD076
        local TRAINER_END = BASE_ADDRESS + 0xE1E0

		local i = 0
		local emptyBox = false
		local alivePokemon = true
        local inBattle = false

        local mon
        local partyPokemon = "PARTY"
        local boxPokemon = "BOX"
        local deadPokemon = "DEAD"
        local trainerParty = "TRAINERPARTY"
        local doubleTrainerParty = "DOUBLETRAINERPARTY"
        local defeatedTrainers = "TRAINERS"

        local partyAddress = PARTY_ADDRESS
        local partySize = memory.readbyte(partyAddress - 4)
        local opponentAddress = memory.readdword(BASE_ADDRESS + 0x352F4) + 0x7A0
        local opponentBattleAddress = 0

        -- Check if we're in battle to retrieve live-updated stats (like HP)
        if (opponentAddress > 0x02000000 and opponentAddress < 0x03000000) then
            local opponentPid = memory.readdword(opponentAddress)
            local trainerPartySize = memory.readbyte(opponentAddress - 4)

            if (opponentPid > 0 and (trainerPartySize >= 1 and trainerPartySize <= 6)) then
                partyAddress = PARTY_ADDRESS + 0x4B7F8 -- Party battle data
                opponentBattleAddress = PARTY_ADDRESS + 0x4BDA8 -- Trainer party battle data
                inBattle = true
            end
        end

		-- Retrieve party Pokémon
        for partySlot = 0, partySize - 1 do
            mon = getPartyPokemon(partyAddress + PARTY_POKEMON_SIZE * partySlot)

            if (mon and mon.speciesId ~= 0) then

				-- teamFullData = teamFullData .. "|" .. printFullData(mon) .. "¤" .. "1"
                partyPokemon = partyPokemon .. "|" .. mon.speciesId .. "¤" .. mon.heldItem .. "¤" .. mon.currentHp .. "¤" .. mon.maxHp .. "¤" .. mon.status
            end
        end

		-- Retrieve PC Pokémon (box + dead)
		while i < (18 * 30) do
            if alivePokemon then
				boxPokemon = boxPokemon .. "|"
			elseif i >= (14 * 30) then
				deadPokemon = deadPokemon .. "|"
			end

			-- If no Pokémon was found in the box, stop parsing alive Pokémon
			if (i % 30 == 0) then
				if emptyBox then
					if alivePokemon then
						alivePokemon = false
						boxPokemon = string.sub(boxPokemon, 1, #boxPokemon - 31) -- Remove last 30 empty Pokémon
					end
				else
					emptyBox = true
				end
			end

            -- Check box slot
            mon = getBoxPokemon(i)

            -- Pokémon found : add it to data file
            if (mon and mon.speciesId ~= 0) then
                emptyBox = false
					
                if (alivePokemon) then
                    boxPokemon = boxPokemon .. mon.speciesId .. "¤" .. mon.heldItem
                else
                    deadPokemon = deadPokemon .. mon.speciesId .. "¤" .. mon.heldItem
                end
            end

            i = i + 1
        end

        -- Retrieve trainer party Pokémon
        if (inBattle) then
            trainerParty = retrieveTrainerTeam(trainerParty, opponentAddress, opponentBattleAddress)

            -- Retrieve double trainer party Pokémon if present
            local doubleOpponentAddress = opponentAddress + 0xB60
            local doubleOpponentBattleAddress = opponentBattleAddress + 0xB60
            local doubleOpponentPid = memory.readdword(doubleOpponentAddress)
            local doubleTrainerPartySize = memory.readbyte(doubleOpponentAddress - 4)

            if (doubleOpponentPid > 0 and (doubleTrainerPartySize >= 1 and doubleTrainerPartySize <= 6)) then
                doubleTrainerParty = retrieveTrainerTeam(doubleTrainerParty, doubleOpponentAddress, doubleOpponentBattleAddress)
            end
        end

		-- Retrieve booleans indicating if trainers have been defeated
		for trainerAddress = TRAINERS_START, TRAINER_END do
			defeatedTrainers = defeatedTrainers .. "|" .. memory.readbyte(trainerAddress)
		end

        -----------------------
        -- TODO next updates --
        -----------------------
		-- -- If in battle, retrieve party/opponent buffs and PP left
		-- if emu:read32(inBattleAddress) ~= 0 then

		-- 	-- Last bit in battle flags is double battle flag
		-- 	isDoubleBattle = emu:read32(battleFlagsAddress) % 2 == 1

		-- 	-- Retrieve all opponents moves and PP
		-- 	opponentMoves = opponentMoves .. getOpponentMoves(activeOpponentAddress) .. (isDoubleBattle and getOpponentMoves(activeSecondOpponentAddress) or "")

		-- 	-- Retrieve all buffs/debuffs
		-- 	opponentBuffs = opponentBuffs .. getStatBuffs(opponentBuffsAddress) .. (isDoubleBattle and getStatBuffs(secondOpponentBuffsAddress) or "")
		-- 	partyBuffs = partyBuffs .. getStatBuffs(partyBuffsAddress) .. (isDoubleBattle and getStatBuffs(secondPartyBuffsAddress) or "")
		-- end

		-- Retrieve pokemonData.txt path from env variable defined by Python script
		local dataFilePath = os.getenv("PLATINUMKAIZODISPLAY_DATAFILE")

		-- Write data in pokemonData.txt
		if dataFilePath then
			local f = io.open(dataFilePath, "w")

			if f then
				f:write(partyPokemon .. "\n" .. boxPokemon .. "\n" .. deadPokemon .. "\n" .. trainerParty .. "\n" .. doubleTrainerParty .. "\n" .. defeatedTrainers)
				f:close()
			else
				displayBuffer:print("Cannot write pokemon data\n")
			end
		else
			displayBuffer:print('Cannot find current folder, run "PlatinumKaizoDisplay.exe" and restart DeSmuME\n')
		end
    end
end

print("Platinum Kaizo Display lua script version " .. getVersion() .. " currently running...")
print("Make sure PlatinumKaizoDisplay.exe is also running !")
gui.register(sendPokemonData)