fiëé croisée
============

I like making crossword puzzles. But it needs *a lot* of time without the right tools. 

At the moment this is some kind of fill-in sheet with attached dictionary to look for matching words.

I hope it will evolve in a tool that makes creating and sharing crossword puzzles just fun.


Installation
------------

It’s a Django_ application, to be run on Nginx_ with Django via gunicorn_.
(Outdated configuration files for Apache and FCGI are included.)

The provided fabfile (fabric_ deployment) is for a Debian server 
and documented at http://github.com/fiee/generic_django_project

Additionally you need an ``.env`` file, containing SECRET_KEY,
DATABASE_PASSWORD and EMAIL_PASSWORD.


Setup
-----

If you don’t need a public API, comment “rest_framework” in ``settings/base.py``
(INSTALLED_APPS) and ``requirements/base.txt``.


Features
--------

* public

  * find words that match a specified pattern (e.g. ``PY?H?N`` or ``?YT*``)
  * work in a puzzle grid (custom size 4-20 lines/rows)
  * save puzzles and retrieve them under a url code
  * load public puzzles
  * export public puzzles as ConTeXt_, LaTeX (cwpuzzle_) or plain text files
  * list words in dictionaries

* authenticated users

  * questions get automatically saved to personal dictionary
  * save puzzles as private

* admin

  * manage words and their descriptions in several dictionaries
  * import word lists

* api

  * optional RESTful API with djangorestframework (rest_framework)_


User
====

Cloze Query
-----------

Using the search field in the toolbar you can look up words that contain defined letters at discrete locations.

You can use _ as wildcards for single letters, * for an undefined number of letters (including none).

E.g. if you look up ``_Y__O_`` you get PYTHON and SYMBOL (depending on dictionaries, of course);
if you look up ``RAM*``, you get e.g. RAM, RAMBLE, RAMADAN etc. Of course you can mix wildcards at will.

All letters get uppercased, German umlauts get converted from Ä, Ö, Ü to AE, OE, UE; other international
characters get de-accented. (If your language needs other conversions, please contact the developer.)

Searching works only if you activate at least one dictionary first.

Query results are limited to 100 answers.


Puzzle Grid
-----------

Here’s how to make your own crossword puzzle:

Click the “star” button to create a grid in your favourite size (12x12 is good).

You can move around in the grid with the arrow keys (tab, shift-tab, backspace,
delete work also).
If you type letters, the cursor will move right to the next cell;
if you press shift while typing a letter, the cursor will move downward.
Please write slowly, otherwise the key handler swallows characters.

Write some letters or words into the grid “by heart” - in an empty grid, you’d
get thousands of possible words.

Perhaps write only one letter in the corners - that’s how I mostly start.
You might also want to start with a pattern of black fields (see below).
Press ? (question mark) in any square, and after a short delay you’ll get
two lists of words that match in this place horizontally and vertically.

You can click on the words in the result list to place them in the grid.
The list will adapt automatically to the new situation.

If you click on the search pattern, it gets copied to the cloze query field.

To mark cells as “blockers” (black fields), press space (and again to remove the block).

To set a number as start-of-word mark, press # (number sign).
The numbering works automatically.
A question field is added to the horizontal and/or vertical list,
it gets filled with the first solution from your selected dictionaries.
Just press # again to remove the number and the question field.
If you change the questions/descriptions, they get saved into your personal
dictionary (only for logged-in users, of course).
 


Admin
=====

Make a wordlist
---------------

1. use the provided wordlists for German, English and Esperanto 
   (derived from ispell_ dictionaries); you can upload them directly.
2. use a dictionary from aspell_:

 aspell dump master > mydict.txt

3. get some long text, e.g. from `Project Gutenberg`_
4. write your own

* The wordlist file is expected in UTF-8 encoding.
* Format is “(word)\\t(description)\\t(priority)\\n”.
  Description and priority are optional (default to word and 0).
* run ``make-wordlist.py`` on it (or several), result is ``wordlist.txt``.


Make a dictionary
-----------------

* upload a wordlist file to your croisee installation (Wordlist Upload);
  that may take a while.
* If the wordlist is too big for processing, you can split it using
  ``tools/split-wordlist.py`` to create chunks of max. 10’000 lines.
* fix descriptions and priorities, if you like.


Development
===========

Roadmap
-------

I’m planning to implement the following features in about this order:

