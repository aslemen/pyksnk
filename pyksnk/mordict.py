import typing
import attr
import abc

import itertools
import collections
import sys
import io
import random

import lark

import pandas as pd
import csv

# ======
# Internal helper functions
# ======

# Generate a random negative integer.
def _gen_rand_neg() -> int:
    return (- random.randint(1, sys.maxsize))
# === END ===

# ======
# Data Types
# ======
@attr.s(
    auto_attribs = True
)
class MorDict_Base(metaclass = abc.ABCMeta):
    """
    An abstract class for all kinds of ingredient in mordict files.

    Attributes
    ----------
    meta : lark.tree.Meta, optional
        Position of the instance is the source file.
        Defaults to `None`.
    comments : typing.List[Comment], optional
        Comments anchored to the instance. 
        Defaults to an empty list rather than `None`.

    Notes
    -----
    Any concrete subclasses are expected to
    implement a function, `dump_mordict`, which dumps their instances back to 
    its morcomb serialization.
    """
    
    meta: typing.Optional[lark.tree.Meta] = attr.ib(
        cmp = False,
        kw_only = True,
        factory = lambda: None
    )

    comments: typing.List["Comment"] = attr.ib(
        cmp = False,
        kw_only = True,
        factory = list
    )

    delimiter_beginning: typing.ClassVar[str]
    """Beginning delimiter in MOR files."""
    delimiter_end: typing.ClassVar[str]
    """End delimiter in MOR files."""
    
    @abc.abstractmethod
    def dump_mordict(
        self,
        buffer: typing.TextIO,
        with_comments: bool = True
    ) -> typing.NoReturn:
        """
        An abstract method
        to serialize and then dump the instance to a text stream
        in the MOR dictionary format. 

        Parameters
        ----------
        buffer : typing.TextIO 
            The stream to dump this into.
        with_commnets : bool, optional
            If `True`, comments anchored to the instance is also dumped.
            Defaults to `True`.
        """
    # === END ===

    def print_mordict(
        self, 
        with_comments: bool = True
    ) -> str:
        """
        Serialize the instance and return the representation.

        Paratmeters
        -----------
        with_comments : bool, optional
            If `True`, comments anchored to the instance is also dumped.
            Defaults to `True`.

        Returns
        -------
        serialization : str
            The resulting string.
        """

        with io.StringIO() as buf:
            self.dump_mordict(buf, with_comments)
            return buf.getvalue()
        # === END WITH ===
    # === END ===

    def __str__(self) -> str:
        return self.print_mordict(with_comments = False)
    # === END ===
# === END abstract CLASS ===

@attr.s(
    cmp = True,     # make this comparable
    frozen = True,  # make this immutable -> hashable
    slots = True,
    auto_attribs = True
)
class MorDict_SingleFixedValue(MorDict_Base):
    """
    An abstract class representing a single fixed value in mordict files.
    Comparable, immutable and hence hashable.

    Attributes
    ----------
    meta : lark.tree.Meta, optional
        Position of the instance is the source file.
        Defaults to `None`.
    comments : typing.List[Comment], optional
        Comments anchored to the instance. 
        Defaults to an empty list rather than `None`.
    value : str
        The value that the instance contain.
    """

    value: str = attr.ib(
        cmp = True,
        kw_only = True
    )

    is_omittable: typing.ClassVar[bool]
    """Indicates whetehr instances can be omitted in MOR dictionary files."""

    def dump_mordict(
        self,
        buffer: typing.TextIO,
        with_comments: bool = True
    ) -> typing.NoReturn: 
        if (not self.is_omittable) or self.value:
            buffer.writelines(
                (
                    self.delimiter_beginning,
                    self.value,
                    self.delimiter_end
                )
            )
        # === END IF ===

        if with_comments:
            if self.comments:
                buffer.write(" ")
            # === END IF ===

            for c in self.comments:
                c.dump_mordict(
                    buffer,
                    with_comments = True
                )
            # === END FOR c ===
        # === END IF ===
    dump_mordict.__doc__ = MorDict_Base.dump_mordict.__doc__
    # === END ===

