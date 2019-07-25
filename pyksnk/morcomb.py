import typing

import functools
import itertools

import pathlib
import lark
import lark.indenter

import ruamel.yaml as yaml

# ======
# Data classes
# ======
WordAnalysis = str

class WordAnalysisCandidates:
    def __init__(self, alts: typing.Iterable[WordAnalysis]):
        self.alts = list(alts)
    # === END ===

    def is_ambiguous(self):
        return len(self.alts) > 1
    # === EMD ===

    def __str__(self) -> str:
        return "^".join(map(str, self.alts))
    # === END ===

    yaml_tag: str = "!WAC"

    @classmethod
    def to_yaml(cls, 
        representer: yaml.BaseRepresenter, 
        node: "WordAnalysisCandidates"
        ):
        flow_style: bool = not node.is_ambiguous() # Candidates will be dumped in a block if you have more than one.

        return representer.represent_sequence(
            cls.yaml_tag,
            node.alts,
            flow_style = flow_style,
        )
    # === END ===

    @classmethod
    def from_yaml(cls, 
        constructor: yaml.RoundTripConstructor, 
        node: yaml.SequenceNode
        ) -> "WordAnalysisCandidates":
        res = cls([])
        yield res
        gotten = constructor.construct_rt_sequence(
            node = node,
            seqtyp = yaml.comments.CommentedSeq(),
            deep = True
            )
        res.alts = gotten
    # === END ===

# === END CLASS ===

class Word:
    def __init__(self,
        mor_candidates: WordAnalysisCandidates = WordAnalysisCandidates([]),
        comb: str = "",
        penn: str = "",
        ort: str = ""
    ):
        self.mor_candidates = mor_candidates
        self.comb = comb
        self.penn = penn
        self.ort = ort
    # === END ===

    @staticmethod
    def iter_from_columns(
        mor: typing.Iterable[WordAnalysisCandidates],
        comb: typing.Iterable[str],
        penn: typing.Iterable[str],
        ort: typing.Iterable[str],
    ) -> typing.Iterator["Word"] :
        return (
            Word(
                mor_candidates = m,
                comb = c,
                penn = p,
                ort = o,
            )
            for m, c, p, o in itertools.zip_longest(
                mor,
                comb,
                penn,
                ort,
            )
        )
    # === END ===

    @staticmethod
    def list_columns_from_words(
        words: typing.Iterable["Word"]
    ) -> typing.Tuple[
        typing.Union[
            typing.List[WordAnalysisCandidates],
            typing.List[str]
        ]
    ]:
        line_mor: typing.List[WordAnalysisCandidates] = []
        line_comb: typing.List[str] = []
        line_penn: typing.List[str] = []
        line_ort: typing.List[str] = []

        for w in words:
            line_mor.append(w.mor_candidates)
            line_comb.append(w.comb)
            line_penn.append(w.penn)
            line_ort.append(w.ort)

        return line_mor, line_comb, line_penn, line_ort
    # === END ===

    def __repr__(self) -> str:
        return "<WORD object {ort} at {id}>".format(
            ort = self.ort if self.ort else self.comb,
            id = id(self)
        )
    # === END ===

    yaml_tag: str = "!Word"

    @classmethod
    def to_yaml(cls, 
        representer: yaml.BaseRepresenter, 
        node: "Word"
        ):
        return representer.represent_mapping(
            cls.yaml_tag,
            {
                "SynCat": node.penn,
                "Orthography": node.ort,
                "Phon": node.comb,
                "Mors": node.mor_candidates,
            },
            flow_style = False, # Always put in a block
        )
    # === END ===

    @classmethod
    def from_yaml(cls, 
        constructor: yaml.RoundTripConstructor, 
        node: yaml.MappingNode
        ) -> "Word":
        res = cls([], [], [], [])
        yield res
        gotten = yaml.comments.CommentedMap()
        constructor.construct_mapping(
            node = node,
            maptyp = gotten,
            deep = True
            )
        gotten_dict = dict(gotten)

        res.mor_candidates = gotten_dict["Mors"]
        res.comb = gotten_dict["Phon"]
        res.penn = gotten_dict["SynCat"]
        res.ort = gotten_dict["Orthography"]
    # === END ===
# === END CLASS ===

class Sentence:
    def __init__(self,
        id_str: str               = "",
        chi:    str               = "",
        words:  typing.List[Word] = [],
    ):
        self.id_str = id_str
        self.chi = chi
        self.words = words
    # === END ===

    def __str__(self) -> str:
        m, c, p, o = Word.list_columns_from_words(self.words)
        spacer: typing.Mapping[list, str] = (
            lambda li: " ".join(map(str, li))
        )
        filter_spacer: typing.Mapping[list, str] = (
            lambda li: spacer(filter(None, li))
        )
        tabber: typing.Mapping[list, str] = (
            lambda li: "\n\t".join(map(str, li))
        )
        filter_tabber: typing.Mapping[list, str] = (
            lambda li: tabber(filter(None, li))
        )

        return """\
*CHI:\t{chi}
%mor:\t{mor}
%comb:\t{comb}
%penn:\t{penn}
%ort:\t{ort}
@G:\t{num}
""".format(
    chi = self.chi,
    mor = filter_tabber(m),
    comb = filter_spacer(c),
    penn = filter_spacer(p),
    ort = filter_spacer(o),
    num = self.id_str,
)
    # === END ===

    yaml_tag: str = "!Sentence"

    @classmethod
    def to_yaml(cls, 
        representer: yaml.BaseRepresenter, 
        node: "Sentence"
        ):
        return representer.represent_mapping(
            cls.yaml_tag,
            {
                "ID": node.id_str,
                "CHI": node.chi,
                "Words": node.words,
            },
            flow_style = False, # Always put in a block
        )
    # === END ===

    @classmethod
    def from_yaml(cls, 
        constructor: yaml.RoundTripConstructor, 
        node: yaml.MappingNode
        ) -> "Sentence":
        res = cls("", "", [])
        yield res

        gotten = yaml.comments.CommentedMap()
        constructor.construct_mapping(
            node = node,
            maptyp = gotten,
            deep = True
            )
        gotten_dict = dict(gotten)

        res.id_str = gotten_dict["ID"]
        res.chi = gotten_dict["CHI"]
        res.words = gotten_dict["Words"]
    # === END ===
