import os
import subprocess
import sys

from workflow import Workflow3


WORKSPACE_DIR = os.path.expanduser(os.environ.get("ALFRED_WORKSPACE_DIR", "~/code"))
GITHUB_URL = "https://github.com/{}"


def main(wf):
    query = wf.args[0] if wf.args else None
    # TODO: Smarter caching? Only on file changes...?
    # TODO: Can Alfred itself handle caching and/or fitlering for us?
    #       What do we gain by handling it ourselves?
    repos = wf.cached_data("repos", get_repos, max_age=600)
    if query:
        repos = wf.filter(query, repos, key=get_repo_search_key)
    for repo in repos:
        title = "/".join([repo["author"], repo["name"]])
        wf.add_item(
            title=title,
            subtitle=repo["url"],
            arg=repo["url"],
            valid=True,
        )
    wf.send_feedback()


def get_repo_search_key(repo):
    return u" ".join(
        [
            repo["author"],
            repo["name"],
        ]
    )


def get_repos(workspace_dir=WORKSPACE_DIR):
    repos = []
    for file_name in os.listdir(workspace_dir):
        path = os.path.join(workspace_dir, file_name)

        if not os.path.isdir(path):
            continue

        # Get subtitle from readme
        # readme_path = os.path.join(path, "README.md")
        # if os.path.isfile(readme_path):
        #     with open(readme_path) as f:
        #         line = ""
        #         while True:
        #             try:
        #                 line = next(f).strip()
        #             except StopIteration:
        #                 break
        #             if line and not (
        #                 line.startswith("#")
        #                 or line.startswith("![")
        #                 or line.startswith("[![")
        #             ):
        #                 break
        #         subtitle = line
        # else:
        #     subtitle = ""

        # Get the github url
        # git_folder = os.path.join(path, ".git")
        # if not os.path.isdir(git_folder):
        #     continue

        try:
            output = subprocess.check_output(["git", "remote", "-v"], cwd=path)
        except subprocess.CalledProcessError:
            continue

        lines = output.split("\n")
        for line in lines:
            if line.startswith("origin"):
                github_suffix = line.split()[1].split(":")[1]
                break
        else:
            # no origin remote
            continue

        url = GITHUB_URL.format(github_suffix)
        if url.endswith(".git"):
            url = url[:-4]
        # git_config_path = os.path.join(git_folder, "config")
        # config = ConfigParser.ConfigParser()
        # print(git_config_path)
        # with open(git_config_path) as f:
        #     text = "".join(l.lstrip() for l in f.read())
        #     config = config.read(text)

        # item = {
        #     "title": file_name,
        #     "subtitle": subtitle,
        # }

        author = github_suffix.split("/")[0].lower()

        # title = "/".join([author, file_name])

        repos.append({"author": author, "name": file_name, "url": url})
    return repos


wf = Workflow3()
sys.exit(wf.run(main))
