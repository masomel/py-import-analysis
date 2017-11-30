# -*- coding: utf-8 -*-

import os
import json

import click

from .__pkg__ import __version__
from .api import find
from .utils import split_params


# Borrowed from http://click.pocoo.org/5/advanced/.
class AliasedGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


@click.group(cls=AliasedGroup, invoke_without_command=True)
@click.option('-v', '--version', is_flag=True, default=False,
              help='Finder tool version.')
@click.pass_context
def finder(ctx, version):
    """Command line interface for searching a given pattern/text in the given
    directory/file path.
    """
    if version:
        click.echo(__version__)


@finder.command('search')
@click.option('--path', default=os.getcwd(),
              help='Searches for the pattern in the directory/file path '
                   'provided. If a directory/file path is not provided, the '
                   'tool searches for the pattern in the current working '
                   'directory.',
              metavar='path1[,path2,...,pathN]')
@click.option('pattern', '-P', '--pattern', '--text', required=True,
              help='Text to be searched.',
              metavar='<pattern>')
@click.option('-v', '--verbose', is_flag=True, default=False,
              help='Some files cannot be opened and searched for the given '
                   'pattern. For example, kernel files which generate content '
                   'on go, files which are not utf-8 encoded, etc. You can '
                   'use this flag if you need a detailed output of which file '
                   'has an error.')
@click.pass_context
def search(ctx, path, pattern, verbose):
    """Searches for the given pattern in the directory/file path provided."""
    for result in find(*split_params(path), pattern=pattern):
        _result = json.loads(result)
        path = _result['path']
        items = _result['items']
        errors = _result['error']

        if items:
            for item in items:
                click.echo('{path}:{line_number}: {line}'
                           .format(path=path,
                                   line_number=item['line_number'],
                                   line=item['line']))

        if errors and verbose:
            for error in errors:
                click.echo('{type}:{path}:{message} {extra}'
                           .format(type=error['type'],
                                   path=path,
                                   message=error['message'],
                                   extra=error['extra'] or ''))
