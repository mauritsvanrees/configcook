# -*- coding: utf-8 -*-
import logging
import six
import subprocess
import sys


logger = logging.getLogger(__name__)
MUST_CLOSE_FDS = not sys.platform.startswith('win')
INPUT_ENCODING = 'UTF-8'
if getattr(sys.stdin, 'encoding', None):
    INPUT_ENCODING = sys.stdin.encoding
OUTPUT_ENCODING = INPUT_ENCODING
if getattr(sys.stdout, 'encoding', None):
    OUTPUT_ENCODING = sys.stdout.encoding


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


def _subprocess_open(p, command, input_value, show_stderr):
    # Taken over from zest.releaser.
    i, o, e = (p.stdin, p.stdout, p.stderr)
    if input_value:
        i.write(input_value.encode(INPUT_ENCODING))
    i.close()
    stdout_output = o.read()
    stderr_output = e.read()
    # We assume that the output from commands we're running is text.
    if not isinstance(stdout_output, six.text_type):
        stdout_output = stdout_output.decode(OUTPUT_ENCODING)
    if not isinstance(stderr_output, six.text_type):
        stderr_output = stderr_output.decode(OUTPUT_ENCODING)
    # TODO.  Note that the returncode is always None, also after
    # running p.kill().  The shell=True may be tripping us up.  For
    # some ideas, see http://stackoverflow.com/questions/4789837
    if p.returncode or show_stderr or 'Traceback' in stderr_output:
        # Some error occured
        result = stdout_output + stderr_output
    else:
        # Only return the stdout. Stderr only contains possible
        # weird/confusing warnings that might trip up extraction of version
        # numbers and so.
        result = stdout_output
        if stderr_output:
            logger.debug(
                "Stderr of running command '%s':\n%s",
                format_command_for_print(command),
                stderr_output,
            )
    o.close()
    e.close()
    return result


def execute_command(command, input_value=''):
    """commands.getoutput() replacement that also works on windows

    Command must be a list of arguments.

    Taken over from zest.releaser, which took it over from zc.buildout.
    """
    if not isinstance(command, (list, tuple)):
        logger.error(
            'command argument to execute_command must be a list or tuple. '
            'Got %r.',
            command,
        )
        sys.exit(1)
    logger.debug("Running command: '%s'", format_command_for_print(command))
    env = None
    show_stderr = True
    # On Python 3, subprocess.Popen can and should be used as context
    # manager, to avoid unclosed files.  On Python 2 this is not possible.
    process_kwargs = {
        'shell': not isinstance(command, (list, tuple)),
        'stdin': subprocess.PIPE,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
        'close_fds': MUST_CLOSE_FDS,
        'env': env,
    }
    if hasattr(subprocess.Popen, '__exit__'):
        # Python 3
        with subprocess.Popen(command, **process_kwargs) as process:
            result = _subprocess_open(
                process, command, input_value, show_stderr
            )
    else:
        # Python 2
        process = subprocess.Popen(command, **process_kwargs)
        result = _subprocess_open(process, command, input_value, show_stderr)
    return result
