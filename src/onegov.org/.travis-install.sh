#!/bin/bash
pip install tox

if [ "$TOXENV" = 'py34' ]; then
    pip install coveralls
fi

# needed until chromedriver 2.31 is officially released
mkdir -p /home/travis/.wdm/chromedriver/2.30
curl -L 'https://github.com/davidthornton/chromedriver-2.31/blob/master/chromedriver?raw=true' -o /home/travis/.wdm/chromedriver/2.30/chromedriver
chmod +x /home/travis/.wdm/chromedriver/2.30/chromedriver
