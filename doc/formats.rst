------------------------------------
Description of model and form fields
------------------------------------

All internal numbering is 0-based.

Directions are "horizontal" and "vertical", represented by "h" and "v".

Puzzle
======

Since puzzle have different sizes, we need flexible storage formats.
That means that we need some interpretation of the saved data.

:text:
  All letters of the puzzle’s solution as continous text, uppercase,
  lines separated by line breaks (\n), blocked cells represented by stops (.),
  empty cells represented by underscores (_) or spaces ( ).
:numbers:
  Numbers mark the start of words and relate to questions. Each "number" is
  a tuple of row, column and word number, separated by stops (.) and chained
  with commas (,), e.g. "2.3.4,2.4.5".
  *Beware*, the word number is 1-based, like displayed!
:questions:
  Questions for/descriptions of the words in the puzzle, one question per line.
  Each line starts with the question number and direction, followed by the
  question itself, all separated by double colons (::), e.g. "1::h::Meaning of Life".
  Lines are separated by line breaks (\n).


Dictionary
==========

:priority:
  An integer number, usable for sorting, with 0 being neutral.
