FROM python:3.7.4-buster

LABEL maintainer="T. N. Hayashi <net@hayashi-lin.net>"

RUN pip install git+https://github.com/aslemen/pyksnk

# RUN wget -O /usr/local/share/pyksnk_check_dup_phon_gloss.py https://gist.githubusercontent.com/aslemen/b49a88b87117f857a3cbd0e7f9009d92/raw/001479ebb0edab36ccd4f9a19e80d3755268b1c5/pyksnk_check_dup_phon_gloss.py 

ENTRYPOINT [ "pyksnk" ]
