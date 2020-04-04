import asyncio
import logging
import sys
import derplib.game as libgame
from derplib.errors import CharacterInUse, InvalidCharacter
from derplib.character import Character, Character_Flags

class derp_game():

    game = libgame.Game()
    game.initial_points = 100
    game.description = 'Welcome to DerpLurk, feel free to derp around.'
    # key: Character name
    # value: (character object, associated streams if connected)
    characters = {}
    # list of rooms in the game
    rooms = {}
    # list of monsters
    monsters = {}

    def initialize_character(self, character, writer):
        name = character.name
        if name in self.characters:
            char, stream = self.characters[name]
            if stream == None:
                self.characters[name] = (char, writer)
                return char
            else:
                raise CharacterInUse(name)
        else:
            valid_character = self.__validate_new_character(character)
            self.characters[name] = (valid_character, writer)
            return character

    def __validate_new_character(self, c):
        s = c.stats
        if s.attack < 0 or s.defense < 0 or s.regen < 0:
            raise InvalidCharacter(c.name, 'Negative stats are not allowed')
        if s.attack + s.defense + s.regen <= self.game.initial_points:
            c.stats.health = 100
            c.stats.gold = 0
            c.stats.current_room = 0
            #new character should be alive and optionally join battle
            newflags = Character_Flags.ALIVE
            newflags += c.flags & Character_Flags.JOIN_BATTLE
            c.flags = newflags
            return c
        else:
            raise InvalidCharacter(c.name, 'Stats are over initial point limit')

    def disconnect_character(self, name):
        c = self.characters[name][0]
        self.characters[name] = (c, None) # remove writer connection

    def get_character_writer(self, name):
        if name in self.characters:
            return self.characters[name][1]
        else:
            return None
