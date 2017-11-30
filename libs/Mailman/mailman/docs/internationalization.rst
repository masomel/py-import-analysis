.. _internationalization:

================================
 Mailman 3 Internationalization
================================

Mailman does not yet support IDNA (internationalized domain names, RFC
5890) or internationalized mailboxes (RFC 6531) in email addresses.
But *display names* and *descriptions* are fully internationalized in
Mailman, using Unicode.  Email content is handled by the Python email
package, which provides robust handling of internationalized content
conforming to the MIME standard (RFCs 2045-2049 and others).

The encoding of URI components addressing a REST endpoint is Unicode
UTF-8.  Mailman does not currently handle normalization, and we
recommend consistently using normal form NFC.  (For some languages
NFKC is risky, as some users' personal names may be corrupted by this
normalization.)  Mailman does not check for confusables or check
repertoire.


Introduction to Unicode Concepts
================================

The Unicode Standard is intended to provide an universal set of
characters with a single, standard encoding providing an invertible
mapping of characters to integers (called *code points* in this
context).


Repertoires
-----------

A set of characters is called a *repertoire*.  Unicode itself is
intended to provide an universal repertoire sufficient to represent
all words in all written languages, but a system may handle a
restricted repertoire and still be considered conformant, as long as
it does not corrupt characters it does not handle, and does not emit
non-character code points.


Convertibility
--------------

Unicode is intended to provide a character for each character defined
in a national character set standard.  This is often controversial:
Chinese characters are often *unified* with Japanese characters that
appear somewhat different when displayed, while the Cyrillic and Greek
equivalents of the Latin character "A" are treated as separate
characters despite being pronounced the same way and being displayed
as identical glyphs.  These judgments are informed by the notion that
a text should *round-trip*.  That is, when a text is converted from
Unicode to another encoding, and then back to Unicode, the result
should be identical to the source text.


Normalization
-------------

For several reasons, Unicode provides for construction of characters
by appending *composable characters* (such as accents) to *base
characters* (typically letters).  But since most languages assign a
code point to each accented letter, the "round-tripping" requirement
described above implies that Unicode should provide a code point for
that accented letter, called a precomposed character.  This means that
for most accented characters, there are two or more ways to represent
them, using various combinations of base characters, precomposed
characters, and composable characters.

There are also a number of cases where equivalent characters have
different code points (in a few extreme cases, the same character has
different code points because the original national standard had
duplicates).  These cases are called *compatibility* characters.

The Unicode Standard requires that the compose character sequence be
treated identically to the precomposed (single) character by all
text-processing algorithms.  For convenience in matching, an
application may choose to *normalize* texts.  There are two
normalizations.  The *NFC* normal form requires that all compositions
to precomposed characters that can be done should be done.  It has the
advantage that the length of a word in characters is the number of
code points in the word.  The *NFD* normal form requires that all
precomposed characters be decomposed into a sequence of a base
character followed by composable characters.  It useful in contexts
where fuzzy matches (*i.e.*, ignoring accents) are desired.

Finally, in each of these two forms a compatibility character may be
replaced by its *canonical equivalent*, denoted *NFKC* and *NFKD*,
respectively.


Using Unicode in Mailman
------------------------

In most cases in Mailman it is highly recommended that input be
encoded as UTF-8 in NFC format.  Although highly conformant systems
are becoming more common, there are still many systems that assume
that one code point is translated to one glyph on display.  On such
systems NFC will provide a smoother user experience than NFD.  Since
much of the text data that Mailman handles is user names, and users
frequently strongly prefer a particular compatibility character to its
canonical equivalent, NFKC (or NFKD) should be avoided.

There are two other considerations in using Unicode in Mailman.  The
first is the problem of confusables.  *Confusables* are characters
which are considered different but whose glyphs are indistinguishable,
such as Latin capital letter A and Greek capital letter Alpha.
Similarly, many code points in Unicode are not yet assigned
characters, or even defined as non-characters, and thus are not part
of the repertoire of characters represented by Unicode.

Mailman makes no attempt to detect inappropriate use of confusables or
non-characters (for example, to redirect users to a domain
disseminating malware).  The risks at present are vanishingly small
because the necessary support in the mail system itself is not yet
widespread, but this is likely to change in the near future.


Localization
============

We have it!  We just don't have proper documentation here yet.

