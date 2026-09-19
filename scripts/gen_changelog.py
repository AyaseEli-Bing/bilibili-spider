#!/usr/bin/env python3
"""从 git commit 历史生成 changelog（用于 Release 说明）。

约定：commit message 使用 Conventional Commits 风格前缀
  feat:xxx  -> 新增
  fix:xxx   -> 修复
  其他       -> 其他
输出 markdown，供 `gh release create --notes-file` 使用。
"""
from __future__ import annotations

import subprocess


def run(cmd: str) -> str:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


def main() -> None:
    tags = [t for t in run("git tag --sort=-creatordate").split("\n") if t]
    current = tags[0] if tags else run("git rev-parse --short HEAD")
    prev = tags[1] if len(tags) > 1 else ""

    if prev:
        log = run(f'git log {prev}..HEAD --pretty=format:"%s"')
    else:
        log = run('git log --pretty=format:"%s"')

    features: list[str] = []
    fixes: list[str] = []
    others: list[str] = []
    for raw in log.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("feat"):
            features.append(line)
        elif line.startswith("fix"):
            fixes.append(line)
        else:
            others.append(line)

    out = [f"## {current}", ""]
    if features:
        out += ["### 新增", ""]
        out += [f"- {f}" for f in features]
        out += [""]
    if fixes:
        out += ["### 修复", ""]
        out += [f"- {f}" for f in fixes]
        out += [""]
    if others:
        out += ["### 其他", ""]
        out += [f"- {o}" for o in others]
        out += [""]
    print("\n".join(out))


if __name__ == "__main__":
    main()
