class ConsoleTiles(object):
    def __new__(cls, *isnt, **interested): #pylint: disable = unused-argument
        raise TypeError("attempt to create instance of static class")
    @classmethod
    def get_tile_character(cls, tile_id):
        error_codes = ("\xa8", "\xbf")
        if hasattr(cls, tile_id):
            return getattr(cls, tile_id)
        for cls2 in cls.expansion_packs:
            tile = cls2.get_tile_character(tile_id)
            if tile not in error_codes:
                return tile
        if hasattr(super(cls), "get_tile_character"):
            return super(cls).get_tile_character(tile_id)
        return error_codes[cls._error_code%len(error_codes)]
    @classmethod
    def attach_expansion_pack(cls, cls2):
        if cls2 not in cls.expansion_packs:
            cls.expansion_packs.append(cls2)
    space = " "
    vwall = "|"
    hwall = "-"
    wall_corner_nw = "-" #In true Rogue style
    wall_corner_ne = "-" #In true Rogue style
    wall_corner_sw = "-" #In true Rogue style
    wall_corner_se = "-" #In true Rogue style
    wall_TeeJnc_up = "-" #In true continuation of Rogue style
    wall_TeeJnc_dn = "-" #In true continuation of Rogue style
    wall_TeeJnc_rt = "|" #In true continuation of Rogue style
    wall_TeeJnc_lt = "|" #In true continuation of Rogue style
    wall_cross = "-" #In true continuation of Rogue style
    vfeature = ":"
    hfeature = "="
    vfeature_open = "-" #Use perpendicular wall chars, per ASCII NetHack
    hfeature_open = "|" #Use perpendicular wall chars, per ASCII NetHack
    #Levels of floor
    floor1 = "."
    floor2 = ","
    floor3 = "/"
    floor4 = "$"
    floor5 = "#"
    user = "@"
    item = "'"
    staircase = ">"
    adversary = "&"
    #
    _error_code = 1
    expansion_packs = []

