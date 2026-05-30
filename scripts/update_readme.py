"""
GitHub Profile README · 自动更新脚本
功能: 更新 Total Stars / Commits / Repos 徽章
通过 HTML 注释标记 <!-- START_SECTION:github-stats --> 定位
"""

import os, re, sys, json
from datetime import datetime, timezone
from pathlib import Path
import urllib.request

GITHUB_USERNAME = "xiachong07"
README_PATH = Path(__file__).resolve().parent.parent / "README.md"

TOKEN = os.getenv("GITHUB_TOKEN", "")


def api(url: str) -> dict | list:
    """带鉴权的 GET 请求。"""
    headers = {
        "User-Agent": "Readme-Updater/2.0",
        "Accept": "application/vnd.github.v3+json",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def get_stats() -> dict:
    """获取 Stars / Repos / Followers。"""
    user = api(f"https://api.github.com/users/{GITHUB_USERNAME}")

    # 累加所有仓库 Star
    stars = 0
    page = 1
    while True:
        repos = api(
            f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
            f"?per_page=100&page={page}"
        )
        if not repos:
            break
        stars += sum(r.get("stargazers_count", 0) for r in repos)
        page += 1

    return {
        "stars": stars,
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
    }


def get_total_commits() -> int:
    """通过 contribution calendar 获取近似总提交数。"""
    # 使用 GraphQL 获取 contribution 总数(包含 commits/issues/PRs)
    # 这里简化: 使用 events 分页统计 PushEvent 中的 commit 数
    total = 0
    for page in range(1, 11):  # 最多查 10 页
        events = api(
            f"https://api.github.com/users/{GITHUB_USERNAME}/events/public"
            f"?per_page=100&page={page}"
        )
        if not events:
            break
        for e in events:
            if e["type"] == "PushEvent":
                total += len(e["payload"].get("commits", []))
    return total


def main():
    print(f"Start: {datetime.now(timezone.utc).isoformat()}")
    print(f"User: {GITHUB_USERNAME}")

    if not README_PATH.exists():
        print(f"ERROR: {README_PATH} not found")
        sys.exit(1)

    readme = README_PATH.read_text(encoding="utf-8")

    # ── 获取数据 ──────────────────────────────────────
    print("Fetching stats...")
    try:
        stats = get_stats()
        commits = get_total_commits()
        print(f"  Stars: {stats['stars']}  Commits: ~{commits}  Repos: {stats['public_repos']}")
    except Exception as e:
        print(f"ERROR fetching stats: {e}")
        sys.exit(1)

    # ── 生成新徽章行 ───────────────────────────────────
    new_badges = (
        f"![Stars](https://img.shields.io/badge/Stars-{stats['stars']}-58a6ff"
        f"?style=flat-square&logo=github&logoColor=white)\n"
        f"&nbsp;\n"
        f"![Commits](https://img.shields.io/badge/Commits-{commits}-58a6ff"
        f"?style=flat-square&logo=git&logoColor=white)\n"
        f"&nbsp;\n"
        f"![Repos](https://img.shields.io/badge/Repos-{stats['public_repos']}-58a6ff"
        f"?style=flat-square&logo=github&logoColor=white)"
    )

    # ── 替换标记区间 ──────────────────────────────────
    start_tag = "<!-- START_SECTION:github-stats -->"
    end_tag = "<!-- END_SECTION:github-stats -->"

    pattern = re.compile(
        re.escape(start_tag) + r".*?" + re.escape(end_tag),
        re.DOTALL,
    )

    if pattern.search(readme):
        replacement = f"{start_tag}\n{new_badges}\n{end_tag}"
        readme = pattern.sub(replacement, readme)
        print("  Stats section replaced.")
    else:
        print(f"  WARNING: {start_tag} marker not found, appending to end.")
        readme = readme.rstrip() + f"\n\n{start_tag}\n{new_badges}\n{end_tag}\n"

    # ── 更新时间戳 ──────────────────────────────────
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    update_line = (
        f"\n\n<sub>Auto-updated {now_str} · "
        f"[Workflow](https://github.com/{GITHUB_USERNAME}/{GITHUB_USERNAME}/actions)</sub>\n"
    )
    readme = re.sub(r"<sub>Auto-updated.*?</sub>\n?", "", readme)
    readme = readme.rstrip() + update_line

    README_PATH.write_text(readme, encoding="utf-8")
    print("Done!")


if __name__ == "__main__":
    main()