# === END abstract CLASS ===

@attr.s(
    frozen = True,
)
class MorDict_PandasColumn(MorDict_Base):
    """
    An interface for MorDict ingredients 
    which gives a Pandas column name.

    Being Pandas cells, instances should be hashable
    (which requires being frozen).
    """

    pandas_col_name: typing.ClassVar[str]
    """Column name in Pandas."""
# === END abstract CLASS ===

class Comment(MorDict_SingleFixedValue):
    r"""
    Comment in MOR dictionary files, 
    represented as `% some comments till EOL`.

    Comparable, frozen and hashable.
    
    Attributes
    ----------
    meta : lark.tree.Meta, optional
        Position of the instance is the source file.
        Defaults to `None`.
    comments : typing.List[Comment], optional
        Comments anchored to the instance. 
        Defaults to an empty list rather than `None`.
    value : str
        The comment.
    """

    delimiter_beginning: typing.ClassVar[str] = "% "
    delimiter_end: typing.ClassVar[str] = "\n"
    is_omittable: typing.ClassVar[bool] = True
# === END CLASS ===

class Phon(MorDict_SingleFixedValue, MorDict_PandasColumn):
    r"""
    Surface form of a word, 
    represented as a bare string in MOR dictionary files.

    Comparable, frozen and hashable.
    
    Attributes
    ----------
    meta : lark.tree.Meta, optional
        Position of the instance is the source file.
        Defaults to `None`.
    comments : typing.List[Comment], optional
        Comments anchored to the instance. 
        Defaults to an empty list rather than `None`.
    value : str
        The surface form.
    """
    delimiter_beginning: typing.ClassVar[str] = ""
    delimiter_end: typing.ClassVar[str] = ""
    pandas_col_name: typing.ClassVar[str] = "Phon"
    is_omittable: typing.ClassVar[bool] = False

    # def __hash__(self): return hash(self.value)
# === END CLASS ===

@attr.s(
    cmp = True,     # make this comparable
    frozen = True,
    cache_hash = True,
    slots = True,
    auto_attribs = True
)
class Cat_AttrVal(MorDict_Base):
    r"""
    Feature-value pair of the 
    category information of a word, 
    represented as `[key value]` in MOR dictionary files.

    Comparable, frozen and hashable.
    
    Attributes
    ----------
    meta : lark.tree.Meta, optional
        Position of the instance is the source file.
        Defaults to `None`.
    comments : typing.List[Comment], optional
        Comments anchored to the instance. 
        Defaults to an empty list rather than `None`.
    key : str
        The feature name.
    value : typing.Union[str, typing.List[str]]
        The value, either a string or a list thereof.
    """
    delimiter_beginning: typing.ClassVar[str] = "["
    delimiter_end:       typing.ClassVar[str] = "]"

    key: str = attr.ib(
        cmp = True,
        kw_only = True
    )
    value: typing.Union[str, typing.List[str]] = attr.ib(
        cmp = True,
        kw_only = True
    )

    def dump_mordict(
        self,
        buffer: typing.TextIO,
        with_comments: bool = True
    ) -> typing.NoReturn:
        buffer.writelines(
            (
                self.delimiter_beginning,
                self.key,
                " "
            )
        )

        if isinstance(self.value, list):
            buffer.writelines(" ".join(self.value))
        else:
            buffer.write(str(self.value))
        # === END IF ===

        buffer.write(self.delimiter_end)
    # === END ===
# === END CLASS ===

