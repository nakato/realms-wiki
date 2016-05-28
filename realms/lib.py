import re
import os


def to_canonical(s):
    """
    Remove leading/trailing whitespace (from all path components)
    Remove leading underscores and slashes "/"
    Convert spaces to dashes "-"
    Limit path components to 63 chars and total size to 436 chars
    """
    reserved_chars = "&$+,:;=?@#"
    unsafe_chars = "?<>[]{}|\^~%"

    s = re.sub(r"\s+", " ", s)
    s = s.lstrip("_/ ")
    s = re.sub(r"[" + re.escape(reserved_chars) + "]", "", s)
    s = re.sub(r"[" + re.escape(unsafe_chars) + "]", "", s)
    # Strip leading/trailing spaces from path components, replace internal spaces
    # with '-', and truncate to 63 characters.
    parts = (part.strip().replace(" ", "-")[:63] for part in s.split("/"))
    # Join any non-empty path components back together
    s = "/".join(filter(None, parts))
    s = s[:436]
    return s


def cname_to_filename(cname):
    """ Convert canonical name to filename

    :param cname: Canonical name
    :return: str -- Filename

    """
    return cname + ".md"


def filename_to_cname(filename):
    """Convert filename to canonical name.

    .. note::

    It's assumed filename is already canonical format

    """
    return os.path.splitext(filename)[0]
