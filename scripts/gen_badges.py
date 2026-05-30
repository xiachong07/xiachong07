"""
生成渐变动画 SVG 技能徽章
每个徽章: 渐变背景 + CSS脉冲动画 + hover放大
用法: python scripts/gen_badges.py
"""

import os

OUT_DIR = "assets/badges"

# 技能定义: (名称, 图标SVG路径, 路径填充色)
SKILLS = [
    # 编程语言
    ("Python", "M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z", "#3776AB"),
    ("C++", "M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z", "#00599C"),
    ("LaTeX", "M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z", "#008080"),
    # ML框架
    ("PyTorch", "M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z", "#EE4C2C"),
    ("Scikit-learn", "M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z", "#F7931E"),
    # 数据处理
    ("Pandas", "M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z", "#150458"),
    ("NumPy", "M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z", "#013243"),
    ("Matplotlib", "M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z", "#11557C"),
    ("Librosa", "M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z", "#3E4A89"),
    # 工具
    ("Git", "M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z", "#F05032"),
    ("VS Code", "M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z", "#007ACC"),
    ("Jupyter", "M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z", "#F37626"),
]


def make_badge(name: str, color: str) -> str:
    """生成单个动画SVG徽章。"""
    # 计算文本宽度近似值
    width = max(90, len(name) * 10 + 40)

    return f"""<!--
  技能徽章: {name}
  渐变: #7928ca → #ff0080
  动画: 2s脉冲 + hover放大
-->
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="28" viewBox="0 0 {width} 28">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#7928ca"/>
      <stop offset="100%" style="stop-color:#ff0080"/>
    </linearGradient>
    <style>
      .badge-bg {{
        animation: pulse 2s ease-in-out infinite;
      }}
      .badge-bg:hover {{
        transform: scale(1.1);
        transform-origin: {width/2}px 14px;
        transition: transform 0.2s ease;
      }}
      @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.75; }}
      }}
    </style>
  </defs>
  <rect class="badge-bg" width="{width}" height="28" rx="6" fill="url(#g)"/>
  <text x="{width/2}" y="19" text-anchor="middle" fill="#ffffff"
        font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"
        font-size="12" font-weight="600">{name}</text>
</svg>"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    for name, _, color in SKILLS:
        svg = make_badge(name, color)
        fname = name.lower().replace(" ", "-").replace("++", "pp")
        path = os.path.join(OUT_DIR, f"{fname}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"  {path}")

    print(f"\nGenerated {len(SKILLS)} badges in {OUT_DIR}/")


if __name__ == "__main__":
    main()
