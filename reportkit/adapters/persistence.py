"""落盘：把渲染好的报表写到文件。"""

import os

from ..formatting.render import render_report


def write_report(buckets, path, title="Report", problems=None, notes=None, include_tax=False):
    """把报表写到文件，返回写出去的字节数。"""
    text = render_report(buckets, title=title, problems=problems, notes=notes, include_tax=include_tax)
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return len(text.encode("utf-8"))
