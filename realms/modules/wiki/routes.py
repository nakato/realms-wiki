import base64
import itertools
import sys
import time

import falcon
from jinja2 import Environment, PackageLoader, Markup, escape

import json

import realms
from realms.lib import to_canonical
from realms import config
from realms.modules.wiki.storage import PageNotFound, Wiki
from realms.modules.wiki import control


class Render(object):

    control = control.WikiController()

    jEnv = Environment(loader=PackageLoader('realms', 'templates'))
    jEnv.filters['datetime'] = lambda ts: time.strftime('%b %d, %Y %I:%M %p', time.localtime(ts))
    jEnv.filters['b64encode'] = lambda s: base64.urlsafe_b64encode(s.encode('utf-8')).decode('utf-8').rstrip("=")

    def escape_page(self, page):
        data = page.copy()
        for key in data.keys():
            data[key] = escape(data[key])
        return json.dumps(data)

    def render(self, *args, **kwargs):
        template = self.jEnv.get_or_select_template(self.TEMPLATE)
        render = template.render(*args, **kwargs, config=config, gassets=realms.gassets)
        return render


class Get(Render):

    def on_get(self, req, resp, path):
        cname = to_canonical(path)
        try:
            data = self.control.get_page(cname)
        except PageNotFound:
            raise falcon.HTTPNotFound()
        data = self.escape_page(data)
        resp.body = data
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200


class Commit(Render):

    TEMPLATE = 'wiki/page.html'

    def on_get(self, req, resp, sha, path):
        cname = to_canonical(path)
        try:
            data = self.control.get_page(cname, sha=sha)
        except PageNotFound:
            raise falcon.HTTPNotFound()
        data = self.escape_page(data)
        resp.body = self.render(name=path, page=data, commit=sha)
        resp.content_type = 'text/html'
        resp.status = falcon.HTTP_200


class Compare(Render):

    TEMPLATE = 'wiki/compare.html'

    def on_get(self, req, resp, path, fsha, lsha):
        diff = self.control.compare(path, fsha, lsha)
        resp.body = self.render(name=path, diff=diff, old=fsha, new=lsha)
        resp.content_type = 'text/html'
        resp.status = falcon.HTTP_200


class Revert(object):

    def on_post(self, req, resp):
        body = b''
        while True:
            chunk = req.stream.read(4096)
            if not chunk:
                break
            body += chunk
        body = body.decode('utf-8')
        query = falcon.util.uri.parse_query_string(
            body, keep_blank_qs_values=True)
        cname = to_canonical(query['name'])
        commit = query['commit']
        message = query.get('message', 'Reverting %s' % cname)

        try:
            sha = self.control.rollback(cname,
                                        commit,
                                        message=message)
        except PageNotFound:
            raise falcon.HTTPNotFound()

        resp.body = str(dict(sha=sha))
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200


class History(Render):

    TEMPLATE = 'wiki/history.html'

    def on_get(self, req, resp, path):
        hist = self.control.get_history(path)
        resp.body = self.render(name=path, history=hist)
        resp.content_type = 'text/html'
        resp.status = falcon.HTTP_200


class Edit(Render):

    TEMPLATE = 'wiki/edit.html'

    def on_get(self, req, resp, path):
        cname = to_canonical(path)
        try:
            page = self.control.get_page(cname)
        except PageNotFound:
            raise falcon.HTTPFound('/_create/%s' % cname)

        info = json.dumps(page.get('info'))
        sha = page.get('sha')
        resp.body = self.render(name=cname, content=page.get('data'),
                                info=info, sha=sha)
        resp.content_type = 'text/html'
        resp.status = falcon.HTTP_200


# XXX TODO: Join with Edit
class Create(Render):

    TEMPLATE = 'wiki/edit.html'

    def on_get(self, req, resp, path=""):
        cname = to_canonical(path)
        if cname and self.control.exists(cname):
            raise falcon.HTTPFound('/_edit/%s' % cname)
        resp.body = self.render(name=cname, content="", info={})
        resp.content_type = 'text/html'
        resp.status = falcon.HTTP_200


class Index(Render):

    TEMPLATE = 'wiki/index.html'

    def _get_subdir(self, path, depth):
        parts = path.split('/', depth)
        if len(parts) > depth:
            return parts[-2]

    def _tree_index(self, items, path=""):
        depth = len(path.split("/"))
        items = filter(lambda x: x['name'].startswith(path), items)
        items = sorted(items, key=lambda x: x['name'])
        for subdir, items in itertools.groupby(
                items, key=lambda x: self._get_subdir(x['name'], depth)):
            if not subdir:
                for item in items:
                    yield dict(item, dir=False)
            else:
                size = 0
                ctime = sys.maxint
                mtime = 0
                for item in items:
                    size += item['size']
                    ctime = min(item['ctime'], ctime)
                    mtime = max(item['mtime'], mtime)
                yield dict(name=path + subdir + "/",
                           mtime=mtime,
                           ctime=ctime,
                           size=size,
                           dir=True)

    def on_get(self, req, resp, path=""):
        items = self.control.get_index()
        if path:
            path = to_canonical(path) + "/"

        index = self._tree_index(items, path=path)
        resp.body = self.render(index=index, path=path)
        resp.content_type = 'text/html'
        resp.status = falcon.HTTP_200


class Page(Render):

    TEMPLATE = 'wiki/page.html'

    def on_get(self, req, resp, path='home'):
        cname = to_canonical(path)
        if cname != path:
            raise falcon.HTTPFound('/%s' % cname)

        try:
            data = self.control.get_page(cname)
        except PageNotFound:
            raise falcon.HTTPFound('/_create/%s' % cname)

        data = self.escape_page(data)
        resp.body = self.render(name=cname, page=data)
        resp.content_type = 'text/html'
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp, path=None):
        if path is None:
            return
        cname = to_canonical(path)
        if not cname:
            return dict(error=True, message="Invalid name")

        body = b''
        while True:
            chunk = req.stream.read(4096)
            if not chunk:
                break
            body += chunk
        body = body.decode('utf-8')
        query = falcon.util.uri.parse_query_string(
            body, keep_blank_qs_values=True)
        content = query['content']
        message = query['message']
        sha = self.control.write_page(cname, content, message, create=True)
        resp.body = str(dict(sha=sha))
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_201

    def on_put(self, req, resp, path=None):
        if path is None:
            return
        cname = to_canonical(path)
        if not cname:
            return dict(error=True, message="Invalid name")

        edit_cname = to_canonical(req.path)

        if edit_cname != cname:
            self.control.rename_page(cname, edit_cname)

        body = b''
        while True:
            chunk = req.stream.read(4096)
            if not chunk:
                break
            body += chunk
        body = body.decode('utf-8')
        query = falcon.util.uri.parse_query_string(
            body, keep_blank_qs_values=True)
        content = query['content']
        message = query['message']
        sha = self.control.write_page(edit_cname, content, message)
        resp.body = str(dict(sha=sha))
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_200

    def on_delete(self, req, resp, path=None):
        if path is None:
            return
        cname = to_canonical(path)
        if not cname:
            return dict(error=True, message="Invalid name")
        sha = self.control.delete_page(cname)
        resp.body = str(dict(sha=sha))
        resp.content_type = 'application/json'
        resp.status = falcon.HTTP_204
