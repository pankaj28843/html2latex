from __future__ import absolute_import

# Standard Library
import hashlib
import os
import re
import subprocess
import uuid

# Third Party Stuff
import jinja2
import redis
from lxml import etree
from splinter import Browser

from ..webkit2png import webkit2png
from .spellchecker import check_spelling_in_html

browser = Browser('phantomjs')
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
REGEX_SN = re.compile(r'(?i)\s*(s\s*\.*\s*no\.*|s\s*\.*\s*n\.*)\s*')


def get_image_for_html_table(html, do_spellcheck=False):
    """ Convert HTML table to image to put in latex"""
    html = html.strip()
    if do_spellcheck:
        html = check_spelling_in_html(html)

    wait_time = 0
    root = etree.HTML(html)
    if root.find('.//span[@class="math-tex"]') is not None:
        # mathjax equations present
        wait_time = 10

    td = root.find(".//td")
    if td is not None and td.find('.//span[@class="math-tex"]') is None:
        td_html = etree.tostring(td)
        html = html.replace(td_html, REGEX_SN.sub(" SN ", td_html, 1), 1)

    hashed_html = u"webkit2png-{0}".format(
        hashlib.sha512(html).hexdigest())

    existing_image_file = redis_client.get(hashed_html)

    if existing_image_file:
        if os.path.isfile(existing_image_file):
            return existing_image_file

    STATIC_ROOT = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '../static',
    )
    context = {
        "table_inner_html": html,
        "STATIC_ROOT": STATIC_ROOT,
    }

    loader = jinja2.FileSystemLoader(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            '../templates',
        )
    )
    jinja2_env = jinja2.Environment(loader=loader)
    template = jinja2_env.get_template('web2png-table.html')
    html = template.render(**context)

    unique_id = str(uuid.uuid4())
    html_file = u"/var/tmp/{0}.html".format(unique_id)
    with open(html_file, "wb") as f:
        f.write(html)

    image_file = u"/var/tmp/{0}.png".format(unique_id)
    url = u"file://{0}".format(html_file)

    if wait_time > 0:
        webkit2png(
            url, image_file, browser=browser, wait_time=wait_time)
    else:
        p = subprocess.Popen(
            ["html2latex_webkit2png.py", "-o", image_file, html_file])
        p.wait()

    redis_client.set(hashed_html, image_file)

    return image_file
