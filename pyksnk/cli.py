import typing

import itertools

import pandas as pd
import ruamel.yaml as yaml
import sys
import io

import click

from . import mordict
from . import morcomb
from . import crule

# ======
# Commandline commands
# ======

# ------
# Root
# ------
@click.group()
def cmd_main():
    """
\b
Requirements:
- Python: >= 3.5
- Python Packages:
    ruamel.yaml
    click
    pandas
    lark-parser
    attrs
    typing
    """
# === END ===

# ------
# 1. Morcomb files
# ------
@cmd_main.group(
    name = "morcomb"
)
def cmd_morcomb(): pass

# -----
# 1.0 Linter
# ------

@cmd_morcomb.command(
    name = "lint"
)
@click.argument(
    "input_file",
    type = click.File(),
    metavar = "<input_file>"
)
def cmd_morcomb_lint(input_file):
    """Lint a morcomb file.

\b
You must specify the path to the input file, <input_file>, so that the script can proceed to get it. 
'-' stands for STDIN. 
(Example: cat <path> | pyksnk morcomb to-yaml -, which is equivalent to mor2yaml <path>)
    """
    # Parsing
    parsed = (
        morcomb.parse(
            text = input_file.read()
        )
    ) # type: morcomb.Morcomb

    # Dumping without any alternations
    sys.stdout.write(str(parsed))
# === END ===

# ------
# 1.1 Convertor to YAML
# ------
@cmd_morcomb.command(
    name = "to-yaml"
)
@click.argument(
    "input_file",
    type = click.File(),
    metavar = "<input_file>"
)
def cmd_morcomb_mor2yaml(input_file):
    """Convert a morcomb file to their YAML formatations.
    
\b
You must specify the path to the input file, <input_file>, so that the script can proceed to get it. 
'-' stands for STDIN. 
(Example: cat <path> | pyksnk morcomb to-yaml -, which is equivalent to mor2yaml <path>)
    """

    # Initializations
    YAML = morcomb.get_YAML_processor() # type: yaml.YAML

    # Parsing
    parsed = (
        morcomb.parse(
            text = input_file.read()
        )
    ) # type: morcomb.Morcomb

    # Dumping
    YAML.dump(parsed, sys.stdout)
# === END ===

# ------
# 1.2 Inverse Convertor from YAML
# ------
@cmd_morcomb.command(
    name = "from-yaml"
)
@click.argument(
    "input_file",
    type = click.File(),
    metavar = "<input_file>"
)
def cmd_morcomb_yaml2mor(input_file):
    # Initializations
    YAML = morcomb.get_YAML_processor() # type: yaml.YAML

    # Parsing
    parsed = YAML.load(input_file)

    # Dumping
    sys.stdout.write(str(parsed))
# === END ===

# ------
# 2. Mor dictionary
# ------
@cmd_main.group(
    name = "dict"
)
def cmd_dict(): pass

@cmd_dict.command(
    name = "check",
    options_metavar = "<options>"
)
@click.argument(
    "dic_files",
    type = click.File('r'),
    nargs = -1,
)
def cmd_dict_check(dic_files):
    if dic_files:
        # Just parse and dump them
        for f in dic_files:
            try:
                mordict.parse_raw(f.read())
            except Exception as e:
                raise e
        # === END FOR f ===
    else:
        # read from STDIN and dump the parse
        mordict.parse_raw(sys.stdin.read())
    # === END IF ===

    sys.stderr.write("No error is detected!\n")
# === END ===

@cmd_dict.command(
    name = "check-duplicates",
    options_metavar = "<options>"
)
@click.argument(
    "dic_files",
    type = click.File('r'),
    nargs = -1,
    #options_metavar = "<dictionary_files>"
)
def cmd_dict_check_dup(dic_files):
    # dict_all: pd.DataFrame = None

    if dic_files:
        dict_all = pd.concat(
            map(
                lambda f: mordict.parse(
                    f.name,
                    f.read()
                ).to_dataframe(),
                dic_files 
            )
        )
    else:
        dict_all = mordict.parse(
            "<STDIN>",
            sys.stdin.read()
        ).to_dataframe()
    # === END IF ===

    dup = dict_all.duplicated(
        subset = [
            mordict.Phon.pandas_col_name
        ],
        keep = False
    ) # type: pd.Series
    contents_dup = dict_all[dup]

    mordict.dump_mordict_pandas(contents_dup, sys.stdout)
# === END ===

@cmd_dict.command(
    name = "lint",
    options_metavar = "<options>"
)
@click.argument(
    "path_dic_files",
    type = click.Path(exists = True),
    nargs = -1,
)
def cmd_dict_lint(path_dic_files):
    if path_dic_files:
        # current_dic: mordict.Dictionary = None

        for pf in path_dic_files:
            try:
                with open(pf, "r") as f:
                    current_dic = mordict.parse(
                        f.name,
                        f.read()
                    )
                # === END WITH ===

                with open(pf, "w") as f:
                    f.write(current_dic.print_mordict())
                # === END WITH ===

            except mordict.lark.ParseError as e:
                sys.stderr.write(
                    "An error has occurred in the file {0}:\n".format(f.name)
                    )
                sys.stderr.write(str(e))
            else: pass
            finally: pass
        # === END FOR pf ===
    else:
        dict_stdin = (
            mordict.parse(
                "<STDIN>",
                sys.stdin.read()
            )
        ) # type: mordict.Dictionary

        buf = io.StringIO() # type: io.StringIO 
        dict_stdin.dump_mordict(buf)
        buf.seek(0) # go back to the beginning
        sys.stdout.writelines(iter(buf)) # write linewise
    # === END IF ===
# === END ===


# ------
# 2. C-rules
# ------
@cmd_main.group(
    name = "crule"
)
def cmd_crule(): pass


@cmd_crule.command(
    name = "uml"
)
@click.argument(
    "input_file",
    type = click.File(),
    metavar = "<input_file>"
)
def cmd_crule_uml(input_file):
    cr = crule.parse(input_file.read())
    cr.dump_plantuml(sys.stdout)
# === END ===

@cmd_crule.command(
    name = "uml-digest"
)
@click.argument(
    "input_file",
    type = click.File(),
    metavar = "<input_file>"
)
def cmd_crule_uml_digest(input_file):
    cr = crule.parse(input_file.read())
    cr.dump_plautuml_digest(sys.stdout)
# === END ===