# -*- coding: utf-8 -*-
from .exceptions import ConfigError
import functools
import logging
import os
import re
import six
import subprocess
import sys
import tempfile
import time


logger = logging.getLogger(__name__)
# pattern for ${part:option}
substitution_pattern = re.compile(r"\${([^:]*):([^}]+)}")


def substitute(config, text, current_part=""):
    """Get substitution value.

    Get the real value from something like ${part:option}.
    """
    if not isinstance(text, six.string_types):
        # Nothing to substitute here.
        return text
    for part, option in substitution_pattern.findall(text):
        template = "${%s:%s}" % (part, option)
        if not part:
            # ${:option} points to the current part
            part = current_part
        try:
            value = config[part][option]
        except KeyError:
            raise ConfigError(
                "Unable to substitute '{0}' from config.".format(template)
            )
        logger.debug("Substituting %r with %r", template, value)
        # TODO: call recursively if needed.
        text = text.replace(template, value)
    return text


def format_command_for_print(command):
    # Taken over from zest.releaser.
    # THIS IS INSECURE! DO NOT USE except for directly printing the
    # result.
    # Poor man's argument quoting, sufficient for user information.
    # Used since shlex.quote() does not exist in Python 2.7.
    if not isinstance(command, (list, tuple)):
        raise ValueError("Must be list or tuple: %r" % command)
    args = []
    for arg in command:
        if " " in arg:
            arg = "'{}'".format(arg)
        args.append(arg)
    return " ".join(args)


def call_or_fail(command):
    """Call a command or fail (raise an exception).

    Call this when you want the program to quit in case of an error.
    The most likely exceptions are OSError and subprocess.CalledProcessError.
    """
    return subprocess.check_call(command)


def call_with_exitcode(command):
    """Call a command and return the exit code.

    Call this when you want the user to see the output and errors,
    and the code is only interested in the exitcode.
    """
    return subprocess.call(command)


def call_with_output_or_fail(command):
    """Call a command and return the output or fail (raise an exception).

    Call this when you want to catch the output,
    and want the program to quit in case of an error.
    The most likely exceptions are OSError and subprocess.CalledProcessError.
    """
    return subprocess.check_output(command)


def call_with_out_and_err(command):
    """Call a command and return the exit code, output and errors.

    Call this when you want to use all three return values,
    for example to log the output with INFO, and the errors with DEBUG
    (or with log level ERROR), and to handle the exitcode.
    """
    out = ""
    err = ""
    outfile = tempfile.mkstemp()
    errfile = tempfile.mkstemp()
    try:
        exitcode = subprocess.call(command, stdout=outfile[0], stderr=errfile[0])
    finally:
        with open(outfile[1]) as myfile:
            out = myfile.read()
        with open(errfile[1]) as myfile:
            err = myfile.read()
        # remove the temporary files
        os.remove(outfile[1])
        os.remove(errfile[1])
    return exitcode, out, err


def entrypoint_function(fun):
    @functools.wraps(fun)
    def wrapper_entrypoint_function(*args, **kwargs):
        # Get a nice name to identify this extension or part/recipe.
        instance = args[0]
        if instance.is_extension:
            name = "extension {0}".format(instance.name)
        elif instance.is_recipe:
            name = "part {0} [recipe {1}]".format(instance.name, instance.recipe_name)
        else:
            name = instance.name
        logger.debug("Calling function %s of %s.", fun.__name__, name)
        start = time.time()
        result = fun(*args, **kwargs)
        end = time.time()
        run_time = end - start
        logger.debug(
            "Finished in %.4f seconds: function %s of %s.", run_time, fun.__name__, name
        )
        return result

    return wrapper_entrypoint_function


def call_extensions(fun):
    @functools.wraps(fun)
    def wrapper_call_extensions(*args, **kwargs):
        instance = args[0]
        function_name = fun.__name__
        if instance.extensions:
            start_ext = time.time()
            logger.debug(
                "Calling extensions.run_before for function %s.", function_name
            )
            for extension in instance.extensions:
                if hasattr(extension, "run_before"):
                    extension.run_before(function_name, *args, **kwargs)
        logger.debug("Calling function %s.", function_name)
        start = time.time()
        result = fun(*args, **kwargs)
        end = time.time()
        run_time = end - start
        if instance.extensions:
            logger.debug("Calling extensions.run_after for function %s.", function_name)
            for extension in instance.extensions:
                if hasattr(extension, "run_after"):
                    extension.run_after(function_name, *args, **kwargs)
            end_ext = time.time()
            ext_time = end_ext - start_ext
            logger.debug(
                "Finished in %.4f seconds (%.4f including extensions): function %s.",
                run_time,
                ext_time,
                function_name,
            )
        else:
            logger.debug(
                "Finished in %.4f seconds: function %s.", run_time, function_name
            )
        return result

    return wrapper_call_extensions


def to_bool(value):
    """Turn a value into True or False."""
    if isinstance(value, bool):
        return value
    if not isinstance(value, six.string_types):
        raise ValueError("Must be text: %r" % value)
    if not value:
        return False
    # Check on/off:
    if value == "on":
        return True
    if value == "off":
        return False
    orig_value = value
    # Check only the first character:
    value = value[0].lower()
    # yes/true/1
    if value in ("y", "t", "1"):
        return True
    # no/false/0
    if value in ("n", "f", "0"):
        return False
    raise ValueError(
        "Cannot interpret as boolean, try true/false instead: %r" % orig_value
    )


def to_list(value):
    """Turn a value into a list."""
    if isinstance(value, list):
        return value
    if not isinstance(value, six.string_types):
        raise ValueError("Must be text: {0!r}".format(value))
    return value.strip().split()


def to_path(value):
    """Turn a value into an absolute path."""
    if not isinstance(value, six.string_types):
        raise ValueError("Must be text: {0!r}".format(value))
    return os.path.realpath(os.path.expanduser(value))


def set_defaults(defaults, options):
    """Add defaults to options.

    options are user-supplied, defaults are from the main configcook,
    or an extension or a recipe.

    Both must be dictionaries.
    The values of defaults must be dictionaries like this:
    {"default": "bin", "parser": to_path, "required": True},
    where none of the keys are mandatory.

    "required" means the key must be in the options,
    AND it must have a true value.  So if the option is there
    but is empty, we raise an error.
    If you want to make an option required but accept an empty value,
    you should arrange that in your own parser.

    When there is a parser, this may also be applied to the default value:
    a default "bin" or "~" could be expanded to an absolute path by parser 'to_path'.

    This changes the dictionary in-place.  (Or raises an exception.)
    """
    for key, value in defaults.items():
        default = value.get("default")
        parser = value.get("parser")
        required = value.get("required", False)
        if key in options:
            orig_value = options[key]
        elif required:
            raise ValueError("Option {0} is missing.".format(key))
        else:
            orig_value = default
            logger.debug("Set %s option to default %r.", key, default)
        if parser is None:
            new_value = orig_value
        else:
            new_value = parser(orig_value)
        if required and not new_value:
            raise ValueError(
                "Option {0} is required to be non empty. Got: {1} (parsed as {2}).".format(
                    key, orig_value, new_value
                )
            )
        options[key] = new_value
