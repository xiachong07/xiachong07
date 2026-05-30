"""
╔══════════════════════════════════════════════════════════╗
║  随机名言模块 · GitHub Actions 每日更新                     ║
║  修改 QUOTES 列表即可增删名言                              ║
╚══════════════════════════════════════════════════════════╝
"""

import random

QUOTES = [
    # ── 数学 ──────────────────────────────────────────
    {
        "text": "The essence of mathematics lies in its freedom.",
        "author": "Georg Cantor",
    },
    {
        "text": "Mathematics is the art of giving the same name to different things.",
        "author": "Henri Poincaré",
    },
    {
        "text": "Pure mathematics is, in its way, the poetry of logical ideas.",
        "author": "Albert Einstein",
    },
    {
        "text": "Mathematics is the most beautiful and most powerful creation of the human spirit.",
        "author": "Stefan Banach",
    },
    {
        "text": "In mathematics, the art of asking questions is more valuable than solving problems.",
        "author": "Georg Cantor",
    },
    # ── 编程 / 计算机科学 ─────────────────────────────
    {
        "text": "Talk is cheap. Show me the code.",
        "author": "Linus Torvalds",
    },
    {
        "text": "First, solve the problem. Then, write the code.",
        "author": "John Johnson",
    },
    {
        "text": "Any fool can write code that a computer can understand. Good programmers write code that humans can understand.",
        "author": "Martin Fowler",
    },
    {
        "text": "The best way to predict the future is to invent it.",
        "author": "Alan Kay",
    },
    {
        "text": "Measuring programming progress by lines of code is like measuring aircraft building progress by weight.",
        "author": "Bill Gates",
    },
    # ── 机器学习 / 数据科学 ────────────────────────────
    {
        "text": "The best way to learn data science is to do data science.",
        "author": "Jeremy Howard",
    },
    {
        "text": "All models are wrong, but some are useful.",
        "author": "George Box",
    },
]


def get_random_quote() -> dict:
    """从名言库中随机选取一条。"""
    return random.choice(QUOTES)


def format_quote(quote: dict) -> str:
    """将名言格式化为 Markdown 引用样式。"""
    return (
        f"> *\"{quote['text']}\"*\n"
        f">\n"
        f'> <div align="right">— {quote["author"]}</div>\n'
    )


if __name__ == "__main__":
    quote = get_random_quote()
    print(format_quote(quote))
