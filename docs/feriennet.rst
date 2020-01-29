Feriennet - A Complicated Org
-----------------------------

Of all the OneGov Org derivatives, OneGov Feriennet is by far the most
complicated. It is probably the buggiest and certainly the most popular of all
our applications. Over 90% of our OneGov Cloud traffic hits Feriennet
instances.

This document will try to shed some light on some aspects of Feriennet that
need to be understood for its continued development.

Essential vs Accidental Complexity
==================================

The complexity of Feriennet is more accidental than it should be, but not
entirely so. The system it replaced was *very* complicated and by implementing
it from scratch without backwards compatibility helped make the new system a
lot easier, at least for the users.

Most other parts of the OneGov Cloud are either simple in their scope, or they
were parts about which we knew a lot about before setting out to write them.

As a result, Feriennet carries the accidental complexity we accrued by not
knowing too much about the various ways Ferienpässe are conducted. Additionally
it contains the essential complexity caused by serving many different
associations that conduct Ferienpässe in various ways.

Ideally we could offer a single way of doing things and everyone working with
the tool would follow that way. Surely, one can dream.

How Ferienpässe Are Organized
=============================

There are two kinds of organizations that organize activities:

* Professional organizations with dedicated staff
* Volunteer organizations with parents working in their free time

Those organizations will usually (but not always) have one period per year
where they offer activities that children can join. Usually in summer.

The way that those activities are conducted again differs in multiple ways, but
essentially boils down to two approaches:

* Attendees can select a limited set of activities for a flat rate.
* Attendees can select any number of activities, paying for each one.

Further, bookings can be made in two ways:

* By creating a wishlist that is turned into bookings later
* By directly creating bookings

If a wishlist is used, a matching algorithm will try to create a stable set of
bookings using an adaption of the Gale-Shapely stable marriage algorithm:

https://www.seantis.ch/blog/stable-marriage/

Finally, payment is handled in two ways:

* By paying the organization up front
* By paying the organization after the event

Some organizations also want the event host to be paid extra fees in cash, and
some want an additional tax on each booking.

Those are not the only ways that organizations differ, but they are the most
important ones. As should be obvious, this already creates a large number
of constellations one might find in the 100+ organizations that already use
Feriennet.

How Feriennet Works
===================

The following is a typical workflow when conducting vacation activities in
the summer:

1. A new period is created that binds all records relevant to this summer.
2. A wishlist-phase is defined during which users add wishes.
3. Event hosts are adding their available dates.
4. Activities are published through the ticketing system.
5. Users start adding dates to their wishlist.
6. The administrator turns wishes to bookings through the matching system.
7. Users may now create additional bookings directly.
8. The activities are conducted.
9. The bills are created and sent out.
10. The billing is finalized and the period is archived.

Design
======

Feriennet consists of two packages:

* ``onegov.feriennet``, an Org derivative
* ``onegov.activity``, contains the models used by Feriennet

Feriennet customizes Org in many ways and requires French translation.
Therefore it is often necessary to add new customization capabilities to Org
when developing Feriennet.

The most important models defined by ``onegov.activity`` are the following:

* ``onegov.activity.models.Period``, binds all records that are relevant to
  a single period only (like bookings and occasions, but not activities).

* ``onegov.activity.models.Activity``, contains the part of an activity that
  stays the same over many periods (like content, owner, pictures).

* ``onegov.activity.models.Occasion``, contains the part of an activity that
  is bound to the period, like the dates or the number of attendees. Bookings
  are linked to occasions.

* ``onegov.activity.models.Booking``, represents a wish or a booking, depending
  on the state of the period.

* ``onegov.activity.models.Attendee``, the person to which the booking belongs.
  This is different from the user, which would usually be the parent, whereas
  the attendee would be the child. Attendees have no user login.

* ``onegov.activity.models.Invoice``, the invoices that need to be paid by the
  users for services received or reserved.

Those are not all the models in ``onegov.activity`` and a lot more information
can be found on the definition of each model, but it should offer a good idea
on the landscape one finds in Feriennet.
