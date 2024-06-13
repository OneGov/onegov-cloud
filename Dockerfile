# =================
# build environment
# =================
FROM ubuntu:noble as build-env

# archive.ubuntu.com is often super slow, ch.archive.ubuntu.com is run by init7 and fast
RUN sed -i 's+http://archive.ubuntu.com+http://ch.archive.ubuntu.com+g' /etc/apt/sources.list

# install packages
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq \
    && apt-get install -y software-properties-common gpg-agent \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    cmake \
    libpq-dev \
    libcurl4-openssl-dev \
    libkrb5-dev \
    libpoppler-cpp-dev \
    libev-dev \
    git \
    golang \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    pkg-config

# su-exec allows us to run commands as different users via the entry point
RUN git clone --depth 1 https://github.com/seantis/su-exec /tmp/su-exec \
    && cd /tmp/su-exec \
    && make all

# tini is a pid-1 replacement which runs all our processes inside the container
RUN git clone --depth 1 https://github.com/seantis/tini /tmp/tini \
    && cd /tmp/tini \
    && cmake . \
    && make

# build the go-based nginx cache buster
COPY docker/nginx-cache-buster /tmp/nginx-cache-buster-src
RUN go build -o /tmp/nginx-cache-buster /tmp/nginx-cache-buster-src/*

# build hivemind, a Procfile runner to spawn multiple processes (used for
# gunboat, the on-premise installer)
RUN GOBIN=/tmp go install github.com/seantis/hivemind@v1.0.4

# build onegov-cloud
COPY MANIFEST.in /app/src/MANIFEST.in
COPY pyproject.toml /app/src/pyproject.toml
COPY setup.cfg /app/src/setup.cfg
COPY src /app/src/src
WORKDIR /app
RUN python3.11 -m venv . > /dev/null \
    && mkdir -p /var/cache/wheels \
    && mkdir -p /var/cache/pip \
    && bin/pip install --cache-dir /var/cache/pip --upgrade pip setuptools wheel --quiet \
    && bin/pip install --find-links /var/cache/wheels --cache-dir /var/cache/pip ./src --quiet \
    && find lib -type d -iname assets -print0 | xargs -0 chmod a+w -R \
    && find /app -regex '^.*\(__pycache__\|\.py[co]\)$' -delete \
    && rm -rf /app/src

# =================
# stage environment
# =================
FROM ubuntu:noble as stage-env

COPY docker/root /

# copy from build step
COPY --from=build-env /etc/apt/sources.list /etc/apt/sources.list
COPY --from=build-env /tmp/su-exec/su-exec /sbin/su-exec
COPY --from=build-env /tmp/tini/tini /sbin/tini
COPY --from=build-env /tmp/nginx-cache-buster /app/bin/
COPY --from=build-env /tmp/hivemind /usr/local/bin/hivemind
COPY --from=build-env /app /app

# install packages
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq \
    && apt-get install -y software-properties-common gpg-agent \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get install -y --no-install-recommends \
    aria2 \
    apt-utils \
    iproute2 \
    libnss-wrapper \
    tzdata \
    python3.11 \
    python3.11-venv \
    python3-pip \
    ca-certificates \
    openssl \
    libffi8 \
    libreadline8 \
    libsqlite3-0 \
    git \
    libmagic1 \
    libcurl4 \
    libpoppler-cpp0v5 \
    default-jre-headless \
    ghostscript \
    libpq-dev \
    libev4 \
    nodejs \
    zip curl \
    xmlsec1 \
    libxmlsec1 \
    libxmlsec1-openssl \
    libcairo2

# configure timezone
RUN ln -fs /usr/share/zoneinfo/UTC /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata

# global commands
RUN ln -s /app/bin/onegov* /usr/local/bin/

# the nginx cache buster needs the SUID bit to be set
RUN chown root:root /app/bin/nginx-cache-buster \
    && chmod 4755 /app/bin/nginx-cache-buster

ENTRYPOINT ["/entrypoint"]
