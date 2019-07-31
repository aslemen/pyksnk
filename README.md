# Kusunoki Dictioanry Management Tools
Using Python 3

## Dependencies
### Required
- Python >= 3.5
- Python Packages
    - ruamel.yaml
    - click
    - pandas
    - lark-parser
    - attrs
    - typing

## Installation
### If you want to use it as a python package (and via the commandline)
```sh
pip install (--user) git+https://github.com/aslemen/pyksnk
```

### If you want to use it via Docker
```sh
docker run -it aslemen/pyksnk
```

## Uninstallation
```sh
pip remove pyksnk
```

## Usage
### Using Interactive Interpreters

Example:
```python3
# load the modules
import sys
import pandas as pd
import pyksnk.mordict as md

# load the dictionary file
dic: md.Dictionary
with open("path/to/some_dict.cut") as f:
    dic = md.parse(f.name, f.read())

# convert the dictionary to a Pandas DataForm
dic_pd: pd.DataFrame = dic.to_dataframe()

# You can play around with `dic_pd`
#   before pushing it back to the original dictionary object `dic`
dic.update_with_dataframe(dic_pd)

# write the modified `dic` out to the STDOUT
dic.dump_mordict(sys.stdout)
```

### Via Commandline
```sh
pyksnk [command] [subcommand]
```
Please see the helps.
