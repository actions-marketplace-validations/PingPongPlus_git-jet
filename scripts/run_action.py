"""Generate assets in the caller workspace; publishing is an explicit separate step."""

import os
import sys
from pathlib import Path

from git_jet.cli import main


def run():
    try:
        workspace = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
        output = (workspace / os.environ.get("JET_OUTPUT_DIR", "git-jet-output")).resolve()
        if not output.is_relative_to(workspace) or output == workspace:
            raise ValueError("output-dir must be a subdirectory inside the caller workspace")
        username = os.environ.get("JET_USERNAME") or os.environ["JET_REPOSITORY_OWNER"]
        if any(char in str(output) for char in "\r\n"):
            raise ValueError("output path must not contain line breaks")
        demo = os.environ.get("JET_DEMO", "false").strip().lower()
        if demo not in ("true", "false"):
            raise ValueError("demo must be true or false")
        auto_compress = os.environ.get("JET_AUTO_COMPRESS", "true").strip().lower()
        if auto_compress not in ("true", "false"):
            raise ValueError("auto-compress must be true or false")
        args = [
            "render",
            "--output-dir",
            str(output),
            "--scale",
            os.environ.get("JET_SCALE", "2"),
            "--fps",
            os.environ.get("JET_FPS", "20"),
            "--jets",
            os.environ.get("JET_JETS", "1"),
            "--carrier",
            os.environ.get("JET_CARRIER", "lincoln"),
            "--water",
            os.environ.get("JET_WATER", "ocean"),
            "--graph-theme",
            os.environ.get("JET_GRAPH_THEME", "blue"),
        ]
        if demo == "true":
            args += ["--demo", "--days", os.environ.get("JET_DAYS", "365")]
        else:
            args += ["--username", username, "--days", os.environ.get("JET_DAYS", "365")]
        seed = os.environ.get("JET_SEED", "")
        if seed:
            args += ["--seed", seed]
        if auto_compress == "false":
            args += ["--no-auto-compress"]
        code = main(args)
        if code:
            return code
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as stream:
            for key, value in {
                "gif": output / "git-jet.gif",
                "png": output / "git-jet.png",
                "calendar": output / "calendar.json",
                "publish-script": Path(__file__).resolve().with_name("publish_assets.py"),
            }.items():
                stream.write(f"{key}={value}\n")
        return 0
    except (KeyError, OSError, ValueError) as error:
        print(f"::error::Git Jet configuration: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
