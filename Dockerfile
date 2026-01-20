FROM ubuntu:noble

# Install packages
RUN sed -i 's+http://archive.ubuntu.com+http://ch.archive.ubuntu.com+g' /etc/apt/sources.list

ARG DEBIAN_FRONTEND=noninteractive
RUN apt -qq update \
    && apt -qq install -y software-properties-common gpg-agent \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt -qq install -y --no-install-recommends \
    apt-utils \
    aria2 \
    build-essential \
    ca-certificates \
    cmake \
    curl \
    default-jre-headless \
    ghostscript \
    git \
    golang \
    iproute2 \
    libcairo2 \
    libcairo2-dev \
    libcurl4 \
    libcurl4-openssl-dev \
    libev-dev \
    libev4 \
    libffi8 \
    libkrb5-dev \
    libmagic1 \
    libnss-wrapper \
    libpoppler-cpp-dev \
    libpoppler-cpp0v5 \
    libpq-dev \
    libreadline8 \
    libsqlite3-0 \
    libxmlsec1 \
    libxmlsec1-openssl \
    libxt-dev \
    nodejs \
    openssl \
    pkg-config \
    python3-pip \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    tzdata \
    weasyprint \
    xmlsec1 \
    zip

# copy root files
COPY docker/root /

# su-exec allows us to run commands as different users via the entry point
RUN git clone --depth 1 https://github.com/seantis/su-exec /tmp/su-exec \
    && cd /tmp/su-exec \
    && make all \
    && cp /tmp/su-exec/su-exec /sbin/su-exec \
    && rm -rf /tmp/su-exec/su-exec

# tini is a pid-1 replacement which runs all our processes inside the container
RUN git clone --depth 1 https://github.com/seantis/tini /tmp/tini \
    && cd /tmp/tini \
    && cmake . \
    && make \
    && cp /tmp/tini/tini /sbin/tini \
    && rm -rf /tmp/tini/tini

# build the go-based nginx cache buster
COPY docker/nginx-cache-buster /tmp/nginx-cache-buster-src
RUN go build -o /tmp/nginx-cache-buster /tmp/nginx-cache-buster-src/* \
    && mkdir -p /app/bin \
    && cp /tmp/nginx-cache-buster /app/bin/ \
    && rm -rf /tmp/nginx-cache-buster \
    && chown root:root /app/bin/nginx-cache-buster \
    && chmod 4755 /app/bin/nginx-cache-buster

# build hivemind, a Procfile runner to spawn multiple processes (used for
# gunboat, the on-premise installer)
RUN GOBIN=/tmp go install github.com/seantis/hivemind@v1.0.4 \
    && cp /tmp/hivemind /usr/local/bin/hivemind \
    && rm -rf /tmp/hivemind

# build onegov-cloud
COPY MANIFEST.in /app/src/MANIFEST.in
COPY pyproject.toml /app/src/pyproject.toml
COPY setup.cfg /app/src/setup.cfg
COPY src /app/src/src
COPY .git /app/.git
WORKDIR /app
RUN git rev-parse --short HEAD > .commit \
    && git rev-parse HEAD > .commit-long \
    && python3.11 -m venv . > /dev/null \
    && mkdir -p /var/cache/wheels \
    && mkdir -p /var/cache/pip \
    && bin/pip install --cache-dir /var/cache/pip --upgrade pip setuptools wheel --quiet \
    && bin/pip install --find-links /var/cache/wheels --cache-dir /var/cache/pip ./src --quiet \
    && find lib -type d -iname assets -print0 | xargs -0 chmod a+w -R \
    && find /app -regex '^.*\(__pycache__\|\.py[co]\)$' -delete \
    && rm -rf /app/src \
    && rm -rf /app/.git \
    && rm -rf /var/cache/wheels \
    && rm -rf /var/cache/pip

# configure timezone
RUN ln -fs /usr/share/zoneinfo/UTC /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata

# global commands
RUN ln -s /app/bin/onegov* /usr/local/bin/

ENTRYPOINT ["/entrypoint"]
