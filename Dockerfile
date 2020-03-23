FROM python:3.8.2

RUN python3 -m pip install pyyaml minidb requests keyring appdirs lxml cssselect beautifulsoup4 jsbeautifier cssbeautifier

WORKDIR /opt/urlwatch

COPY lib ./lib
COPY share ./share
COPY setup.py .
COPY setup.cfg .

RUN python setup.py install

WORKDIR /root/.urlwatch

ENTRYPOINT ["urlwatch"]
