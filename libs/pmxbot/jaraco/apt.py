from __future__ import unicode_literals

import re

import six

class PackageName(six.text_type):
    """A package name possibly with other attributes"""
    @classmethod
    def from_apt(cls, name):
        automatic = name.endswith('{a}')
        if automatic:
            name = name[:-3]
        res = cls(name)
        res.automatic = automatic
        return res

def parse_new_packages(apt_output, include_automatic=False):
    """
    Given the output from an apt or aptitude command, determine which packages
    are newly-installed.
    """
    pat = r'^The following NEW packages will be installed:[\r\n]+(.*?)[\r\n]\w'
    matcher = re.search(pat, apt_output, re.DOTALL | re.MULTILINE)
    if not matcher: return []
    new_pkg_text = matcher.group(1)
    raw_names = re.findall(r'[\w{}\.+-]+', new_pkg_text)
    all_packages = list(map(PackageName.from_apt, raw_names))
    manual_packages = [pack for pack in all_packages if not pack.automatic]
    return all_packages if include_automatic else manual_packages
