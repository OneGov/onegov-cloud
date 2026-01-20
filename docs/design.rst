The Design of OneGov Cloud
--------------------------

This document gives a general overview over the design of OneGov Cloud. After
reading this document you should understand its history, structure, and reason
for being.

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

Morepath is dubbed a micro-framework with superpowers. It heavily borrows from
Zope and Grok, both of which were at least in part written by Morepath's
author.

Like Zope it allows for web applications to inherit from others. And like Grok
it eschews Zope's heavy reliance on XML configuration files.

When it came out, we decided to take a chance and build our own in-house
framework based on Morepath, to find a path out of our reliance on Plone.

Learning Morepath is essential to learn more about OneGov Cloud. Here are
a few good starting points.

Here's an introductory video (25 mins):

https://www.youtube.com/watch?v=gyDKMAWPyuY

Third, the official Morepath docs:

https://morepath.readthedocs.io/en/latest/

Turtles All The Way Down
========================

Resting upon the foundation that is Morepath, we built our own set of modules
that implement a lot of the parts that are missing in Morepath, which is a
*micro*-framework after all.

This includes some tooling, like a development server (``onegov.server``), a
general framework component for requests/session handling and the like
(``onegov.core``), libraries implementing data models, like ``onegov.user``,
and applications tying it all together, like ``onegov.org``.

An overview over the most important modules can be found here:
:doc:`modules`.

Crucially, almost everything can be written in a way that allows for
customization using the open/close principle (open for extension,
closed for modification).

Partially this is directly supported by Morepath, partially it is done with
custom implementations of things like template macro lookups.

Though it is never free to do so, it is always possible to take an application
or a module and add an abstraction on top that modifies its behavior.

Efficient Request Handling
==========================

Another thing that Plone is not that great at is running at scale. Of course,
you can scale a Plone application to thousands of users and millions of
requests. But it's going to require a lot of resources.

With OneGov Cloud we wanted to be more efficient. After some years and lots of
added code we sometimes fall short of this, but in general wen can run some
pretty nice workloads on pretty small servers with OneGov Cloud.

One reason for this is a lot of new code that we wrote ourselves. That is,
what runs is really what we need and want. To a large degree that is something
that you get with every new software project. Something that you will also lose
as the software grows bigger.

The other reason however is due to a design decision. We can run all our
OneGov Cloud workloads in a single process, no matter the request. Basically
we are supporting multi-tenant since the very first day.

As a result we have hosts where a handful of processes support over 100
different websites. Though we tend to distribute them homogeneously for
logistical reasons, we can theoretically load all our customers onto a single
server and run the workloads on a single set of processes.

Each request that hits our processes has a namespace which is associated with
different code-paths and database records, but which runs on a shared code-base.

As a result, our biggest server handling some 300 requests a second can run
on 8GB worth of RAM and 4 CPUs without breaking a sweat.

Single Container
================

The latest thing we got rid of that often was a source of pain is the package
management aspect of our deployments. At its conception, OneGov Cloud was
made up of a list of different Python modules that could be installed
separately.

This proved to be tricky, as one could not easily make changes over multiple
modules in a single commit. Often one would have to apply a change to different
modules in succession and release them one by one for CI to work properly.

To solve this once and for all, we now deploy all our sources using a single
container that contains all sources of all OneGov Cloud projects.

As a result our memory footprint is a bit higher than it needs to be, since we
are possibly loading modules we will never need. But on the other hand we can
test all code together and be sure that it all interacts well with each other.

The containerization also made our deployments easier and more reliable.
