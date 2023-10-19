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


Pull requests
-------------

Before creating a pull request, ensure you follow thoses rules :

* Follow the guidelines of this page
* Self-review your code
* Add comments in your code, particularly in hard-to-understand areas
* Make corresponding changes to the documentation
* There is tests that prove my fix is effective or that my feature works.
* New and existing unit tests pass locally with my changes
* All new lines of code are tested
* There is an entry in the changelog file (with the corresponding issue referenced)


Release
-------

On master branch :