* move from jQuery to Vue.js
* export grid and solution as text (done) / HTML / LaTeX (cwpuzzle_, done) / ConTeXt_ (done) / PDF / InDesign IDML
* export of dictionaries
* edit personal dictionary (or all for admins)
* add additional locales
* use tagging for puzzles
* delete anonymous puzzles after e.g. 1 month
* allow adopting of anonymous puzzles by users
* import text files (JSON, YAML?)
* different types of crossword grids (fat lines instead of blocked cells, uneven outline...)
* mark letters for extra solution (competition word)
* automate filling the grid (algorithm?)
* set up a paid service
* get rich
* world domination


Bugs / Todo
-----------

* If the first fields of the grid are empty, text is shifted left after saving.
  (Problem of the text format used for saving; replace space with underscore.)
* only German keyboards work well; seems we use key codes instead of character codes
* word numbers are rather small in Mozilla (and probably other browsers than WebKit-based)
* admin: if adding to an existing dict, disable other fields
* clean up redundant template/view code
* update libraries and optimize JS code
* still not really a reusable app (to be integrated in `fiëé cérébrale`_)
* still no tests!
* add Sphinx_ documentation
* add setup.py
* bind anonymous puzzles to one session to avoid puzzles being edited by several anonymous users at the same time
* add sample `settings_local.py`
* Esperanto locale is an automatical translation, I don’t speak Esperanto (but like the concept)


Internal workflow
-----------------

If you save a puzzle for the first time, a new hash code is generated
from your IP address and the local datetime.
The puzzle’s address is becoming something like “/puzzle/abcdef123456/”.

as anonymous user
^^^^^^^^^^^^^^^^^

Your saved puzzles are always public (otherwise you couldn’t access it later).
Everyone can change it.
Your solutions (i.e. questions for words) are only saved with the puzzle.

as authenticated user
^^^^^^^^^^^^^^^^^^^^^

You can decide to make your puzzles public, but only you can change it.
Your solutions are also saved to your personal dictionary.

*The following is not yet implemented:*
If you’re a staff member, your solutions can be saved to a public dictionary
and you can use non-public dictionaries.
You can export your personal dictionary to use it with your own croisee
installation.
You can claim (adopt) puzzles of anonymous users (e.g. your own, while you
weren’t logged in).


License
-------

GPLv3, see http://www.gnu.org/copyleft/gpl.html

Feel free to ask for different, additional licensing.

I don’t plan to release my edited dictionaries, because in them’s the most work.

Everything related to `fiëé visuëlle`_ (logo, names) is copyrighted and
contained only for the sake of completeness.
That means you must not use the fiëé logo, fiëé favicon or any name containing
fiëé in public, except in a descriptive manner, where it is encouraged
(e.g. “this is derived from / based on”).


Author(s)
---------

* Henning Hraban Ramm, `fiëé visuëlle`_, <hraban@fiee.net>, https://www.fiee.net
* Heiko Oberdiek: enhancement of LaTeX template,
  http://www.listserv.dfn.de/cgi-bin/wa?A2=ind1110&L=tex-d-l&T=0&P=3297
* inspiration and code snippets by several other people & projects


Dependencies
------------

* Python_ 2.7/3.5
* Django_ 1.9+
* `django registration`_
* `django guardian`_
* Fabric_ 0.9+ (optional, for easy deployment)
* jQuery_, `jQuery UI`_
* djangorestframework_ (optional)


.. _fiëé visuëlle: https://www.fiee.net
.. _fiëé cérébrale: http://www.cerebrale.net

.. _Python: http://www.python.org
.. _Sphinx: http://sphinx.pocoo.org/
.. _Fabric: http://docs.fabfile.org/
.. _South: http://south.aeracode.org/
.. _gunicorn: http://gunicorn.org/

.. _Django: http://www.djangoproject.com
.. _django registration: https://bitbucket.org/ubernostrum/django-registration/
.. _django guardian: http://packages.python.org/django-guardian/
.. _djangorestframework: http://django-rest-framework.org/

.. _YUI grids css: http://developer.yahoo.com/yui/grids/
.. _jQuery: http://docs.jquery.com/
.. _jQuery UI: http://jqueryui.com/demos/

.. _Nginx: http://wiki.nginx.org/
.. _ConTeXt: http://wiki.contextgarden.net
.. _cwpuzzle: http://ctan.org/tex-archive/macros/latex/contrib/gene/crossword
.. _Project Gutenberg: http://www.gutenberg.org

.. _ispell: http://ficus-www.cs.ucla.edu/geoff/ispell.html
.. _aspell: http://aspell.net/
