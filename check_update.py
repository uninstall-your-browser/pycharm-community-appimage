import os
from typing import Iterable

from github import Github, Auth
from github.GitReleaseAsset import GitReleaseAsset

product_release_prefix = os.environ.get("PRODUCT_RELEASE_PREFIX") + "/"

g = Github(auth=Auth.Token(os.environ.get("GH_TOKEN", None)))

print(f"{os.environ["GITHUB_REPOSITORY"]=}")

this_repo = g.get_repo(os.environ["GITHUB_REPOSITORY"])

try:
    latest_custom_release = this_repo.get_releases()[0].tag_name
except IndexError:
    latest_custom_release = ""

jetbrains_repo = g.get_repo("JetBrains/intellij-community", lazy=True)


def set_output(name: str, value: str):
    if os.environ.get("GITHUB_RUNNING_ACTION", "false") == "true":
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            fh.write(f"{name}={value}\n")
    else:
        print(f"{name}={value}")


def find_linux_release_asset(assets: Iterable[GitReleaseAsset]) -> GitReleaseAsset:
    for asset in assets:
        if asset.name.endswith("tar.gz") and "-aarch64" not in asset.name:
            return asset

    raise RuntimeError("couldn't find any suitable release asset")


for release in jetbrains_repo.get_releases():
    release_name = release.tag_name

    if release_name.startswith(product_release_prefix):
        print(f"Inspecting release {release_name}")
        latest_product_version = release.tag_name.lstrip(product_release_prefix)
        needs_update = latest_product_version > latest_custom_release

        print(f"{latest_custom_release=} {latest_product_version=}, {needs_update=}")

        if needs_update:
            set_output("download_url", find_linux_release_asset(release.assets).browser_download_url)

        set_output(
            "needs_update",
            str(needs_update).lower(),
        )
        break
    else:
        print(f"Ignored release {release_name}")
else:
    raise RuntimeError("WHERE ARE THE RELEASES????")
