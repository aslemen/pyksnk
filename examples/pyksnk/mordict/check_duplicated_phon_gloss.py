# Requirements:
# - Python >= 3.5
# - pyksnk @ https://github.com/aslemen/pyksnk

import sys
import io
import typing

import pyksnk.mordict as md
import pandas as pd

#dic: md.Dictionary

# ======
# Parse MOR dictionary file(s)
# ======
with open("/home/twotrees12/NPCMJ/Kusunoki/dictionary/lex/entries.cut") as f:
    dic = md.parse(f.name, f.read())
# === END WITH f ===

# ======
# Convert the parsed dictionary to a Pandas DataFrame
# ======
dic_pd = dic.to_dataframe() # type: pd.DataFrame

# ======
# Making a mask (a Pandas series of booleans) on those entries 
#     based on whether they are duplicated
# ======

# Note: An easiest way would be using DataFrame.duplicated(subset, keep = False),
#   where subset is a list of the names of those columns on which you want to detect duplication.
#   However, it is kind of "loose" in the sense that even duplication on some (but not all) of those columns would be counted (i.e. duplication are deci)
#
#mask_dup: pd.Series = dic_pd.duplicated(
#    subset = [
#        md.Phon.pandas_col_name,
#        md.Gloss.pandas_col_name
#    ],
#    keep = False
#)

#   For a more "rigid" detection, you can create a "product" column (using tuple) or a "hash" column taking all those columes into calculation beforehand and then procced to check that column.

scats = dic_pd[md.Cat.pandas_col_name].apply(
        lambda c: tuple(map(lambda kv: kv.value, c["scat"]))
) # type: pd.Series

tuple_check_dup = zip(
    dic_pd[md.Phon.pandas_col_name],
    scats,
    dic_pd[md.Sem.pandas_col_name],
) # type: typing.Iterator[tuple]

dic_pd["check_dup"] = list(tuple_check_dup)
dic_pd["touch"] = dic_pd.index.get_level_values("line").map(lambda x: x > 10000)

# Grouping
dic_pd_gr = (
    dic_pd.groupby("check_dup")
) # type: pd.core.groupby.generic.DataFrameGroupBy

def del_redundant(df: pd.DataFrame) -> pd.DataFrame:
    having_comp = df[md.Cat.pandas_col_name].apply(
        lambda c: len(tuple(c["comp"]))
    )

    having_gloss = df[md.Gloss.pandas_col_name].apply(
        lambda c: int(bool(c.value))
    )
    score = having_comp + having_gloss # type: pd.Series

    df.loc[
        (
            df["touch"] 
            & (score != score.max())
        ),
        "enabled"
    ] = False

    return df
# === END ===

# scoring entries, keeping the highest one and discard the others
dic_discard_redundants = dic_pd_gr.apply(del_redundant) # type: pd.DataFrame

# ======
# Dump the result
# ======

# push the dataframe back to the original dictionary
dic.update_with_dataframe(dic_discard_redundants)

# dump it to stdout
res = io.StringIO()
dic.dump_mordict(res)

sys.stdout.write(res.getvalue())