# Requirements:
# - Python >= 3.5
# - pyksnk @ https://github.com/aslemen/pyksnk

import sys
import io
import typing

import pyksnk.mordict as md

#dic: md.Dictionary

# ======
# Parse MOR dictionary file(s)
# ======
with open("/home/twotrees12/NPCMJ/Kusunoki/dictionary/lex/closed.cut") as f:
    dic = md.parse(f.name, f.read())
# === END WITH f ===

# ======
# Filter sfxes
# ======
def match_attrvalue_str(
    attrval: md.Cat_AttrVal, 
    value = str
    ) -> bool:
    p_value = attrval.value
    
    def match_attrvalue_list_item(item: typing.Any):
        if isinstance(item, str):
            return item.find(value) >= 0
        else:
            return False
        # === END IF ===
    # === END ===

    if isinstance(p_value, str):
        return p_value.find(value) >= 0
    elif isinstance(p_value, list):
        return any(map(match_attrvalue_list_item, p_value))
    else:
        return False
    # === END IF ===
# === END ===

dic.contents = filter(
    lambda lex: any(
        map(
            lambda attrval: match_attrvalue_str(attrval, "sfx"),
            lex.cat["scat"]
        )
    ),
    dic.contents
)

# dump it to stdout
res = io.StringIO()
dic.dump_mordict(res)

sys.stdout.write(res.getvalue())