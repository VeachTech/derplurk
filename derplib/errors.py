class Error(Exception):
    pass

class CharacterInUse(Error):
    def __init__(self, name):
        self.name = name

class InvalidCharacter(Error):
    def __init__(self, name, message):
        self.name = name
        self.message = message