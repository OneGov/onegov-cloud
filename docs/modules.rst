OneGov Cloud Modules
====================

..
    Currently, all sub-modules have to be added manually. It seems like the
    following could fix that: https://github.com/sphinx-doc/sphinx/issues/709

Hierarchy
---------

There are three kinds of OneGov Cloud Modules:

**Base modules**
    Provide the framework inside which OneGov Cloud is run.

**Supporting modules**
    Provide models/methods/utilities, but *no* HTTP interface (neither HTML
    nor REST).

**Base applications**
    Provide shared bases for multiple applications. Namely it allows for
    shared UI elements.

**Applications**
    Utilize the base and the supporting modules to actually provide a web
    application. Those may or may not be limited to HTML/REST.

This is how this hierarchy looks like:

.. code-block:: text

                       ┌───────────────┐
                       │               │
                       │ onegov.server │  ◇─┐
                       │               │    │
                       └───────────────┘    │
                               ▲            │ base modules
                               │            │
                       ┌───────────────┐    │
                       │               │    │
                       │  onegov.core  │  ◇─┘
                       │               │
                       └───────────────┘
                               ▲
                               │
                       ┌───────────────┐
                       │               │  ◇─┐
                       │  onegov.org   │    │ a base application
                       │               │  ◇─┘
                       └───────────────┘
                               ▲
                               │
                       ┌───────────────┐
                       │               │  ◇─┐
                       │ onegov.town6  │    │ an application
                       │               │  ◇─┘
                       └───────────────┘
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
    ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
    │               │  │               │  │               │
    │  onegov.page  │  │  onegov.user  │  │  onegov.form  │
    │               │  │               │  │               │
    └───────────────┘  └───────────────┘  └───────────────┘
            ◇                                     ◇
            └─────────────────────────────────────┘
                      supporting modules
           (may depend on onegov.core or each other)

Base Modules
------------

OneGov Server
^^^^^^^^^^^^^

Serves the OneGov web-applications. Meant to be the runner and configurator
of all applications. Not meant to run publicly. Like all python
web-applications this one should be proxied behind Nginx or Apache2.

OneGov server does not depend on any other OneGov module.

OneGov Core
^^^^^^^^^^^

Contains functionality shared between all the other OneGov modules, with the
exception of OneGov Server, which may not depend on the core. In many ways
this *is* the OneGov Cloud framework.

Supporting Modules
------------------

OneGov Activity
^^^^^^^^^^^^^^^

Contains the model representing youth activites for Pro Juventute.

OneGov Event
^^^^^^^^^^^^

A simple event (concert, meetup, party) system for OneGov Cloud.

OneGov File
^^^^^^^^^^^

Provides a way to store and serve files tied to the database and bound to
the transaction.

OneGov Form
^^^^^^^^^^^

Integrates the form library WTForms with OneGov and provides useful
functionality related to that. May generate HTML, but won't offer any
UI as such.

OneGov Foundation
^^^^^^^^^^^^^^^^^

Provides the Zurb Foundation theme for OneGov in an extendable fashion.

OneGov Gis
^^^^^^^^^^

Contains models, methods and Javascript to use, work with and display maps and
coordinates.

OneGov Newsletter
^^^^^^^^^^^^^^^^^

Contains models to handle the sending of newsletters and the managing of
subscribers/recipients.

OneGov Page
^^^^^^^^^^^

Provides functionality to manage custom pages used by OneGov Town. Does not
provide a UI.

OneGov People
^^^^^^^^^^^^^

Provides functionality to manage people. Does not provide a UI.

OneGov Recipient
^^^^^^^^^^^^^^^^

A generic implementation of e-mail/sms/url recipients backed by the database.

OneGov Reservation
^^^^^^^^^^^^^^^^^^

Libres integration for OneGov Cloud. Libres is a python library to reserve stuff.

`Libres Documentation <https://libres.readthedocs.io/en/latest/>`_

OneGov Search
^^^^^^^^^^^^^

Elasticsearch integration for OneGov Cloud.

OneGov Shared
^^^^^^^^^^^^^

Assets and other things shared between multiple OneGov applications.

OneGov Ticket
^^^^^^^^^^^^^

A simple ticketing system for OneGov.


OneGov User
^^^^^^^^^^^

Providers user management without any UI.

Base Applications
-----------------

OneGov Org
^^^^^^^^^^^^^^^^^^

Provides a base for applications written for organizations close to the
government. For example, municipalities, youth organizations, elderly care,
and so on.

Applications
------------

OneGov Election Day
^^^^^^^^^^^^^^^^^^^

Shows Swiss election/voting results in an archive and as they come in during
voting day.

OneGov Feriennet
^^^^^^^^^^^^^^^^

Developed for Pro Juventute, this specialised organisation website helps to
organise summer activites for Switzerland's youth.

OneGov Agency
^^^^^^^^^^^^^
List of all agencies within an organization and the associated persons/functions

OneGov Town
^^^^^^^^^^^

The most visible part of the OneGov municipality websites. Combines
functionality of other OneGov modules and renders them.

OneGov Town tries to implement features itself when necessary. It's main
concern is rendering JSON/HTML. Therefore it should be considered the UI
layer.
