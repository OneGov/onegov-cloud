The Design of OneGov Cloud
--------------------------

This document gives a general overview over the design of OneGov Cloud. After
reading this document you should understand its history, structure, and reason
for being. Hopefully this can serve as a guide for future development.

Primordial Soup
===============

The first lines of code for OneGov Cloud were written in 2014. At this point
we had written, deployed, and maintained a number of Plone modules.

This, it turned out, was often a blessing and a curse. With Plone it was easy
to provide the customer with additional value, by relying on the work of
others. A lot of open source code has been written for Plone and integrating
this work is generally quite possible, if not always straight forward.

The ability to take code written for Plone and customizing it with surgical
precision is another of its clear strengths.

However, a tall stack of modules of customizations doesn't always make for a
great experience. Neither for the user, nor for the developer. Plone sites are
generally full of things that one should probably not touch. We've had a few
instances where users accidentally brought down their site.

A complex permission scheme also lead to a lot of erroneous configurations
where users could do more than anticipated and where content was sometimes
public when it should not have been.

The OneGov Cloud is our break with Plone and the attempt keep some of its
strengths while shedding a lot of its weaknesses.

Zope Got It Right
=================

The underlying technology of Plone, is Zope. The first Python web framework
of note, Zope was a pioneer and 10 years ahead of its time.

What made Zope such a great framework was the ability to layer code and
configuration infinitely often. That most web-frameworks have never considered
this approach is curious.

Imagine a web-application that handles hotel bookings. You write it, sell it
to a hotel and after a while you find a second hotel that wants it too.

Naturally, the second hotel wants to customize a few things. The design for
one, but possibly also the required fields on the booking form, the booking
process itself and the e-mail sent to the customer.

With Zope, you can write a general hotel application and override pieces of
its functionally, through well-defined boundaries, in custom applications that
inherit from the general one. Think of it as class based inheritance for
web applications.

Now, in 2014 you don't start a new project on Zope, as its time has passed. But
luckily, you have an old Zope developer writing a re-imagined micro
web-framework based on the ideas of Zope.

Enter Morepath.

Morepath
========

