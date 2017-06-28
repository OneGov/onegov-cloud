Changelog
---------

- Fixes syntax error in po file.
  [href]

0.13.0 (2017-06-28)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to create signup links to allow users to register themselves
  as editors or admins.
  [href]

0.12.1 (2017-06-28)
~~~~~~~~~~~~~~~~~~~

- Updates Romansch translations.
  [msom]

0.12.0 (2017-06-26)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to filter the user collection with custom filters.
  [href]

0.11.0 (2017-06-22)
~~~~~~~~~~~~~~~~~~~

- Adds forms and helper functions for password reset.
  [msom]

- Adds French, Italian and Romansh translations.
  [msom]

0.10.1 (2017-05-02)
~~~~~~~~~~~~~~~~~~~

- Adds the userprofile to the indexed values.
  [href]

0.10.0 (2017-04-27)
~~~~~~~~~~~~~~~~~~~

- Forces all usernames to be lowercase.
  [href]

0.9.0 (2017-01-20)
~~~~~~~~~~~~~~~~~~~

- Makes the user model searchable.
  [href]

0.8.4 (2016-11-25)
~~~~~~~~~~~~~~~~~~~

- Fix user title sql expression not working as intended.
  [href]

0.8.3 (2016-10-28)
~~~~~~~~~~~~~~~~~~~

- The login is now unskippable by default.
  [href]

0.8.2 (2016-10-27)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to check if the login can be skipped.
  [href]

0.8.1 (2016-10-24)
~~~~~~~~~~~~~~~~~~~

- Fixes yubikey to otp raising an error if the yubikey is malformed.
  [href]

0.8.0 (2016-10-06)
~~~~~~~~~~~~~~~~~~~

- Introduces a realname column.
  [href]

- Adds the ability to query users by role through the collection.
  [href]

0.7.1 (2016-08-31)
~~~~~~~~~~~~~~~~~~~

- Fixes yubikey property failing with empty values.
  [href]

- Adds the ability to find a user by yubikey.
  [href]

0.7.0 (2016-08-30)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to check the format of a yubikey OTP.
  [href]

- Adds the ability to extract the yubikey serial from one of its OTPs.
  [href]

- Adds support for yubikey removal on the login form.
  [href]

0.6.4 (2016-08-30)
~~~~~~~~~~~~~~~~~~~

- Be less clever about the existing user error, to avoid invalidating
  the session.
  [href]

0.6.3 (2016-08-30)
~~~~~~~~~~~~~~~~~~~

- Raises an ExistingUserError when an existing user is added.
  [href]

0.6.2 (2016-08-26)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to query a user by id.
  [href]

0.6.1 (2016-08-26)
~~~~~~~~~~~~~~~~~~~

- Log registrations for fail2ban integration.
  [href]

0.6.0 (2016-08-26)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to register new users and activate them with a token.
  [href]

0.5.0 (2016-08-24)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to create a login auth object to the current path.
  [href]

0.4.4 (2016-07-19)
~~~~~~~~~~~~~~~~~~~

- Adds compatibility with Morepath 0.15.
  [href]

0.4.3 (2016-06-28)
~~~~~~~~~~~~~~~~~~~

- Adds the ability to activate/deactivate users.
  [href]

- Adds the ability to list users through the cli.
  [href]

0.4.2 (2016-05-30)
~~~~~~~~~~~~~~~~~~~

- Catches signature verifcation error responses to the yubico server.
  [href]

0.4.1 (2016-05-30)
~~~~~~~~~~~~~~~~~~~

- Adds compatibility with onegov.core 0.21.0.

0.4.0 (2016-01-13)
~~~~~~~~~~~~~~~~~~~

- Adds an initials property to the user.
  [href]

- Adds a title property to the user.
  [href]

0.3.1 (2015-12-16)
~~~~~~~~~~~~~~~~~~~

- Turns the Yubikey field into an ordinary string field.
  [href]

- Replayed Yubikeys no longer lead to an exception.
  [href]

0.3.0 (2015-11-20)
~~~~~~~~~~~~~~~~~~~

- Adds 2FA support with Yubikey as the first possible option.
  [href]

0.2.1 (2015-10-15)
~~~~~~~~~~~~~~~~~~~

- Use 'de_CH' translation instead of 'de'.
  [href]

0.2.0 (2015-10-12)
~~~~~~~~~~~~~~~~~~~

- Removes Python 2.x support.
  [href]

0.1.1 (2015-10-06)
~~~~~~~~~~~~~~~~~~~

- Fixes 'to' parameter not being passed on by Auth.from_request.
  [href]

0.1.0 (2015-10-05)
~~~~~~~~~~~~~~~~~~~

- Adds a generic authentication model for login/logout views.
  [href]

0.0.3 (2015-10-02)
~~~~~~~~~~~~~~~~~~~

- Adds a generic login form
  [href]

0.0.2 (2015-06-26)
~~~~~~~~~~~~~~~~~~~

- Adds support for onegov.core.upgrade
  [href]

- Remove support for Python 3.3
  [href]

0.0.1 (2015-04-29)
~~~~~~~~~~~~~~~~~~~

- Initial Release [href]
