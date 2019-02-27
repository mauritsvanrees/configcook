# -*- coding: utf-8 -*-
import logging
import os
import subprocess
import tempfile


logger = logging.getLogger(__name__)


def format_command_for_print(command):
    # Taken over from zest.releaser.
    # THIS IS INSECURE! DO NOT USE except for directly printing the
    # result.
    # Poor man's argument quoting, sufficient for user information.
    # Used since shlex.quote() does not exist in Python 2.7.
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
    out = ''
    err = ''
    outfile = tempfile.mkstemp()
    errfile = tempfile.mkstemp()
    try:
        exitcode = subprocess.call(
            command, stdout=outfile[0], stderr=errfile[0]
        )
    finally:
        with open(outfile[1]) as myfile:
            out = myfile.read()
        with open(errfile[1]) as myfile:
            err = myfile.read()
        # remove the temporary files
        os.remove(outfile[1])
        os.remove(errfile[1])
    return exitcode, out, err
