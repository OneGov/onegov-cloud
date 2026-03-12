OneGov Org - OneGov Cloud's Flagship Application
------------------------------------------------

By far the most extensive application of OneGov Cloud is OneGov Org. Originally
it was a homepage for municipalities with a heavy focus on town-related
services like room reservations, forms, events and directories. Eventually the
town-specific functionality was moved out to a more specialized version named
OneGov Town.

What remained is a web application that is useful for any kind of organisation
in the government / NGO / associations realm that is an essential part of
the live of Swiss citizens.

Org, as it shall be called from here onward, now serves as a foundation for
many specialized applications that need the features that Org offers and maybe
a bit more.

Org Features
============

Org's most important features are the following:

Tickets
^^^^^^^
All services which are offered by organizations are piped through a ticketing
system that includes e-mail notifications, a chat and ways to execute actions
on tickets (for example, mark a ticket as paid).

This offers users an easy way to turn their sites into perpetual ToDo-lists and
offers a modern and professional approach to handling customer requests.

Topics
^^^^^^
A a CMS-like tree of pages with unstructured content.

Forms
^^^^^
Forms can be written using the formcode syntax described here:
:doc:`formcode`

Submitted forms are then presented as open tickets, which offers a generic way
of handling a wide range of situations. Additionally, submission windows may
be used to limit the influx of forms to a certain time and number.

Reservations
^^^^^^^^^^^^
To reserve things like tickets, gear, or rooms, the reservation system may be
used. To maximize backwards-compatibility we used Libres, a Plone-based
reservation system we wrote back in 2010:

https://libres.readthedocs.io

Reservations, like most other things that require an action on the website
owner's part, are managed through tickets. Additionally, formcode may be used
to ask for additional customer information.

Events
^^^^^^
Concerts, exhibitions and the like can be submitted by users or imported from
external systems and displayed in a timeline.

Directories
^^^^^^^^^^^
Topics are not great when it comes to unstructured content. When structure is
present and should be enforced, directories are used.

Directories are somewhat complex for the user to set up, but they allow the use
of formcode to create a schema for data that is then enforced over a set of
records.

Additionally, users may submit new entries and change requests for existing
ones. This is handled through tickets.

Uploads
^^^^^^^
Org supports the upload of various images and documents that is then served
through the web applications. We have some customers with 20GB worth of
pictures organized in photo-albums. As most files are cached directly on the
front-end server (nginx), offering this feature puts little strain on our
servers.

Additionally, we support the digital signing of PDF files through the Swisscom
All-In Signing Service.

Payments
^^^^^^^^
Through Stripe we support payments in any module that supports formcode:

* Forms
* Directories
* Reservations

As Stripe is just a payment provider, we are able to add additional payment
providers, though it is certainly a lot of work.

User-Management
^^^^^^^^^^^^^^^
We offer user management with four roles:

- Admin (may do everything)
- Editor (may do most things)
- Member (may not do much)
- Anonymous (my do even less)

There's no way to add additional rules or to specify custom permissions. Doing
so is often a great way to shoot oneself in the foot, so we generally try to
avoid it as much as possible.

Org Derivatives
===============

From org, other applications have spawned that usually change little:

- OneGov Town, which includes some customizations for municipalities.
- OneGov Intranet, which offers a different permission set.
- OneGov Winterthur, which adds some features and changes the UI.
- OneGov Fsi, which is specialization for the canton of Zug.
- OneGov Feriennet, which adds a large number of features for Pro Juventute.
