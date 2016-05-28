import ghdiff

from realms.lib import cname_to_filename
from realms.modules.wiki import storage


class WikiController(object):

    default_committer_name = 'Anon'
    default_committer_email = 'anon@anon.anon'

    def __init__(self):
        self.storage = storage.Wiki()

    def _get_user(self, username, email):
        if not username:
            username = self.default_committer_name
        if not email:
            email = self.default_committer_email

        return username, email

    def rollback(self, name, commit, message, username=None, email=None):
        page = self.get_page(name, commit_sha)

        username, email = self._get_user(username, email)

        return self.write_page(name, page['data'], message=message, username=username, email=email)

    def compare(self, name, old_sha, new_sha):
        old = self.get_page(name, sha=old_sha)
        new = self.get_page(name, sha=new_sha)
        return ghdiff.diff(old['data'], new['data'])

    def exists(self, name, ref='HEAD', error=False):
        try:
            _ = self.get_page(name, sha=ref)
            return True
        except storage.PageNotFound:
            if error:
                raise
            return False

    def rename_page(self, old_name, new_name, username=None, email=None, message=None):
        username, email = self._get_user(username, email)
        old = cname_to_filename(old_name)
        new = cname_to_filename(new_name)

        if not message:
            message = "Moved %s to %s" % (old_name, new_name)

        try:
            sha = self.storage.move(old, new, username, email, message)
        except storage.PageNotFound:
            # FIXME: Currently doesn't raise this exception or a same file exception or page-exists exception.
            pass

        return sha

    # XXX Placeholders
    def write_page(self, name, content, username=None, email=None, message=None, create=False):
        username, email = self._get_user(username, email)
        cname = to_canonical(name)
        filename = cname_to_filename(cname)
        if not message:
            message = "Updated %s" % name
        self.storage.write_page(filename, content, username, email, message=message, create=create)

    def delete_page(self, name, username=None, email=None, message=None):
        username, email = self._get_user(username, email)
        if not message:
            message = "Deleted %s" % name
        filename = cname_to_filename(name)
        return self.storage.delete_page(filename, username, email, message=message)

    def get_page(self, name, sha='master'):
        filename = cname_to_filename(name)
        return self.storage.get_page(filename, sha=sha)

    def get_index(self):
        return self.storage.get_index()

    def get_history(self, name, limit=100):
        filename = cname_to_filename(name)
        return self.storage.get_history(filename, limit=limit)
