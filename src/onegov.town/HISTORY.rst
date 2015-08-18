Changelog
---------

Unreleased
~~~~~~~~~~

- Removes Gravatar support.
  [href]

0.3.8 (2015-08-14)
~~~~~~~~~~~~~~~~~~~

- Emails are now sent only if the db transaction is successful.
  [href]

0.3.7 (2015-08-12)
~~~~~~~~~~~~~~~~~~~

- Fixes some email sending issues.
  [href]

0.3.6 (2015-08-12)
~~~~~~~~~~~~~~~~~~~

- Makes sure that all person links are valid.
  [href]

- When inserting a defined link, the dropdown now starts with an empty selection.
  [href]

0.3.5 (2015-08-11)
~~~~~~~~~~~~~~~~~~~

- Fix code editor not working in form definition editor.
  [href]

0.3.4 (2015-08-11)
~~~~~~~~~~~~~~~~~~~

- Depends on latest onegov.form release to fix installation issue.
  [href]

- The onegov.town.element classes now use less memory.
  [href]

0.3.3 (2015-08-10)
~~~~~~~~~~~~~~~~~~~

- Improves upon the requirements.txt generation. No other changes.
  [href]

0.3.2 (2015-08-10)
~~~~~~~~~~~~~~~~~~~

- No changes worth mentioning. Experimental requirements.txt generation on release.
  [href]

0.3.1 (2015-08-07)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to insert site links in the redactor through a dropdown.
  [href]

- Limit the deletion of pages including subpages to users with the admin role.
  [href]

- Adds a copy&paste mechanism for pages, links and news.
  [href]

- Add the ability to define room/daypass resources and allocations (no way
  to do reservations just yet).
  [href]

- Group images by dates.
  [msom]

0.3.0 (2015-08-03)
~~~~~~~~~~~~~~~~~~~

- Correctly sort the the pages even if the title has changed.
  [href]

- Limits the news list on the homepage to two entries.
  [href]

- Adds the datetimepicker plugin.
  [msom]

- Add retrieve password functionality.
  [msom]

0.2.6 (2015-07-16)
~~~~~~~~~~~~~~~~~~~

- Fixes encoding issue in Apple Mail.
  [href]

0.2.5 (2015-07-16)
~~~~~~~~~~~~~~~~~~~

- Shows a ticket count at the top of every page for logged in users.
  [href]

- Adds e-mail notifications for open/close ticket.
  [href]

- Adds reopen ticket functionality.
  [msom]

- Adds analytics code snippet.
  [msom]

0.2.4 (2015-07-14)
~~~~~~~~~~~~~~~~~~~

- Integrates tickets through onegov.ticket.
  [href]

- Form submissions automatically generate a onegov.ticket in the backend.
  [href]

- The old form submissions colleciton view is no more. This is now done
  through the ticketing system.
  [href]

- Form submissions, tickets and news are now shown with a relative date
  (e.g. 5 hours ago).
  [href]

0.2.3 (2015-07-09)
~~~~~~~~~~~~~~~~~~~

- Each form must now contain at least one required e-mail address field.
  [href]

- The login link always redirects to the original site now.
  [href]

- Show an alert for every form that contains errors.
  [href]

- Adds a reply-to address for automated e-mails.
  [href]

- Show the edit/delete links outside the dropdown.
  [href]

- Adds the ability to add an address block to topics, news and forms.
  [href]

- Adds the ability to add people to topics, news and forms.
  [href]

0.2.2 (2015-07-03)
~~~~~~~~~~~~~~~~~~~

- Show sidebar below the content on smaller screens.
  [href]

- Adds the ability to keep a directory of people related to the town.
  [href]

- Fix lists not showing a dot in the redactor editor.
  [href]

- Adds files upload and listing.
  [treinhard]

- Use more pronounced colors for various elements.
  [href]

- Adds the ability to hide news, pages or forms from anonymous users.
  [href]

- Fix sticky footer being partly rendered out of the viewport.
  [href]

- Updates Redactor to 10.2.
  [href]

0.2.1 (2015-06-26)
~~~~~~~~~~~~~~~~~~~

- Adds support for onegov.core.upgrade.
  [href]

- Remove support for Python 3.3.
  [href]

- Pages are now always sorted from A to Z.
  [href]

- Fixes form dependency javascript not working with multiple choices.
  [href]

- Fixes greyscale scss mixin not working in Firefox.
  [href]

- Adds many new builtin forms.
  [freinhard]

- Adds minor style adjustments.
  [freinhard]

0.2.0 (2015-06-10)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to use builtin forms, define custom forms and manage
  submissions.

- The 'more...' news link is only showed if there actually is more to read.
  [href]

- Paragraphs are now limited in width, images are 100% width.
  [href]

- Fix sticky footer jumping in Chrome by fixating it using CSS.
  [href]

0.1.0 (2015-05-07)
~~~~~~~~~~~~~~~~~~~

- Adds a news section.
  [href]

- Refactors pages to be easily be able to define new kind of pages.
  [href]

- Adds contact and opening hours as a footer.
  [href]

0.0.2 (2015-05-05)
~~~~~~~~~~~~~~~~~~~

- Images are now always shown in order of their creation.
  [href]

- Adds image thumbnails and the ability to select previously uploaded images
  in the html editor.
  [href]

- Adds support for image uploads through the html editor.
  [href]

- Replaces the markdown editor with a WYSIWYG html editor.
  [href]

- Upgrade to Zurb Foundation 5.5.2.
  [href]

- Show a wildcard next to required form fields.
  [href]

- Adds hints to form fields, rendered as placemarks.
  [href]

- The page markdown editor no longer steals the focus when opening the page.
  [href]

0.0.1 (2015-04-29)
~~~~~~~~~~~~~~~~~~~

- Initial release.
  [href]