@attr.s(
    cmp = True,
    frozen = True,
    cache_hash = True,
    slots = True,
    auto_attribs = True
)
class Cat(MorDict_PandasColumn):
    r"""
    Category information of a word, 
    represented as `{[key1 value1][key2 value2]...}` in MOR dictionary files.

    Comparable, frozen and hashable.
    Subscriptable. 
    The subscription operator `Cat["some key"]` returns an **iterator** of `Cat_AttrVal` rather than a single instance of it.
    This is necessitated by an unusual (but possible) kind of case
        that a category has a duplicated feature ascription
        (e.g. `[scat n][scat v]`),
        in which more than one feature is to be returned.
    A consequence is that when a given key is not found in the key-value set,
        the subscription operator does a vacuous iteration
        instead of raising a `KeyError`.
    
    Attributes
    ----------
    meta : lark.tree.Meta, optional
        Position of the instance is the source file.
        Defaults to `None`.
    comments : typing.List[Comment], optional
        Comments anchored to the instance. 
        Defaults to an empty list rather than `None`.
    attrvals : typing.Tuple[Cat_AttrVal], optional
        The set of the features and their values.
        Defaults to an empty `Tuple`.
    """

    delimiter_beginning:    typing.ClassVar[str] = "{"
    delimiter_end:          typing.ClassVar[str] = "}"
    pandas_col_name:        typing.ClassVar[str] = "Category"
    is_omittable:           typing.ClassVar[bool] = False
    
    attrvals: typing.Tuple[Cat_AttrVal] = attr.ib( 
        cmp = True,
        kw_only = True,
        factory = tuple
    )

    def dump_mordict(
        self,
        buffer: typing.TextIO,
        with_comments: bool = True
    ) -> typing.NoReturn:
        buffer.write(self.delimiter_beginning)
        for attrval in self.attrvals:
            attrval.dump_mordict(buffer, with_comments)
        # === END FOR attrval ===

        buffer.write(self.delimiter_end)

        if with_comments:
            if self.comments:
                buffer.write(" ")
            # === END IF ===

            for c in self.comments:
                c.dump_mordict(
                    buffer,
                    with_comments = True
                )
            # === END FOR c ===
        # === END IF ===
    # === END ===

    def __getitem__(self, key: str) -> typing.Iterator[Cat_AttrVal]:
        return filter(lambda item: item.key == key, self.attrvals)
    # === END ===
# === END CLASS ===

class Sem(MorDict_SingleFixedValue, MorDict_PandasColumn):
    r"""
    English Translation of a word, 
    represented as `=sem=` in MOR dictionary files.

    Comparable, frozen and hashable.
    
    Attributes
    ----------
    meta : lark.tree.Meta, optional
        Position of the instance is the source file.
        Defaults to `None`.
    comments : typing.List[Comment], optional
        Comments anchored to the instance. 
        Defaults to an empty list rather than `None`.
    value : str
        The english translation.
    """
    delimiter_beginning:    typing.ClassVar[str]  = "="
    delimiter_end:          typing.ClassVar[str]  = "="
    is_omittable:           typing.ClassVar[bool] = True
    pandas_col_name:        typing.ClassVar[str]  = "Overall Semantics"
    # def __hash__(self): return hash(self.value)
# === END CLASS ===

class Gloss(MorDict_SingleFixedValue, MorDict_PandasColumn):
    r"""
    Lemmatization of a word, 
    represented as `"gloss"` in MOR dictionary files.

    Comparable, frozen and hashable.
    
    Attributes
    ----------
    meta : lark.tree.Meta, optional
        Position of the instance is the source file.
        Defaults to `None`.
    comments : typing.List[Comment], optional
        Comments anchored to the instance. 
        Defaults to an empty list rather than `None`.
    value : str
        The lemmatization.
    """
    delimiter_beginning:    typing.ClassVar[str]  = '"'
    delimiter_end:          typing.ClassVar[str]  = '"'
    is_omittable:           typing.ClassVar[bool] = True
    pandas_col_name:        typing.ClassVar[str]  = "Morphological Analysis"
    # def __hash__(self): return hash(self.value)
# === END CLASS ===

