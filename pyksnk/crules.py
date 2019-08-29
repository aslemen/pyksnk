import typing

import attr
import functools
import itertools

import io
import re
import random
import lark

_plantuml_rename_table = str.maketrans({
    "-": "_"
})

@attr.s(cmp = False)
class CRULE_Clause:
    conditions = attr.ib(
        type = typing.List[str] # tentative
    )

    resultcat = attr.ib(
        type = str
    )

    rulepackages = attr.ib(
        type = typing.List[str]
    )
# === END CLASS ===

@attr.s(cmp = False)
class CRULE:
    name = attr.ib(
        type = str
    )

    ctype = attr.ib(
        type = str
    )

    variable_defs = attr.ib(
        factory = dict,
        repr = False,
        type = typing.Dict[str, "_sre.SRE_Pattern"]
    )

    clauses = attr.ib(
        factory = list,
        repr = False,
        type = typing.List[CRULE_Clause]
    )

    def dump_plantuml(self, stream: typing.TextIO) -> typing.NoReturn:
        stream.writelines([
            "state ", self.name.translate(_plantuml_rename_table), " {\n",
            "start\n"
        ]) 
        
        for clause in self.clauses:
            stream.writelines([
                ":", "∧".join(map(str, clause.conditions)), ";\n"
            ])

        # === END FOR clause ===

        stream.writelines([
            "stop\n",
            "}\n"
        ])
# === END CLASS ===

Preamble = str

@attr.s(cmp = False)
class CRULE_Set:
    name = attr.ib(
        factory = lambda: "<UNTITLED>{0:0=7X}".format(
            random.randint(1, 16^7)
        ),
        type = str
    )

    preambles = attr.ib(
        factory = list,
        type = typing.List[Preamble]
    )

    rules = attr.ib(
        factory = dict,
        type = typing.Dict[str, CRULE]
    )

    def dump_plantuml(self, stream: typing.TextIO) -> typing.NoReturn:
        stream.writelines([
            "@startuml\n",
            "title ", self.name.translate(_plantuml_rename_table), "\n",
            "a --> b\n"
        ])

        for rule in self.rules.values():
            rule.dump_plantuml(stream)
        # === END FOR rule ===

        stream.write("@enduml\n")
# === END CLASS ===

# ======
# Parsing
# ======
class __Transformer(lark.Transformer):
    def document(self, args) -> CRULE_Set:
        return CRULE_Set(
            preambles = args[0],
            rules = args[1]
        )
    # === END ===
    def rule_action_set(
        self,
        args: list
    ) -> typing.Dict[str, typing.Any]:
        res = {
            "resultcat": args[0]
        }

        if len(res) > 1:
            res["rulepackages"] = args[1]
        # === END IF ===

        return res
    # === END ===

    def rule_resultcat(
        self,
        args
    ) -> str:
        return "".join(args)
        # tentative
    # === END ===

    def rulepackages(
        self, 
        args: typing.Iterable[lark.Token]
    ) -> typing.List[str]:
        return list(str(x) for x in args)
    # === END ===

    def item_variable_declaration(
        self, 
        args
    ) -> typing.Tuple[typing.Union[str, "_sre.SRE_Pattern"]]:
        return (str(args[0]), re.compile(args[1]))
    # === END ===

    def variable_declarations(
        self, 
        args: typing.Tuple[typing.Union[str, "_sre.SRE_Pattern"]]
    ) -> typing.Dict[str, "_sre.SRE_Pattern"]:
        return dict(args)
    # === END ===

    def rule_name(self, args) -> str:
        return "".join(args)
    # === END ===

    def rule_ctype(self, args) -> str:
        return "".join(args)
    # === END ===

    def item_rule_clause(self, args) -> CRULE_Clause:
        if len(args) > 2:
            rulepackages = args[2]
        else:
            rulepackages = list()
        # === END IF ===

        return CRULE_Clause(
            conditions = args[0],
            resultcat = args[1],
            rulepackages = rulepackages
        )
    # === END ===

    def rule_clauses(
        self, 
        args: typing.List[CRULE_Clause]
    ) -> typing.List[CRULE_Clause]:
        return args
    # === END ===

    def item_rule_condition(self, args) -> str:
        # tentative
        return "".join(args)
    # === END ===

    def rule_conditions(self, args) -> typing.List[str]:
        return args
    # === END ===

    def item_rule(self, args) -> CRULE:
        return CRULE(
            name = args[0],
            ctype = args[1],
            variable_defs = args[2],
            clauses = args[3],
        )

    def rules(self, args) -> typing.Dict[str, CRULE]:
        return {x.name : x for x in args}
    # === END ===

    def item_preamble(self, args) -> str:
        return "".join(args)
    # === END ===

    def preambles(
        self, 
        args: typing.List[str]
    ) -> typing.List[str]:
        return args
    # === END ===

# === END CLASS ===

_grammar = (
    # ======
    # Lexers
    # ======

    # ------
    # Literals
    # ------
    r"""
NAMECHAR: /[a-zA-Z0-9\^&+\-_:@.\/]/
NAMECHARS: NAMECHAR+
CHARS:     /[^\s]+/
ANYCHARS:  /[^\r\n]+/
REGEX:     ANYCHARS
CTYPE: "START" | "END" | "-" | "#" | "+" | "$"
    """


    # ------
    # Linebreaks
    # ------
    r"""
_EOL: /(\r\n?|\r?\n)/
_COMMENT: "%" /[^\r\n]+/? _EOL

_PERIOD: (_EOL | _COMMENT)+
    """

    # ------
    # Spaces
    # ------
    r"""
%import common.WS_INLINE -> _WS_INLINE
%ignore _WS_INLINE
_LINE_CONT: /\\/ _EOL
%ignore _LINE_CONT
    """

    # ======
    # Items
    # ======
    r"""
variable_ref: "$" ( NAMECHAR | "(" NAMECHARS ")" )
feature: "[" CHARS CHARS "]"
feature_spec: "[" (CHARS CHARS | CHARS ("AND" | "OR") CHARS+) "]"
feature_name_ref: "[" CHARS "]"
    """

    r"""
rule_name: "RULENAME:" NAMECHARS _PERIOD
rule_ctype: "CTYPE:" CTYPE _PERIOD

item_variable_declaration: NAMECHARS "=" REGEX _PERIOD
variable_declarations: item_variable_declaration*

item_rule_condition: ANYCHARS _PERIOD // tentative
rule_resultcat: "RESULTCAT" "=" ANYCHARS _PERIOD // tentative
rulepackages: "RULEPACKAGE" "=" "{" (NAMECHARS ( "," NAMECHARS )* )? "}" _PERIOD
rule_conditions: item_rule_condition*

item_rule_clause: "if" _PERIOD rule_conditions "then" _PERIOD rule_resultcat rulepackages?
rule_clauses: item_rule_clause*
item_rule: rule_name rule_ctype variable_declarations rule_clauses
    """

    r"""
item_preamble: "@" ANYCHARS _PERIOD
preambles: item_preamble*
rules: item_rule*
document: preambles rules
    """
)

parser = lark.Lark(
    grammar = _grammar,
    start = "document",
    parser = "lalr",
    transformer = __Transformer()
) # type; lark.Lark
"""
A Lark parser for MOR c-rules.
"""

# ------
# Executor
# ------
def parse(text: str) -> CRULE_Set:
    return parser.parse(text)
# === END ===

if __name__ == "__main__":
    import sys
    cr = parse(sys.stdin.read())

    cr.dump_plantuml(sys.stdout)