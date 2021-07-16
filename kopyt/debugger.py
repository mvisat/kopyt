"""Module for debugging parse functions. Not intended for public use."""

import inspect
import os
import sys

from .exception import KopytException


def debugger(klass):  # pragma: no cover
    if not bool(os.getenv("DEBUG")):
        return klass

    def decorator(method):
        def debugged_parse(self, *args, **kwargs):
            if not hasattr(self, "debug_recursion_depth"):
                self.debug_recursion_depth = 0

            if not hasattr(self, "debug_func_id"):
                self.debug_func_id = 0

            self.debug_func_id += 1
            prefix = f"{self.debug_func_id:05d}"
            indent = "-" * self.debug_recursion_depth
            name = method.__name__
            token = self.tokens.peek().value
            sys.stderr.write(f"{prefix} {indent}> {name}({token!r})")

            self.debug_recursion_depth += 1
            ret = None
            last_err = None
            try:
                ret = method(self, *args, **kwargs)
            except KopytException as err:
                last_err = err
                raise KopytException from err
            finally:
                token = self.tokens.peek().value
                ret_str = f", result: {ret!s}" if ret else ""
                err_str = f", error: {last_err!s}" if last_err else ""
                sys.stderr.write(
                    f"{prefix} <{indent} {name}({token!r}){ret_str}{err_str}\n"
                )
                self.debug_recursion_depth -= 1
                if self.debug_recursion_depth == 0:
                    sys.stderr.write("\n")
            return ret

        return debugged_parse

    for name, func in inspect.getmembers(klass, inspect.isfunction):
        if not name.startswith("parse"):
            continue
        setattr(klass, name, decorator(func))
    return klass