@attr.s(
    cmp = True,
    frozen = True,
    auto_attribs = True
)
class Lex_Entry(MorDict_Base):
    r"""
    Word entry in MOR dictionary files.

    Comparable, frozen and hashable.
    
    Attributes
    ----------
    meta : lark.tree.Meta, optional
        Position of the instance is the source file.
        Defaults to `None`.
    comments : typing.List[Comment], optional
        Comments anchored to the instance. 
        Defaults to an empty list rather than `None`.
    phon : Phon
    cat : Cat
    sem : Sem, optional
    gloss : Gloss, optional
    enabled : bool, optional
        If `False`, the entry will be disabled and commented out in serialization processes.
        Defaults to `True`.

    Notes
    -----
    The motivation to establish the `enabled` attribute 
    comes from the need to preserved anchored comments 
    in the course of manupilation of a whole dictionary.
    There are cases in which
    it is necessary to delete a word entry in a dictionary
    without comments anchored there also being removed.
    Switching the `enabled` attribute to `False` enables you
    to keep those comments by masking the entry instaed of deleting it.
    """
    phon: Phon = attr.ib(
        cmp = True,
        kw_only = True
    )
    cat: Cat = attr.ib(
        cmp = True,
        kw_only = True
    )
    sem: Sem = attr.ib(
        cmp = True,
        kw_only = True,
        factory = lambda: Sem(
            meta = None, 
            comments = [], 
            value = ""
        )
    )
    gloss: Gloss = attr.ib(
        cmp = True,
        kw_only = True,
        factory = lambda: Gloss(
            meta = None, 
            comments = [], 
            value = ""
        )
    )
    enabled: bool = attr.ib(
        cmp = False,
        kw_only = True,
        factory = lambda: True
    )

    delimiter_beginning: typing.ClassVar[str] = ""
    delimiter_end:       typing.ClassVar[str] = ""

    def dump_mordict(
        self,
        buffer: typing.TextIO,
        with_comments: bool = True
    ) -> typing.NoReturn:
        if self.enabled:
            self.phon.dump_mordict(buffer, with_comments)
            buffer.write("\t")
            self.cat.dump_mordict(buffer, with_comments)

            if self.sem.value:
                buffer.write(" ")
            # === END IF ===
            self.sem.dump_mordict(buffer, with_comments)

            if self.gloss.value:
                buffer.write(" ")
            # === END IF ===
            self.gloss.dump_mordict(buffer, with_comments)
        else:
            # discard contents and just dump comments
            disabled_entry: io.StringIO = io.StringIO()

            self.phon.dump_mordict(disabled_entry, with_comments)
            buffer.write("\t")
            self.cat.dump_mordict(disabled_entry, with_comments)

            if self.sem.value:
                buffer.write(" ")
            # === END IF ===
            self.sem.dump_mordict(disabled_entry, with_comments)

            if self.gloss.value:
                buffer.write(" ")
            # === END IF ===
            self.gloss.dump_mordict(disabled_entry, with_comments)

            disabled_entry_res: str = disabled_entry.getvalue(
            ).replace(
                "\r\n", " "
            ).replace(
                "\n", " "
            ).replace(
                "\r", " "
            )

            buffer.writelines(
                (
                    "% DISABLED: ",
                    disabled_entry_res,
                )
            )
        # === END IF ===

        if with_comments:
            for c in self.comments:
                c.dump_mordict(
                    buffer,
                    with_comments = True
                )
            # === END FOR c ===
        # === END IF ===

        if buffer.seekable():
            buffer.seek(buffer.tell() - 1)
            last_char: str = buffer.read()
            if last_char not in "\n\r":
                buffer.write("\n")
            # === END IF ===
        else:
            buffer.write("\n")
        # === END IF ===
    dump_mordict.__doc__ = MorDict_Base.dump_mordict.__doc__
    # === END ===

    def to_tuple(
        self
    ) -> typing.Iterator[
        typing.Union[MorDict_PandasColumn, bool]
    ]:
        """
        Convert all the non-meta attributes into a tuple

        Returns
        ------
        values: typing.Tuple[Phon, Cat, Sem, Gloss, bool]
            `phon`, `cat`, `sem`, `gloss` and `enabled`.
        """
        return (
            self.phon,
            self.cat,
            self.sem,
            self.gloss,
            self.enabled
        )
    # === END ===

    def get_dataframe_index(self, name: str):
        """
        he elements of the Pandas row index 
        ascribed to this instance.
        The index consists of the following three items:

        dict_name : str
            Name of the dictionary that this entry belongs to.
            Given by the argument.
        line : int
            Line number in the source file, 
            retrived from the `meta` attribute.
            If it is not available, 
            a negative random integer is assigned instead.
        column : int
            Column number in the source file, 
            retrived from the `meta` attribute.
            If it is not available, 
            a negative random integer is assigned instead.

        Parameters
        ---------
        name : str
            Name of the dictionary that this entry belongs to. 

        Returns
        ------
        index : typing.Tuple[str, int, int]
            The complex index tuple explained above.
        """
        meta: typing.Optional[lark.tree.Meta] = self.meta
        if meta and not meta.empty:
            return (name, meta.line, meta.column)
        else:
            return (name, _gen_rand_neg(), _gen_rand_neg())
    # === END ===
