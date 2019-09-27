# OneGov Cloud 🌤

OneGov Cloud is a Swiss initiative to provide municipalities with open-source
web-applications.

[![Screenshot](/docs/_static/govikon.png?raw=true)]()

---

You have reached the source of `onegov-cloud`. If that's not what you were
looking for, you might appreciate these links:

- **[Marketing site](https://onegovcloud.ch)**
<br>For an executive summary

- **[Developer docs](https://onegovcloud.ch)**
<br>For a technical overview and Python API docs

- **[Showcase](https://govikon.onegovcloud.ch)**
<br>Where we show of and blog about new features

- **[Onboarding](https//start.onegovcloud.ch)**
<br>Where you can start your own free instance

- **[Changelog](CHANGES.md)**
<br>Where you get a list of releases with relevant changes

---

[![Build status](https://badge.buildkite.com/400d427112a4df24baa12351dea74ccc3ff1cc977a1703a82f.svg)](https://buildkite.com/seantis/onegov-cloud)

## Branches 🖖

> ⚠️ Please note that the master branch of this repository can and will be
> deployed often.
> It is therefore imperative *not* to develop on the master branch.

To create a new feature, start a new branch, named after the ticket:

* `ticket-101`
* `fer-50`
* `zw-112`

Or if there really is no ticket, with an appropriate name:

* `new-templating-engine`
* `experimental-design`

When ready to deploy, merge the branch as follows and provide a good commit
message (see below):

    git checkout master
    git pull
    git checkout ticket-101
    git rebase master
    git checkout master
    git merge ticket-101 --edit

### Commit Messages

Commit messages are used to build the release history. For a commit to show
up in the release history, it needs to be written as follows:

    <Module>: <Message>

    <Optional Description>

    TYPE: <Feature|Bugfix>
    LINK: <Ticket-Number>

For example:

    Election-Day: Adds an customizable footer

    The footer can be customized in the settings, by admin users.

    TYPE: Feature
    LINK: 101

Commits that do not follow this scheme are not included in the changelog.

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

## Requirements ☝️

To run OneGov Cloud locally, you must meet the following requirements:

* Linux/MacOS
* Postgres 10+
* Python 3.7+
* OpenJDK 11+
* Elasticsearch 6.x
* Redis 5.x
* NodeJS 9+

### Libraries

You'll additionally have to install a number of libraries, to build the
dependencies:

#### MacOS
```shell
brew install curl libffi libjpeg libpq libxml2 libxslt zlib libev poppler pv
```

#### Ubuntu
```shell
sudo apt-get install libcurl4-openssl-dev libffi-dev libjpeg-dev libpq-dev
libxml2-dev libxslt1-dev zlib1g-dev libev-dev libgnutls28-dev libkrb5-dev
libpoppler-cpp-dev pv
```

## Installation 🤘

To install OneGov Cloud, you should first get the source:

    git clone https://github.com/onegov/onegov-cloud

Switch to the source folder:

    cd onegov-cloud

Next you want to create a virtual environment:

    python -m venv venv

Then you want to activate it:

    source venv/bin/activate

Finally, run the installation:

    make install

## Configuration 👌

To configure your setup, copy the example configuration and adjust it to your needs:

    cp onegov.yml.example onegov.yml

Once you are happy, you can start your first organisation:

    onegov-org --select /onegov_org/govikon add "Gemeinde Govikon"

Together with your first user:

    onegov-user --select /onegov_org/govikon add admin admin@example.org

Then, start your local instance:

    onegov-server

And open the local url in your browser:

    open http://localhost/onegov_town/govikon

## Updates 🙌

To run updates, you want to first update your sources:

    git pull

Then you should install updated dependencies:

    make update

Then, apply database changes.

    onegov-core upgrade

## Tests 🤞

To run all tests (this will take ~ 30 minutes):

    py.test

To run all tests concurrently with 2 processes (~ 15 minutes):

    pytest -n 2

To run the tests of a single module:

    py.test tests/onegov/core

To keep track of changes and only re-run necessary tests:

    py.test --testmon

## Translations 🌍

To extract the translation strings of an already configured module:

    do/translate onegov.org

To add a language to module:

    do/translate onegov.org fr_CH

Additionally, you can use <https://gengo.com> to translate English messages
to other languages, like German, French or Italian.

For this to work, you need to set the following variables:

    export GENGO_PUBLIC_KEY="my gengo public key"
    export GENGO_PRIVATE_KEY="my gengo private key"

To push a translation job to Gengo, run:

    do/honyaku onegov.org fr_CH

Later you can re-run the command to get the state of the translations. As they
come in you can accept them or ask for revisions.

You can also add a comment for the translator when creating the job:

    do/honyaku onegov.org fr_CH "Please leave tickets as 'tickets', not 'billets'"

Or:

    do/honyaku onegov.org fr_CH "The following are variables and should be left as is: ${example}"


## Releases 🚀

To create a new release, check the changelog first:

    do/changes

Then run the release script:

    do/release

## License 🤝

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
