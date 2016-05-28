import os
import posixpath

from git import Actor, Blob
from git import Repo
from git.exc import NoSuchPathError, ODBError

from realms import config
from realms.lib import filename_to_cname


class PageNotFound(Exception):
    pass


class Wiki(object):

    def __init__(self):
        self.repo = None
        self.path = config.WIKI_PATH
        try:
            self.repo = Repo(self.path)
        except NoSuchPathError:
            os.makedirs(self.path)
            self.repo = Repo.init(self.path)

    def write_page(self, filename, content, username, email, message, create=False):
        dirname = posixpath.join(self.path, posixpath.dirname(filename))

        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(self.path + "/" + filename, 'w') as f:
            f.write(content)

        self.repo.index.add([filename])

        git_user = Actor(username, email)
        ret = self.repo.index.commit(message, author=git_user,
                                     committer=git_user)

        return ret.hexsha

    # Move to Control
    def move(self, old, new, username, email, message):
        try:
            self.repo.heads.master.commit.tree[old]
        except KeyError:
            # old doesn't exist
            return None

        if old == new:
            return

        git_user = Actor(username, email)

        self.repo.index.move([old_filename, new_filename])

        commit = self.repo.index.commit(message, author=git_user,
                                        committer=git_user)

        return commit.hexsha

    def delete_page(self, filename, username, email, message):
        git_user = Actor(username, email)
        os.remove(os.path.join(self.path, filename))
        self.repo.index.remove([filename])
        commit = self.repo.index.commit(message, author=git_user,
                                        committer=git_user)
        return commit

    def get_page(self, filename, sha='HEAD'):
        data = {}
        try:
            blob = self.repo.tree(sha)[filename]
            data['name'] = blob.name[0:-3]
            data['sha'] = blob.hexsha
            data['path'] = blob.path
            data['mode'] = '0' + str(blob.mode)
            data['data'] = blob.data_stream.read().decode('utf-8')
            data['info'] = self.get_history(filename, limit=1)[0]
            return data

        except (KeyError, ODBError):
            raise PageNotFound()

    def get_index(self):
        rv = []
        try:
            for i in self.repo.tree().list_traverse():
                if isinstance(i, Blob):
                    rv.append(dict(name=filename_to_cname(i.path),
                                   filename=i.path,
                                   ctime=0,
                                   mtime=0,
                                   sha=i.hexsha,
                                   size=i.size))
        except ValueError:
            # No history/files
            return []

        return rv

    def get_history(self, filename, limit=100):
        if not len(self.repo.tree().list_traverse()):
            # Index is empty, no commits
            return []

        versions = []

        for commit in self.repo.iter_commits(paths=filename, max_count=limit):
            change_type = None
            actor = commit.author
            author_name = actor.name
            author_email = actor.email
            versions.append(dict(
                author=author_name.strip(),
                author_email=author_email,
                time=commit.authored_date,
                message=commit.message,
                sha=commit.hexsha,
                type=change_type))

        return versions