# === END CLASS ===

pandas_index_names: typing.Tuple[str] = (
    "dict_name",
    "line",
    "column"
)
"""
Fixed list of index names of a MOR dictionary in a Pandas DataFrame.
"""

pandas_col_names: typing.Tuple[str] = (
    Phon.pandas_col_name,
    Cat.pandas_col_name,
    Sem.pandas_col_name,
    Gloss.pandas_col_name,
    "enabled"
)
"""
Fixed list of column names of a MOR dictionary in the Pandas DataFrame form.
"""

pandas_col_names_overt: typing.Tuple[str] = (
    Phon.pandas_col_name,
    Cat.pandas_col_name,
    Sem.pandas_col_name,
    Gloss.pandas_col_name,
)
"""
Fixed list of column names of a MOR dictionary which originally appears in a MOR file.
"""

def dump_mordict_pandas(
        df: pd.DataFrame,
        path_or_buf: typing.Union[str, typing.TextIO], 
    ) -> typing.NoReturn:
    """
    Dump a detailed representation of a 
    MOR dictionary in the Pandas DataFrame form.

    Parameters
    ---------
    df : pd.DataFrame
        MOR dictionary in the Pandas DataFrame form.
    path_or_buf : typing.Union[str, typing.TextIO]
        Either a path to a file or a writable stream 
        to which the dictionary is dumped.
    """
    df.to_csv(
        path_or_buf = path_or_buf,
        columns = pandas_col_names_overt,
        header = True,
        index = True,
        sep = "\t",
        quoting = csv.QUOTE_NONE
    )
# === END ===

class Preamble(MorDict_SingleFixedValue):
    r"""
    Preamble of a MOR dictionary, 
    represented as `@amb content till EOL` in MOR dictionary files.

    Comparable, frozen and hashable.
    
    Attributes
    ----------
    meta : lark.tree.Meta, optional
        Position of the instance is the source file.
        Defaults to `None`.
    comments : typing.List[Comment], optional
        Comments anchored to the instance. 
        Defaults to an empty list rather than `None`.
    value : str
        The content.
    """
    delimiter_beginning: typing.ClassVar[str] = "@"
    delimiter_end: typing.ClassVar[str] = "\n"
    is_omittable: typing.ClassVar[bool] = True
# === END CLASS ===

