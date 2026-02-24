Please fill in the commit message below and work through the checklist. You can delete parts that are not needed, e.g. the optional description, the link to a ticket or irrelevant options of the checklist.

## Commit message

<Module>: <Message>

<Optional Description>

TYPE: <Feature|Performance|Bugfix>
LINK: <Ticket-Number>
HINT: <Optional upgrade hint>

## Checklist

- [ ] I have performed a self-review of my code
- [ ] I considered adding a reviewer
- [ ] I have added an upgrade hint such as data migration commands to be run
- [ ] I have updated the PO files
- [ ] I have added new modules to the docs
- [ ] I made changes/features for both org and town6
- [ ] I have updated the election_day API docs
- [ ] I have tested my code thoroughly by hand
    - [ ] I have tested styling changes/features on different browsers
    - [ ] I have tested javascript changes/features on different browsers
    - [ ] I have tested database upgrades
    - [ ] I have tested sending mails
    - [ ] I have tested building the documentation
- [ ] I have added tests for my changes/features
    - [ ] I am using freezegun for tests depending on date and times
    - [ ] I considered using browser tests für javascript changes/features
    - [ ] I have added/updated jest tests for d3rendering (election_day, swissvotes)
