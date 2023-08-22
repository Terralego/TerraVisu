============
Contributing
============

Conventions
-----------

* Before contributing, open an issue and discuss about it with community (is it a bug or a feature ? What is the best way to achieve my goal ?)
* Use flake8
* KISS & DRY as much as possible
* Elegant and generic is good, simple is better
* Separate bug fixes and new features in several pull requests.
* Open a new Pull Request in "Draft" status until tests passed. Use at least 'bug', 'improvement' or 'feature' label.
* Commits messages are explicit and mention issue number (``(ref #12)`` or ``(fixes #23)``)
* Features are developed in a branch and merged from Github pull-requests.


Definition of done
------------------

* ``docs/changelog.rst`` is up-to-date
* An explicit unit-test covers the bugfix or the new feature.
* Unit-tests total coverage is above or at least equal with previous commits. Patch coverage is 100% on new lines.
* Settings have default value in ``project/settings/__init__.py``
* Installation instructions and documentation are up-to-date