# === END CLASS ===

class Morcomb:
    def __init__(self,
        preambles:      typing.List[str] = [],
        sentences:      typing.List[str] = [],
        postambles:     typing.List[str] = []
    ):
        self.preambles = preambles
        self.sentences = sentences
        self.postambles = postambles
    # === END ===

    def __str__(self) -> str:
        def print_amble(amble: str) -> str:
            return "@{0}\n".format(amble)
        # === END ===

        return (
            "".join(
                itertools.chain(
                    map(print_amble, self.preambles),
                    map(str, self.sentences),
                    map(print_amble, self.postambles)
                )
            )
        )
    # === END ===

    yaml_tag: str = "!Morcomb"

    @classmethod
    def to_yaml(cls, 
        representer: yaml.BaseRepresenter, 
        node: "Morcomb"
        ):
        
        return representer.represent_mapping(
            cls.yaml_tag,
            {
                "preambles": node.preambles,
                "contents": node.sentences,
                "postambles": node.postambles,
            },
            flow_style = False, # Always put in a block
        )
    # === END ===

    @classmethod
    def from_yaml(cls, 
        constructor: yaml.RoundTripConstructor, 
        node: yaml.MappingNode
        ) -> "Morcomb":
        # ref. https://stackoverflow.com/questions/43812020/what-does-deep-true-do-in-pyyaml-loader-construct-mapping/43812995#43812995
        res = cls([], [], [])
        yield res

        gotten = yaml.comments.CommentedMap()
        constructor.construct_mapping(
            node = node,
            maptyp = gotten,
            deep = True
            )
        gotten_dict = dict(gotten)

        res.preambles = gotten_dict["preambles"]
        res.sentences = gotten_dict["contents"]
        res.postambles = gotten_dict["postambles"]
    # === END ===
# === END CLASS ===

# ======
# Dumping to YAML
# ======
def get_YAML_processor() -> yaml.YAML:
    YAML: yaml.YAML = yaml.YAML()
    YAML.register_class(WordAnalysisCandidates)
    YAML.register_class(Word)
    YAML.register_class(Sentence)
    YAML.register_class(Morcomb)

    return YAML
# === END ===

# ======
# Parsing
# ======

# ------
# Auxiliaries
# ------
class __Indenter(lark.indenter.Indenter):
    NL_type:            str                 = "_NEWLINES"
    OPEN_PAREN_types:   typing.List[str]    = []
    CLOSE_PAREN_types:  typing.List[str]    = []
    INDENT_type:        str                 = "_INDENT"
    DEDENT_type:        str                 = "_DEDENT"
    tab_len:            int                 = 4
# === END CLASS ===

# TODO: この種の変換は必ずしも必要ない（lintの場合は特にそう）ので、変換を切り出しておくとよい。
class __Transformer(lark.Transformer):
    def start(self, args):
        return Morcomb(*args)
    # === END ===

    def sentence_list(self, args):
        return args
    # === END ===

    def preambles(self, args):
        return [p.value for p in args]
    # === END ===

    def postambles(self, args):
        return [p.value for p in args]
    # === END ===

    def sentence(self, args: typing.Iterator[lark.Tree]):
        res = {subtree.data:subtree.children for subtree in args}

        res_words: dict = Word.iter_from_columns(
            res["line_mor"],
            map(lambda x: x.value, res["line_comb"]),
            map(lambda x: x.value, res["line_penn"]),
            map(lambda x: x.value, res["line_ort"]),
        )
        # TODO: この手の変換はもう少しlocalにやりたい

        def squash_tokens(li: typing.List[lark.Token]) -> str:
            return "".join(map(lambda x: x.value, li))
        # === END ===

        return Sentence(
            id_str = squash_tokens(res["line_num"]),
            chi = squash_tokens(res["line_chi"]),
            words = list(res_words)
        )
    # === END ===

    def list_mor(self, args):
        return WordAnalysisCandidates(item.value for item in args)
    # === END ===

# === END CLASS ===

# ------
# Parser
# ------
parser: lark.Lark = None
with open(
        pathlib.Path(__file__).parent / "morcomb.lark",
        mode = "r"
    ) as grammar:
    parser = lark.Lark(
        grammar = grammar,
        parser = "lalr",
        postlex = __Indenter(),
        transformer = __Transformer()
    )
# === END WITH grammar ===

def parse(text: str) -> Morcomb:
    return parser.parse(text)
# === END ===
