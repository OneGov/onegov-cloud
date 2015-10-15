# /usr/bin/env sh
pip install tox

if [ "$TOXENV" = 'py34' ]; then
    pip install coveralls
fi

if [ "$ES_URL" != 'no' ]; then
    mkdir /tmp/elasticsearch
    wget -O - "$ES_URL" | tar xz --directory=/tmp/elasticsearch --strip-components=1
fi