@attr.s(
    auto_attribs = True
)
class Dictionary(MorDict_Base):
    r"""
    MOR dictionary as a whole.

    Incomparable, mutable and unhashable.
    
    Attributes
    ----------
    meta : lark.tree.Meta, optional
        Position of the instance is the source file.
        Defaults to `None`.
    comments : typing.List[Comment], optional
        Comments anchored to the instance. 
        Defaults to an empty list rather than `None`.
    name : str, optional
        Name of the dictionary.
        Defaults to a 7-digit hexadecimal random number.
    preambles : typing.List[Preamble], optional
        List of preambles.
        Defaults to an empty list.
    contents : typing.List[Lex_Entry], optional
        List of word entries.
        Defaults to an empty list.
    """
    name: str = attr.ib(
        cmp = True,
        kw_only = True,
        factory = lambda: "<UNTITLED>{0:0=7X}".format(
            random.randint(1, 16^7)
        ) 
    )

    preambles: typing.List[Preamble] = attr.ib(
        cmp = False,
        kw_only = True,
        factory = list
    )

    contents: typing.List[Lex_Entry] = attr.ib(
        cmp = True,
        kw_only = True,
        factory = list
    )
    # === EMD ===

    def dump_mordict(
        self,
        buffer: typing.TextIO,
        with_comments: bool = True
    ):
        for item in itertools.chain(
                self.comments,
                self.preambles,
                self.contents
        ):
            item.dump_mordict(
                buffer,
                with_comments = with_comments
            )
        # === END FOR item ===
    dump_mordict.__doc__ = MorDict_Base.dump_mordict.__doc__
    # === END ===

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert this dictionary to a Pandas DataFrame.

        Returns
        -------
        df : pd.DataFrame
            The Pandas DataFrame.
        """
        data: typing.Iterator[typing.Tuple[Phon, Cat, Sem, Gloss, bool]] = (
            map(
                lambda lex: tuple(lex.to_tuple()),
                self.contents
            )
        )
        index: typing.Iterator[typing.Tuple[str, int, int]] = (
            map(
                lambda lex: tuple(lex.get_dataframe_index(self.name)),
                self.contents
            )
        )

        return pd.DataFrame(
            data,
            columns = pandas_col_names,
            index = pd.MultiIndex.from_tuples(
                tuples = index, 
                names = pandas_index_names
            ),
        )
    # === END ===

    @staticmethod
    def dataframe_to_entries(
        df: pd.DataFrame
    ) -> typing.List[Lex_Entry]:
        """
        Convert a Pandas DataFrame back to a list of `Lex_Entry`.
        Note that the indices (containg the source file name,
             the position therein, etc.)
             are totally discarded.

        Parameters
        ---------
        df : pd.DataFrame
            MOR dictionary having been converted to a DataFrame. 
    
        Returns
        -------
        lexs : typing.List[Lex_Entry]
            List of the lexical entries in the given DataFrame.
        """
        return [
            Lex_Entry(
                    phon = row[Phon.pandas_col_name],
                    cat = row[Cat.pandas_col_name],
                    sem = row[Sem.pandas_col_name],
                    gloss = row[Gloss.pandas_col_name],
                    enabled = row["enabled"],
                    meta = None,
                    comments = []
            )
            for _, row in df.iterrows()
        ]
    # === END ===

    def update_with_dataframe(
        self, 
        df: pd.DataFrame
    ) -> typing.NoReturn:
        """
        Overwrite the contents with an external Pandas DataFrame.

        Parameters
        ---------
        df : pd.DataFrame
            MOR dictionary having been converted to a DataFrame. 
    
        """
        self.contents = self.dataframe_to_entries(df)
    # === END ===

    @staticmethod
    def from_dataframe(
            comments: typing.List[Comment],
            meta: lark.tree.Meta,
            preambles: typing.List[Preamble],
            df: pd.DataFrame,
            name: str = ""
    ) -> "Dictionary":
        return Dictionary(
            comments = comments,
            meta = meta,
            preambles = preambles,
            contents = Dictionary.dataframe_to_entries(df),
            name = name
        )
    # === END ===
# === END CLASS ===

# ======
# Parsing
# ======

# ------
# Auxiliaries
# ------
@lark.visitors.v_args(meta = True)
class __Transformer(lark.Transformer):
    def start(
            self, 
            children: typing.Iterator[typing.Any],
            meta: lark.tree.Meta
        ) -> Dictionary:
        return Dictionary(
            **dict(children), 
            meta = meta
        )
    # === EMD ===

    def comments_init(
        self,
        children: typing.Iterator[typing.Any],
        meta: lark.tree.Meta # to be discarded
        ) -> typing.Tuple[str, typing.List[Comment]]:
        return (
            "comments",
            children
        )
    # === EMD ===

    def adj_comment(
        self, 
        children: typing.Iterator[typing.Any],
        meta: lark.tree.Meta
        ) -> Comment:
        return Comment(
            meta = meta,
            value = "".join(
                map(
                    lambda a: str(a).strip(),
                    children
                )
            ), 
            comments = []
        )
    # === END ===

    def preambles(
        self, 
        children: typing.Iterator[typing.Any],
        meta: lark.tree.Meta # to be discarded
        ) -> typing.List[Preamble]:
        return ("preambles", children)
    # === EMD ===

    def entries(self, 
        children: typing.Iterator[typing.Any],
        meta: lark.tree.Meta # to be discarded
    ) -> typing.Tuple[str, typing.List[Lex_Entry]]:
        return ("contents", children)
    # === END ===

    def line(
        self, 
        children: typing.Iterator[typing.Any],
        meta: lark.tree.Meta
        ) -> Lex_Entry:
        return Lex_Entry(
            **dict(children), 
            enabled = True,
            meta = meta, 
            comments = []
        )
    # === END ===

    def item_phon(
            self, 
            children: typing.Iterator[typing.Any],
            meta: lark.tree.Meta
        ) -> Phon:
        return (
            "phon",
            Phon(
                meta = meta,
                value = str(children[0]),
                comments = children[1:]
            )
        )
    # === END ===

    def item_cat_attr(
        self, 
        children: typing.Iterator[typing.Any],
        meta: lark.tree.Meta
    ) -> str:
        return str(children[0])
    # === END ===

    def item_cat_values(
        self, 
        children: typing.Iterator[typing.Any],
        meta: lark.tree.Meta
    ) -> typing.List[str]:
        return list(map(str, children))
    # === END ===

    def item_cat_attrval(
        self,
        children: typing.Iterator[typing.Any],
        meta: lark.tree.Meta
    ) -> Cat_AttrVal:
        key = children[0]
        vals = children[1]
        comments = children[2:]

        val_res: typing.Union[str, typing.List[str]]
        val_len: int = len(vals)

        if val_len == 0:
            val_res = ""
        elif val_len == 1:
            val_res = vals[0]
        else:
            val_res = vals
        # === END IF ===

        return Cat_AttrVal(
            key = key,
            value = val_res,
            meta = meta,
            comments = comments,
        )
    # === END ===

    def item_cat_attrval_list(
            self, 
            children: typing.Iterator[typing.Any],
            meta: lark.tree.Meta
    ) -> typing.Tuple[Cat_AttrVal]:
        return tuple(children)
    # === END ===

    def item_cat(
            self, 
            children: typing.Iterator[typing.Any],
            meta: lark.tree.Meta
    ) -> Cat:
        attrval_list: typing.Tuple[Cat_AttrVal] = children[0]
        comments: typing.List[Comment] = children[1:]

        return (
            "cat", 
            Cat(
                meta = meta,
                comments = comments,
                attrvals = attrval_list
            )
        )
    # === END ===

    def item_sem(
            self, 
            children: typing.Iterator[typing.Any],
            meta: lark.tree.Meta
        ) -> Sem:
        res_str: str = ""
        comments: typing.List[Comment] = []

        if len(children) > 0:
            init_arg: lark.Token  = children[0]

            if isinstance(init_arg, lark.Token) and init_arg.type == "SEM":
                res_str = str(init_arg)
                comments = children[1:]
            # === END IF ===
        # === END IF ===

        return (
            "sem", 
            Sem(
                meta = meta,
                value = res_str, 
                comments = comments
            )
        )
    # === END ===

    def item_gloss(
            self, 
            children: typing.Iterator[typing.Any],
            meta: lark.tree.Meta
        ) -> Gloss:
        res_str: str = ""
        comments: typing.List[Comment] = []

        if len(children) > 0:
            init_arg: lark.Token = children[0]

            if init_arg.type == "GLOSS":
                res_str = str(init_arg)
                comments = children[1:]
            # === END IF ===
        # === END IF ===
    # === END IF ===

        return (
            "gloss",
            Gloss(
                meta = meta,
                value = res_str, 
                comments = comments
            )
        )
    # === END ===

    def item_preamble(
        self, 
        children: typing.Iterator[typing.Any],
        meta: lark.tree.Meta
        ) -> Preamble:
        return Preamble(
            meta = meta,
            value = str(children[0]),
            comments = children[1:]
        )
    # === END ===
# === END CLASS ===

__transformer_instance: __Transformer = __Transformer()

# ------
# Parser
# ------
_grammar: str = (
    # ======
    # Lexers
    # ======

    # ------
    # Literals
    # ------
    r"""
