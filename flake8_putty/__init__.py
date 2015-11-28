# -*- coding: utf-8 -*-
"""Allow more user control over ignoring flake8 errors."""
from __future__ import absolute_import, unicode_literals, with_statement

from flake8_putty.extension import PuttyExtension

__version__ = '0.1.0'

__all__ = ('PuttyExtension', )

PuttyExtension.version = __version__
