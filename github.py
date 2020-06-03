import os
import re
import subprocess
import sys

from workflow import Workflow3


WORKSPACE_DIR = os.path.expanduser(os.environ.get("ALFRED_WORKSPACE_DIR", "~/code"))


class Repository:
    def __init__(self, author, name):
        self.author = author
        self.name = name

    GITHUB_URL = "https://github.com/{}/{}"

    @property
    def url(self):
        return self.GITHUB_URL.format(self.author, self.name)

    @property
    def search_key(self):
        return u" ".join(
            [
                self.author,
                self.name,
            ]
        )

    @classmethod
    def from_dir(cls, path):
        if not os.path.isdir(path):
            raise ValueError("{} is not a directory".format(path))
        try:
            with open(os.devnull, "wb") as devnull:
                output = subprocess.check_output(
                    ["git", "remote", "-v"],
                    cwd=path,
                    stderr=devnull,
                )
        except subprocess.CalledProcessError:
            raise ValueError("{} is not a git repository".format(path))
        author, name = Repository._parse_git_remote(output.decode())
        if name.endswith(".git"):
            name = name[:-4]
        return cls(author, name)

    GIT_REMOTE_PATTERN = re.compile(
        r"^origin\sgit@github\.com:(.*)\/(.*)\s\((?:fetch|push)\).*$"
    )

    @classmethod
    def _parse_git_remote(cls, string):
        lines = string.split("\n")
        for line in lines:
            line = line.lower().strip()
            match = cls.GIT_REMOTE_PATTERN.match(line)
            if match:
                return match.groups()
        raise ValueError("string has no 'origin' remote")

    def as_alfred_item(self):
        title = "{}/{}".format(self.author, self.name)
        return dict(
            title=title,
            subtitle=self.url,
            arg=self.url,
            valid=True,
        )


def get_repos(workspace_dir=WORKSPACE_DIR):
    repos = []
    for d in os.listdir(workspace_dir):
        d = os.path.join(workspace_dir, d)
        try:
            repo = Repository.from_dir(d)
        except ValueError:
            pass
        else:
            repos.append(repo)
    return repos


def main(wf):
    query = wf.args[0] if wf.args else None
    repos = wf.cached_data("repos", get_repos, max_age=60*60*24)
    if query:
        repos = wf.filter(query, repos, lambda x: x.search_key)
    for repo in repos:
        wf.add_item(**repo.as_alfred_item())
    wf.send_feedback()


if __name__ == "__main__":
    wf = Workflow3()
    sys.exit(wf.run(main))