PREAMBLE:       /[^%\r\n]+/

PHON:           /\w[^\s{%]*/
CAT_ATTR:       /[^{\[\]%\s]+/
CAT_VALUE:      /[^{\[\]%\s]+/
SEM:            /[^=%]+/
GLOSS:          /[^"%]+/
COMMENT:        /[^\r\n]+/
    """
    
    # ------
    # Spaces
    # ------
    r"""
_WS_INLINE:        /[ \t\f]+/
%ignore _WS_INLINE
_EOL:       /(\r\n?|\r?\n)/
    """

    # ======
    # Items
    # ======
    r"""
adj_comment:        "%" COMMENT?                _EOL+
 
item_phon:          PHON                        _EOL* adj_comment*
item_cat_attr:      CAT_ATTR                    // _EOL* adj_comment*
item_cat_values:    CAT_VALUE*                  // _EOL* adj_comment*
item_cat_attrval:   "[" item_cat_attr item_cat_values "]" _EOL* adj_comment*
// TODO: check whether MOR allows interleaving EOLs

item_cat_attrval_list: item_cat_attrval*        // _EOL* adj_comment*
item_cat:           "{" item_cat_attrval_list "}"   _EOL* adj_comment*
item_sem:           "=" SEM? "="                _EOL* adj_comment*
item_gloss:         "\"" GLOSS? "\""            _EOL* adj_comment*

item_preamble:      "@" PREAMBLE     (_EOL+ | adj_comment)  adj_comment*
    """

    # ======
    # Lines
    # ======
    r"""
line:           item_phon item_cat item_sem? item_gloss? 
    """

    # ======
    # Document
    # ======
    r"""
entries:        line*
preambles:      item_preamble*
comments_init:  adj_comment*
start:          _EOL* comments_init preambles _EOL* entries _EOL*
    """
)

parser: lark.Lark = lark.Lark(
    grammar = _grammar,
    parser = "lalr",
    propagate_positions = True,
)
"""
A Lark parser for MOR dictionary files.
"""

# ------
# Executor
# ------
def parse_raw(text: str) -> lark.Tree:
    """
    Parse a MOR dicionary file and return a raw Lark Tree.

    Parameters
    ---------
    text : str
        Source text.
    
    Returns
    -------
    tree : lark.Tree
        A raw Lark Tree.

    See Also
    --------
    parse
    """
    return parser.parse(text)
# === END ===

def parse(name: str, text: str) -> Dictionary:
    """
    Parse a MOR dicionary file and return a structured Python object.

    Parameters
    ---------
    name : str
        Name of the source file or stream.
    text : str
        Source text.
    
    Returns
    -------
    dictionary : Dictionary
        The Python object representing the input text.

    See Also
    --------
    parse_raw
    """
    res: Dictionary = __transformer_instance.transform(parse_raw(text))
    res.name = name
    return res
# === END ===