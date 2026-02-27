# OneGov Cloud

OneGov Cloud is a Swiss initiative to provide municipalities with open-source
web-applications.

[![Screenshot](docs/_static/wil-sg.png?raw=true)]()

---

You have reached the source of `onegov-cloud`. If that's not what you were
looking for, you might appreciate these links:

- **[Marketing site](https://admin.digital)**
<br>For an executive summary (in German)

- **[Developer docs](https://onegov.github.io/onegov-cloud/)**
<br>For a technical overview and Python API docs

- **[Changelog](CHANGES.md)**
<br>Where you get a list of releases with relevant changes

- **[Onboarding](https://start.onegovcloud.ch)**
<br>Where you can start your own free instance of our solution for muncipalities

---
[![Tests](https://github.com/OneGov/onegov-cloud/actions/workflows/tests.yml/badge.svg)](https://github.com/OneGov/onegov-cloud/actions/workflows/tests.yml) [![Build status](https://github.com/OneGov/onegov-cloud/actions/workflows/build-and-push.yml/badge.svg)](https://github.com/OneGov/onegov-cloud/actions/workflows/build-and-push.yml) [![codecov](https://codecov.io/github/OneGov/onegov-cloud/branch/master/graph/badge.svg?token=88YQZSZKEX)](https://codecov.io/github/OneGov/onegov-cloud) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

## Developing

To create a new feature or bugfix, start a new branch, named after the ticket:

* `ticket-101`
* `fer-50`
* `zw-112`

Or if there really is no ticket, with an appropriate name:

* `new-templating-engine`
* `experimental-design`

When ready to deploy, create a pull request with a good pull request message (see below) and, if possible, add some reviewers. If the review has passed, merge and **squash**.

### Commit and Pull Request Messages

**Commit messages** are used to build the release history. For a commit to show
up in the release history, it needs to be written as follows:

    <Module>: <Message>

    <Optional Description>

    TYPE: <Feature|Bugfix>
    LINK: <Ticket-Number>
    HINT: <Optional upgrade hint>

For example:

    Election-Day: Adds an customizable footer

    The footer can be customized in the settings, by admin users.

    TYPE: Feature
    LINK: OGC-101
    HINT: Run `ongegov-election --select /onegov_election_day/* migrate` after upgrade

> Commits that do not follow this schema are not included in the changelog.


**Pull request messages** should contain the first line of the commit message (`<Module>: <Message>`) for the title and the rest for the message.

**Module Name**

The module name may be any valid string that starts with an uppercase
character and is less than 17 characters long.

Examples:

* `Core`
* `Org`
* `Search`

**Type**

The type may be one of these values:

* `Feature`
* `Performance`
* `Bugfix`
* `Other`

**Link**

The link points to an issue, if there is any (optional). For example:

* `101` - points to GitHub Issue 101 in the `onegov-cloud` repository.
* `VOTES-1` - points to the first election day issue in the internal tracker.

To preview the changelog at any point, make your commit locally (with the
appropriate message) and run `do/changes`. This will render the complete
changelog in markdown. Your commit should be somewhere at the top.

If the commit you did does not show up, check to make sure that the module
name is valid (first character must be uppercase!).

### Type hints code of conduct

Some of our modules have increasingly strict requirements for writing type hints, sometimes this can be a distraction, especially for hot fixes, which need to happen quick.

In order to avoid degrading the quality of our type hints over time, here are some rules for how to deal with situations where you don't know what the correct type hint for a function/attribute should look like:

    from typing import Any as Incomplete

    def foo(x: Incomplete) -> Incomplete:
        y: Incomplete = bar(x)
        ...  # type error further below because of y


`Incomplete` indicates that a type annotation isn't finished, so we can easily
search for it and fix it later on. Please avoid using `type:ignore` comments unless you are absolutely certain that the error is fine to ignore, it's a lot more difficult to clean up later on and can hide genuine problems with the code.

## Requirements

To run OneGov Cloud locally, you must meet the following requirements:

* Linux/MacOS
* Postgres 10+
* Python 3.11+
* Redis 5+
* NodeJS 9+
* Docker Compose

To install the requirements for Ubuntu do:

    sudo apt install postgresql postgresql-contrib redis-server nodejs python3 docker-compose

### Libraries

You'll additionally have to install a number of libraries, to build the
dependencies:

#### MacOS
```shell
brew install curl libffi libjpeg libpq libxml2 libxslt zlib libev poppler pv libxmlsec1 weasyprint
```

#### Ubuntu
```shell
sudo apt-get install libcurl4-openssl-dev libffi-dev libjpeg-dev libpq-dev \
libxml2-dev libxslt1-dev zlib1g-dev libev-dev libgnutls28-dev libkrb5-dev \
libpoppler-cpp-dev pv libzbar0 openssl libssl-dev xmlsec1 libxmlsec1-openssl \
weasyprint
```

## Installation

To install OneGov Cloud, you should first get the source:

    git clone git@github.com:OneGov/onegov-cloud.git

Switch to the source folder:

    cd onegov-cloud

Next you want to create a virtual environment:

    python3 -m venv venv

Then you want to activate it:

    source venv/bin/activate

Finally, run the installation:

    make install

> :sos: **I get compile errors related to OpenSSL on macOS**
>
> This occurs if you are using brew to install Python and OpenSSL. The resulting
> binaries link to the brew OpenSSL library, not the macOS one. To fix the
> problem, export the following variables before trying `make install` again:

```bash
export LDFLAGS="-L/usr/local/opt/openssl/lib"
export CPPFLAGS="-I/usr/local/opt/openssl/include"
```

## Configuration

To configure your setup, copy the example configuration and adjust it to your needs:

    cp onegov.yml.example onegov.yml

## Create a database for onegov

Define a user `dev` and password `devpassword` using `dsn: postgresql://dev:devpassword@localhost:5432/onegov`
in `onegov.yml`:

    sudo -u postgres psql

    CREATE USER dev WITH PASSWORD 'devpassword' LOGIN NOINHERIT;
    ALTER USER dev WITH SUPERUSER;
    CREATE DATABASE onegov;
    GRANT ALL PRIVILEGES ON DATABASE onegov TO dev;
    ALTER DATABASE onegov SET timezone TO 'UTC';

Use the 'exit' command once your done to quit the postgres cli.

    postgres=# exit


Onegov cloud uses one database for all applications and instances.


## Setting up the application(s) locally

### Create folder structure for local storage and change owner accordingly

    sudo mkdir -p /usr/local/var/onegov/depot
    sudo mkdir -p /usr/local/var/onegov/files
    sudo chown -R $USER:$USER /usr/local/var/onegov

### Configure token

add the mapbox token to you onegov.yml (generic)

    mapbox_token: '<token>'

> NOTE: Make sure you don't miss the single quotes

**Org, Town, Town6, Agency, FSI and Translator Directory**

Create a new organization in the database together with a new admin (adjust the path according to your configuration):

    onegov-org --select /onegov_town6/govikon add "Gemeinde Govikon"
    onegov-user --select /onegov_town6/govikon add admin admin@example.org --password test --no-prompt


**Election Day and Swissvotes**

Create the `principal.yaml` and flush redis. You may want to add a user (see above).

## Running the instance(s)

Run your local setup - start onegov server:

    onegov-server

And open the local url in your browser (depending on what you setup, a new community or an existing by transferring from a remote server, see above):

    http://localhost:8080/onegov_town6/govikon

To auto-reload chameleon templates, set `ONEGOV_DEVELOPMENT` environment variable:

    export ONEGOV_DEVELOPMENT='1'

**Optional**
Run the D3renderer and the SMTP server: (for me sudo was required)

    docker compose up -d

## Update your local setup

To run updates, you want to first update your sources:

    git pull

Then you should install updated dependencies:

    make update

Then, apply database changes.

    onegov-core upgrade

To list database changes since a release:

    git diff release-2021.60 -- '**upgrade.py'

## Tests

### Python

To run all tests (this will take ~ 30 minutes):

    pytest

To run all tests concurrently with 2 processes (~ 15 minutes):

    pytest -n 2

To run the tests of a single module:

    pytest tests/onegov/core

To keep track of changes and only re-run necessary tests:

    pytest --testmon

To get an image with profiling information (requires graphviz):

    pytest --profile-svg

To use a RAM located database:

    docker run --rm \
      -e POSTGRES_HOST_AUTH_METHOD=trust \
      --mount type=tmpfs,destination=/var/lib/postgresql/data \
      -p 55432:5432 postgres:12.6 -c fsync=off
    pytest --nopg

### JavaScript

To run the javascript tests (swissvotes and election day):

    cd tests/js
    npm install
    npm test

To update the snapshots after changes, run:

    npm test -- --update-snapshot

## Translations

To extract the translation strings of an already configured module:

    do/translate onegov.org

To add a language to module:

    do/translate onegov.org fr_CH

To synchronize between different modules:

    do/apply-translations onegov.org onegov.town6

Additionally, you can use <https://gengo.com> <https://www.marstranslation.com> to translate English messages
to other languages, like German, French or Italian.

For this to work, you need to set the following variables (note the single quotes!):

    export GENGO_PUBLIC_KEY='my gengo public key'
    export GENGO_PRIVATE_KEY='my gengo private key'

To push a translation job to Gengo, run:

    do/honyaku onegov.org fr_CH

Later you can re-run the command to get the state of the translations. As they
come in you can accept them or ask for revisions.

You can also add a comment for the translator when creating the job:

    do/honyaku onegov.org fr_CH "Please leave tickets as 'tickets', not 'billets'"

Or:

    do/honyaku onegov.org fr_CH "The following are variables and should be left as is: ${example}"


### Import / Export of Translations (XLSX)

First, install poxls (pip/pipx) and gettext (package manager).

Export the current translations to a XLSX

    do/translations-to-excel onegov.org translations.xlsx

Update the current translation with the given XLSX

    do/translations-from-excel onegov.org translations.xlsx

## Releases

To create a new release, check the changelog first:

    do/changes

Then run the release script:

    do/release

## License

OneGov Cloud is released under the MIT license:

```
Copyright 2019 Seantis GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
