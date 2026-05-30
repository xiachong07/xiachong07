"""
╔══════════════════════════════════════════════════════════╗
║  GitHub Profile README · 自动更新脚本                     ║
║  功能：                                                   ║
║    1. 最近 5 条 GitHub 提交记录                            ║
║    2. Kaggle 竞赛排名与成绩                                ║
║    3. 总 Star 数 + 提交数                                 ║
║  通过 HTML 注释标记定位 README 中的可更新区域                ║
╚══════════════════════════════════════════════════════════╝

使用方法：
  - 将本脚本放入 xiachong07/xiachong07 仓库的 scripts/ 目录
  - 在仓库 Settings → Secrets and variables → Actions → Variables
    中添加 KAGGLE_USERNAME（你的 Kaggle 用户名）
  - GITHUB_TOKEN 由 Actions 自动注入，无需手动配置
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

# ═══════════════════════════════════════════════════════════
#  配置区（按需修改以下变量）
# ═══════════════════════════════════════════════════════════

GITHUB_USERNAME = "xiachong07"
README_PATH = Path(__file__).resolve().parent.parent / "README.md"
COMMIT_COUNT = 5  # 展示最近 N 条提交

# 从环境变量读取 Token 和 Kaggle 用户名
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME", "")

# GitHub API 请求头
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Readme-Auto-Updater/1.0",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


# ═══════════════════════════════════════════════════════════
#  数据获取函数
# ═══════════════════════════════════════════════════════════

def fetch_recent_commits(username: str, count: int) -> list[dict]:
    """通过 GitHub Events API 获取用户最近 N 条 Push 提交。"""
    url = f"https://api.github.com/users/{username}/events/public?per_page=100"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    commits = []
    for event in resp.json():
        if event["type"] != "PushEvent":
            continue
        for c in event["payload"].get("commits", []):
            if len(commits) >= count:
                break
            commits.append({
                "repo": event["repo"]["name"],
                "message": c.get("message", "").split("\n")[0][:72],
                "url": f"https://github.com/{event['repo']['name']}/commit/{c['sha'][:8]}",
                "date": event["created_at"],
            })
        if len(commits) >= count:
            break
    return commits


def fetch_total_stats(username: str) -> dict:
    """获取用户总 Star 数、公开仓库数、关注者数。"""
    url = f"https://api.github.com/users/{username}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    user = resp.json()

    # 遍历所有仓库累加 Star
    stars = 0
    page = 1
    while True:
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}"
        r = requests.get(repos_url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        repos = r.json()
        if not repos:
            break
        stars += sum(repo.get("stargazers_count", 0) for repo in repos)
        page += 1

    return {
        "stars": stars,
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
    }


def fetch_commit_count(username: str) -> int:
    """通过搜索 API 统计用户总提交数（近似值）。"""
    url = "https://api.github.com/search/commits"
    params = {"q": f"author:{username}", "per_page": 1}
    headers = {**HEADERS, "Accept": "application/vnd.github.cloak-preview+json"}
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    if resp.status_code == 200:
        return resp.json().get("total_count", 0)
    return 0


def fetch_kaggle_profile(username: str) -> dict | None:
    """
    尝试抓取 Kaggle 公开个人页面获取排名摘要。

    Kaggle 无官方公开排名 API，这里使用两种方式备选：
      1. 尝试 kagglehub 库（如果已安装）
      2. 解析公开个人页面 HTML

    返回 dict: { "rank": "...", "medals": "...", "competitions": "..." }
    失败返回 None。
    """
    if not username:
        return None

    # 方式一：通过 kagglehub（推荐，但需预装）
    try:
        import kagglehub  # type: ignore
        # kagglehub 目前不直接提供排名查询，
        # 这里保留占位，待未来 API 开放后接入
    except ImportError:
        pass

    # 方式二：解析公开页面
    try:
        url = f"https://www.kaggle.com/{username}"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if resp.status_code != 200:
            return None

        html = resp.text

        # 提取排名片段（页面结构可能变化，需定期维护选择器）
        # Kaggle 页面在 <script> 中以 JSON 嵌入用户数据
        pattern = r'window\.__INITIAL_STATE__\s*=\s*({.+?});\s*</script>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            # 路径取决于 Kaggle 前端状态结构，这里是常见路径
            try:
                user_info = (
                    data.get("user", {})
                    .get("userProfile", {})
                )
                return {
                    "rank": user_info.get("rank", "N/A"),
                    "medals": str(user_info.get("medalsCount", 0)),
                    "competitions": str(user_info.get("competitionsCount", 0)),
                }
            except Exception:
                pass
    except Exception:
        pass

    return None


# ═══════════════════════════════════════════════════════════
#  Markdown 生成函数
# ═══════════════════════════════════════════════════════════

def build_commits_md(commits: list[dict]) -> str:
    """将提交列表渲染为 Markdown 表格。"""
    if not commits:
        return "> 暂无近期提交记录。\n"

    lines = [
        "| 时间 | 仓库 | 提交信息 |",
        "| :--- | :--- | :--- |",
    ]
    for c in commits:
        dt = datetime.fromisoformat(c["date"].replace("Z", "+00:00"))
        time_str = dt.strftime("%m-%d %H:%M")
        repo_short = c["repo"].split("/", 1)[-1] if "/" in c["repo"] else c["repo"]
        lines.append(
            f"| {time_str} "
            f"| [{repo_short}](https://github.com/{c['repo']}) "
            f"| [{c['message']}]({c['url']}) |"
        )
    return "\n".join(lines) + "\n"


def build_stats_md(stats: dict, commit_count: int) -> str:
    """将统计数据渲染为 shields.io 徽章行。"""
    return (
        f"![Stars](https://img.shields.io/badge/Total_Stars-{stats['stars']}-58a6ff"
        f"?style=flat-square&logo=github&logoColor=white)\n"
        f"&nbsp;\n"
        f"![Commits](https://img.shields.io/badge/Total_Commits-{commit_count}-58a6ff"
        f"?style=flat-square&logo=git&logoColor=white)\n"
        f"&nbsp;\n"
        f"![Repos](https://img.shields.io/badge/Public_Repos-{stats['public_repos']}-58a6ff"
        f"?style=flat-square&logo=github&logoColor=white)\n"
        f"&nbsp;\n"
        f"![Followers](https://img.shields.io/badge/Followers-{stats['followers']}-58a6ff"
        f"?style=flat-square&logo=github&logoColor=white)\n"
    )


def build_kaggle_md(kaggle: dict | None) -> str:
    """将 Kaggle 数据渲染为 Markdown。"""
    if not kaggle:
        return (
            "> ⚠️ 未获取到 Kaggle 数据。请检查仓库 Actions Variables 中"
            "的 `KAGGLE_USERNAME` 是否正确设置。\n"
        )
    lines = [
        "| 指标 | 数据 |",
        "| :--- | :--- |",
    ]
    labels = {
        "rank": "🏆 排名",
        "medals": "🥇 奖牌数",
        "competitions": "📊 参赛次数",
    }
    for key, label in labels.items():
        if key in kaggle:
            lines.append(f"| {label} | {kaggle[key]} |")
    return "\n".join(lines) + "\n"


# ═══════════════════════════════════════════════════════════
#  核心：替换 README 中的标记区间
# ═══════════════════════════════════════════════════════════

def replace_section(readme: str, marker: str, new_content: str) -> str:
    """
    在 README 中查找 `<!-- START_SECTION:<marker> -->` 和
    `<!-- END_SECTION:<marker> -->` 之间的内容并替换。

    如果标记不存在，追加到文件末尾并附警告注释。
    """
    start_tag = f"<!-- START_SECTION:{marker} -->"
    end_tag = f"<!-- END_SECTION:{marker} -->"

    pattern = re.compile(
        re.escape(start_tag) + r".*?" + re.escape(end_tag),
        re.DOTALL,
    )

    replacement = f"{start_tag}\n{new_content}\n{end_tag}"

    if pattern.search(readme):
        return pattern.sub(replacement, readme)

    # 标记不存在时，追加到末尾
    print(f"  ⚠ 未找到 {{<!-- START_SECTION:{marker} -->}} 标记，追加到 README 末尾。")
    return readme.rstrip() + f"\n\n{replacement}\n"


# ═══════════════════════════════════════════════════════════
#  主流程
# ═══════════════════════════════════════════════════════════

def main() -> None:
    print(f"🕐 开始时间: {datetime.now(timezone.utc).isoformat()}")
    print(f"👤 用户: {GITHUB_USERNAME}")
    print(f"🎯 Kaggle 用户: {KAGGLE_USERNAME or '(未配置)'}")

    # 检查 README 是否存在
    if not README_PATH.exists():
        print(f"❌ 未找到 {README_PATH}，请确保脚本位于仓库 scripts/ 目录下。")
        sys.exit(1)

    readme = README_PATH.read_text(encoding="utf-8")

    # ── 1. 更新最近提交 ──────────────────────────────────
    print("\n📋 获取最近提交...")
    try:
        commits = fetch_recent_commits(GITHUB_USERNAME, COMMIT_COUNT)
        commits_md = build_commits_md(commits)
        readme = replace_section(readme, "recent-commits", commits_md)
        print(f"  ✅ 已获取 {len(commits)} 条提交。")
    except Exception as e:
        print(f"  ❌ 获取提交失败: {e}")

    # ── 2. 更新统计数字 ──────────────────────────────────
    print("\n📊 获取统计数据...")
    try:
        stats = fetch_total_stats(GITHUB_USERNAME)
        commit_count = fetch_commit_count(GITHUB_USERNAME)
        stats_md = build_stats_md(stats, commit_count)
        readme = replace_section(readme, "github-stats", stats_md)
        print(f"  ✅ Star: {stats['stars']} | 提交: {commit_count} | 仓库: {stats['public_repos']}")
    except Exception as e:
        print(f"  ❌ 获取统计失败: {e}")

    # ── 3. 更新 Kaggle 数据 ──────────────────────────────
    print("\n🎯 获取 Kaggle 数据...")
    try:
        kaggle = fetch_kaggle_profile(KAGGLE_USERNAME)
        kaggle_md = build_kaggle_md(kaggle)
        readme = replace_section(readme, "kaggle-stats", kaggle_md)
        print(f"  ✅ Kaggle 数据已更新。")
    except Exception as e:
        print(f"  ❌ 获取 Kaggle 数据失败: {e}")

    # ── 4. 追加更新时间戳 ────────────────────────────────
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    update_line = f"\n\n<sub>🤖 自动更新于 {now_str} · [Workflow](https://github.com/{GITHUB_USERNAME}/{GITHUB_USERNAME}/actions)</sub>\n"
    # 移除旧时间戳
    readme = re.sub(
        r"<sub>🤖 自动更新于.*?</sub>\n?",
        "",
        readme,
    )
    readme = readme.rstrip() + update_line

    # ── 5. 写回 README ───────────────────────────────────
    README_PATH.write_text(readme, encoding="utf-8")
    print(f"\n🎉 README 更新完成！")


if __name__ == "__main__":
    main()
