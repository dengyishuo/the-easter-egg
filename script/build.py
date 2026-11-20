#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《彩蛋：影响世界的顶级商人》构建脚本
把 draft/*.md 拼成一本单文件 HTML（可打印）与一份合并 Markdown。

用法： python3 script/build.py
"""

import os
import re
import html
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRAFT = os.path.join(ROOT, "draft")
OUT = os.path.join(ROOT, "output")

BOOK_TITLE = "彩蛋"
BOOK_SUB = "影响世界的顶级商人"
BOOK_EN = "The Easter Egg"
BOOK_EN_SUB = "The Merchants Who Changed the World"
AUTHOR = "揖光尘"

# 全书按时代先后编排。缺文件的章节会被跳过，补上 draft/*.md 即自动入书。
ORDER = [
    ("00-preface.md", None),
    ("00-intro.md", None),
    ("00-theory.md", None),
    # 第一部分　商人从哪里来
    ("00-part1-intro.md", "第一部分　商人从哪里来"),
    ("01-merchant.md", "第一部分　商人从哪里来"),
    ("02-warehouse.md", "第一部分　商人从哪里来"),
    ("03-trust.md", "第一部分　商人从哪里来"),
    # 第二部分　蒸汽与钢铁
    ("04-steam.md", "第二部分　蒸汽与钢铁"),
    ("04b-rail.md", "第二部分　蒸汽与钢铁"),
    # 第三部分　电与信号
    ("06-telegraph.md", "第三部分　电与信号"),
    ("06b-telephone.md", "第三部分　电与信号"),
    ("06c-electric.md", "第三部分　电与信号"),
    # 第四部分　引擎与翅膀
    ("05-ford.md", "第四部分　引擎与翅膀"),
    ("09-flight.md", "第四部分　引擎与翅膀"),
    # 第五部分　零售
    ("06-walmart.md", "第五部分　零售"),
    # 第六部分　计算的普及
    ("07-ibm.md", "第六部分　计算的普及"),
    ("08-jobs.md", "第六部分　计算的普及"),
    # 第七部分　连接一切
    ("16-portal.md", "第七部分　连接一切"),
    ("17-email.md", "第七部分　连接一切"),
    ("14-search.md", "第七部分　连接一切"),
    ("10-commerce.md", "第七部分　连接一切"),
    # 第八部分　重连人与人
    ("11-social.md", "第八部分　重连人与人"),
    # 第九部分　机器替人做事
    ("12-ev.md", "第九部分　机器替人做事"),
    ("12b-battery.md", "第九部分　机器替人做事"),
    ("13-robot.md", "第九部分　机器替人做事"),
    ("15-ai.md", "第九部分　机器替人做事"),
    # 反思章（不编号，与结语并列）
    ("16b-wealth.md", None),
    # 收尾
    ("97-closing.md", None),
    ("98-epilogue.md", None),
    ("A-timeline.md", None),
    ("B-references.md", None),
]

PART_SUB = {
    "第一部分　商人从哪里来": "商人为什么出现，有什么意义——货郎、仓与招牌",
    "第二部分　蒸汽与钢铁": "蒸汽机、轮船、火车——把力气装进机器",
    "第三部分　电与信号": "电报、电话、电灯——让信息和光跑起来",
    "第四部分　引擎与翅膀": "汽车与飞机——速度成为一门生意",
    "第五部分　零售": "把商品送到每个人手上",
    "第六部分　计算的普及": "从机房到口袋——计算能力进入生活",
    "第七部分　连接一切": "门户、邮箱、搜索、电商——互联网如何把人聚起来",
    "第八部分　重连人与人": "社交网络——把人与人的距离压到零",
    "第九部分　机器替人做事": "电动汽车、电池、机器人、人工智能——从替你出力，到替你思考",
}


# ---------------- Markdown 转换 ----------------

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    return t


def md_to_html(text):
    lines = text.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].rstrip()
        s = line.strip()

        if not s:
            i += 1
            continue

        # 表格
        if s.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            cells = []
            for r in rows:
                if re.match(r"^\|[\s:\-\|]+\|$", r):
                    continue
                parts = [c.strip() for c in r.strip("|").split("|")]
                cells.append(parts)
            if cells:
                head, body = cells[0], cells[1:]
                out.append("<div class=\"table-wrap\"><table>")
                out.append("<thead><tr>" + "".join(
                    f"<th>{inline(c)}</th>" for c in head) + "</tr></thead>")
                out.append("<tbody>")
                for row in body:
                    out.append("<tr>" + "".join(
                        f"<td>{inline(c)}</td>" for c in row) + "</tr>")
                out.append("</tbody></table></div>")
            continue

        # 分隔线
        if re.match(r"^---+$", s):
            out.append("<hr />")
            i += 1
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            lvl = len(m.group(1))
            txt = m.group(2)
            anchor = "h" + str(abs(hash(txt)) % 1000000)
            out.append(f"<h{lvl} id=\"{anchor}\">{inline(txt)}</h{lvl}>")
            i += 1
            continue

        # 引用
        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            paras = [p for p in buf if p]
            inner = "".join(f"<p>{inline(p)}</p>" for p in paras)
            out.append(f"<blockquote>{inner}</blockquote>")
            continue

        # 有序列表
        if re.match(r"^\d+\.\s+", s):
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue

        # 无序列表
        if re.match(r"^-\s+", s):
            items = []
            while i < n and re.match(r"^-\s+", lines[i].strip()):
                items.append(re.sub(r"^-\s+", "", lines[i].strip()))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue

        # 段落
        buf = []
        while i < n:
            s2 = lines[i].strip()
            if not s2:
                break
            if s2.startswith("|") or s2.startswith(">") or re.match(r"^#{1,6}\s", s2) \
                    or re.match(r"^\d+\.\s+", s2) or re.match(r"^-\s+", s2) or re.match(r"^---+$", s2):
                break
            buf.append(s2)
            i += 1
        out.append("<p>" + inline("".join(buf)) + "</p>")

    return "\n".join(out)


def split_sections(path):
    """按一级标题切分，返回 [(title, html)]"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    chunks = re.split(r"^#\s+", text, flags=re.M)
    secs = []
    for ch in chunks:
        ch = ch.strip()
        if not ch:
            continue
        first, _, rest = ch.partition("\n")
        secs.append((first.strip(), md_to_html(rest)))
    return secs


def split_sections_md(path):
    """按一级标题切分，返回 [(title, 原始 Markdown 正文)]"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    chunks = re.split(r"^#\s+", text, flags=re.M)
    secs = []
    for ch in chunks:
        ch = ch.strip()
        if not ch:
            continue
        first, _, rest = ch.partition("\n")
        secs.append((first.strip(), rest.strip()))
    return secs


# ---------------- 构建 ----------------

def build():
    os.makedirs(OUT, exist_ok=True)

    docs = []   # (part, title, html)
    for fname, part in ORDER:
        p = os.path.join(DRAFT, fname)
        if not os.path.exists(p):
            print("缺少文件:", fname)
            continue
        for title, body in split_sections(p):
            disp = re.sub(r"^第[一二三四五六七八九十]+章[\s\u3000]*", "", title) if part else title
            docs.append({"part": part, "title": title, "disp": disp, "html": body})

    # 目录
    toc_items = []
    sidebar_items = []
    chapters = []
    last_part = None
    seq = 0
    for idx, d in enumerate(docs):
        if d["part"] and d["part"] != last_part:
            last_part = d["part"]
            toc_items.append(
                f'<li class="toc-part">{html.escape(last_part)}</li>')
            short = re.sub(r"^第[一二三四五六七八九十]+部分[\s\u3000]*", "", last_part)
            sidebar_items.append(
                f'<div class="sb-part">{html.escape(short)}</div>')
        num = ""
        if d["part"]:
            seq += 1
            num = f'<span class="toc-num">{seq:02d}</span>'
        toc_items.append(
            f'<li class="toc-chap"><a href="#ch{idx}">{num}'
            f'<span>{html.escape(d["disp"])}</span></a></li>')
        sidebar_items.append(
            f'<a class="sb-link" href="#ch{idx}" data-idx="{idx}">'
            f'{num}<span>{html.escape(d["disp"])}</span></a>')

    # 正文
    last_part = None
    seq = 0
    for idx, d in enumerate(docs):
        if d["part"] and d["part"] != last_part:
            last_part = d["part"]
            sub = PART_SUB.get(last_part, "")
            chapters.append(
                f'<section class="part-page">'
                f'<div class="part-inner"><div class="part-rule"></div>'
                f'<h2 class="part-name">{html.escape(last_part)}</h2>'
                f'<p class="part-sub">{html.escape(sub)}</p>'
                f'<div class="part-rule"></div></div></section>')
        kicker = ""
        if d["part"]:
            seq += 1
            kicker = f'<div class="chap-kicker">{html.escape(d["part"])}</div>'
        chapters.append(
            f'<article class="chapter" id="ch{idx}">'
            f'<header class="chap-head">{kicker}'
            f'<h1>{html.escape(d["disp"])}</h1></header>'
            f'<div class="chap-body">{d["html"]}</div></article>')

    today = datetime.date.today().isoformat()
    total_chars = sum(len(re.sub(r"<[^>]+>", "", d["html"])) for d in docs)

    tmpl = TEMPLATE
    out_html = (tmpl
                .replace("__TOC__", "\n".join(toc_items))
                .replace("__SIDEBAR__", "\n".join(sidebar_items))
                .replace("__BODY__", "\n".join(chapters))
                .replace("__DATE__", today)
                .replace("__CHARS__", f"{total_chars // 1000}"))

    out_path = os.path.join(OUT, "彩蛋-影响世界的顶级商人.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_html)

    # 合并 Markdown（用原始 Markdown 正文，不混入 HTML）
    md_parts = [f"# {BOOK_TITLE}：{BOOK_SUB}\n\n**{BOOK_EN}: {BOOK_EN_SUB}**\n\n"
                f"> 作者：{AUTHOR}\n\n---\n"]
    last_part = None
    seq = 0
    for fname, part in ORDER:
        p = os.path.join(DRAFT, fname)
        if not os.path.exists(p):
            continue
        if part and part != last_part:
            last_part = part
            md_parts.append(f"\n---\n\n# {part}\n")
        for title, raw in split_sections_md(p):
            disp = re.sub(r"^第[一二三四五六七八九十]+章[\s\u3000]*", "", title) if part else title
            # 章标题统一用 ##，正文内的小节整体降一级，避免层级冲突
            raw = re.sub(r"^(#{2,5})[ \t]", lambda m: "#" * (len(m.group(1)) + 1) + " ", raw, flags=re.M)
            if part:
                seq += 1
                md_parts.append(f"\n## {seq:02d}　{disp}\n")
            else:
                md_parts.append(f"\n## {disp}\n")
            md_parts.append(raw + "\n")
    with open(os.path.join(OUT, "彩蛋-影响世界的顶级商人.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md_parts))

    print(f"生成：{out_path}")
    print(f"章节数：{len(docs)}　正文约 {total_chars // 1000} 千字")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="paper">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>彩蛋：影响世界的顶级商人</title>
<style>
:root{
  --bg:#f5f2ea; --paper:#fffdf8; --ink:#1c1a17; --ink-2:#4a453d; --ink-3:#8a8175;
  --rule:#ded5c4; --accent:#8a5a1f; --accent-soft:#f3ead7;
  --sbw:290px;
  --serif:"Songti SC","Noto Serif SC","Source Han Serif SC",Georgia,"Times New Roman",serif;
  --sans:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",-apple-system,sans-serif;
}
html[data-theme="night"]{
  --bg:#14161a; --paper:#1b1e23; --ink:#e8e4dc; --ink-2:#b6b0a5; --ink-3:#7d766b;
  --rule:#33373e; --accent:#d9a860; --accent-soft:#2b2419;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:var(--serif); font-size:17px; line-height:1.95;
  -webkit-font-smoothing:antialiased;
  padding-left:var(--sbw);
}
#bar{position:fixed;top:0;left:0;height:3px;background:var(--accent);width:0;z-index:99}

/* 左侧目录栏 */
#sidebar{
  position:fixed;top:0;left:0;bottom:0;width:var(--sbw);z-index:80;
  background:var(--paper);border-right:1px solid var(--rule);
  display:flex;flex-direction:column;
}
.sb-head{
  padding:26px 22px 18px;border-bottom:1px solid var(--rule);flex:none
}
.sb-title{font-size:19px;letter-spacing:.14em;margin:0;font-weight:400}
.sb-sub{font-family:var(--sans);font-size:10px;letter-spacing:.2em;color:var(--ink-3);margin:.5em 0 0}
.sb-nav{overflow-y:auto;flex:1;padding:14px 0 30px;scrollbar-width:thin}
.sb-part{
  font-family:var(--sans);font-size:10px;letter-spacing:.18em;color:var(--accent);
  padding:16px 22px 6px;line-height:1.5
}
.sb-link{
  display:flex;gap:10px;align-items:baseline;text-decoration:none;color:var(--ink-2);
  padding:5px 22px;font-size:12.5px;line-height:1.6;border-left:2px solid transparent;
  transition:background .18s,color .18s,border-color .18s
}
.sb-link .toc-num{font-size:10px;color:var(--ink-3);min-width:20px}
.sb-link:hover{color:var(--accent);background:var(--accent-soft)}
.sb-link.active{color:var(--accent);border-left-color:var(--accent);background:var(--accent-soft);font-weight:600}
#sb-toggle{
  display:none;position:fixed;top:14px;left:14px;z-index:90;width:38px;height:38px;
  border-radius:50%;border:1px solid var(--rule);background:var(--paper);color:var(--ink-2);
  cursor:pointer;font-size:15px;font-family:var(--sans);align-items:center;justify-content:center;
  box-shadow:0 2px 10px rgba(0,0,0,.06)
}

/* 封面 */
.cover{
  min-height:100vh; display:flex; flex-direction:column; justify-content:center;
  align-items:center; padding:8vh 8vw; position:relative; text-align:center;
  background:var(--paper);
}
.cover-mark{font-family:var(--sans);font-size:11px;letter-spacing:.42em;color:var(--ink-3);margin-bottom:5vh}
.cover h1{
  font-size:clamp(60px,13vw,132px); margin:0; letter-spacing:.16em;
  font-weight:400; line-height:1.1; text-indent:.16em;
}
.cover .cn-sub{
  font-size:clamp(16px,2.1vw,25px); letter-spacing:.24em; color:var(--ink-2);
  margin:3.2vh 0 0; text-indent:.24em;
}
.cover .rule{width:64px;height:1px;background:var(--accent);margin:5vh 0}
.cover .en{font-family:var(--sans);font-size:12px;letter-spacing:.28em;color:var(--ink-3);line-height:2.2;max-width:min(640px,84vw)}
.cover svg{width:min(560px,84vw);margin:7vh 0 0;overflow:visible}
.cover .author{margin:2vh 0 0;font-family:var(--sans);font-size:13px;letter-spacing:.3em;color:var(--ink-2)}

/* 目录 */
.toc-wrap{background:var(--paper);padding:14vh 8vw 16vh;border-top:1px solid var(--rule)}
.toc-inner{max-width:760px;margin:0 auto}
.toc-wrap h2{
  font-size:13px;font-family:var(--sans);letter-spacing:.34em;color:var(--ink-3);
  font-weight:400;margin:0 0 6vh;text-align:center
}
.toc{list-style:none;padding:0;margin:0}
.toc-part{
  font-family:var(--sans);font-size:12px;letter-spacing:.24em;color:var(--accent);
  margin:4.4vh 0 1.6vh;padding-bottom:.9vh;border-bottom:1px solid var(--rule)
}
.toc-part:first-child{margin-top:0}
.toc-chap a{
  display:flex;gap:14px;align-items:baseline;text-decoration:none;color:var(--ink);
  padding:.85vh 0;border-bottom:1px dotted transparent;transition:.2s
}
.toc-chap a:hover{color:var(--accent);border-bottom-color:var(--rule)}
.toc-num{font-family:var(--sans);font-size:11px;color:var(--ink-3);min-width:26px;letter-spacing:.1em}
.toc-chap span{font-size:16.5px}

/* 部扉页 */
.part-page{
  min-height:88vh;display:flex;align-items:center;justify-content:center;
  background:var(--paper);padding:10vh 8vw;border-top:1px solid var(--rule)
}
.part-inner{text-align:center;max-width:640px}
.part-name{
  font-size:clamp(26px,4vw,40px);font-weight:400;letter-spacing:.2em;
  margin:4vh 0;color:var(--ink);text-indent:.2em
}
.part-sub{font-size:15px;color:var(--ink-3);letter-spacing:.16em;margin:0}
.part-rule{width:40px;height:1px;background:var(--rule);margin:0 auto}

/* 章节 */
.chapter{
  background:var(--paper);padding:12vh 8vw 14vh;
  border-top:1px solid var(--rule);max-width:100%
}
.chap-head{max-width:700px;margin:0 auto 7vh;text-align:left}
.chap-kicker{
  font-family:var(--sans);font-size:11px;letter-spacing:.34em;color:var(--accent);margin-bottom:2.4vh
}
.chap-head h1{
  font-size:clamp(26px,3.6vw,38px);font-weight:400;line-height:1.5;
  margin:0;letter-spacing:.04em
}
.chap-body{max-width:700px;margin:0 auto}
.chap-body p{margin:0 0 1.55em;text-align:justify;text-justify:inter-ideograph}

.chap-body h2{
  font-size:20px;font-weight:400;letter-spacing:.1em;margin:3.4em 0 1.2em;
  padding-left:14px;border-left:2px solid var(--accent);line-height:1.6
}
.chap-body h3{font-size:17px;font-weight:600;margin:2.4em 0 .9em;letter-spacing:.04em}

.chap-body blockquote{
  margin:2.4em 0;padding:1.4em 1.8em;background:var(--accent-soft);
  border-left:2px solid var(--accent);color:var(--ink);
  font-size:16px;border-radius:2px
}
.chap-body blockquote p{margin:0 0 .6em}
.chap-body blockquote p:last-child{margin-bottom:0}

.chap-body ul,.chap-body ol{margin:0 0 1.6em;padding-left:1.5em}
.chap-body li{margin:.4em 0;text-align:justify}

.chap-body hr{border:0;height:1px;background:var(--rule);margin:3.2em auto;width:38%}

.chap-body strong{font-weight:700;color:var(--ink)}
.chap-body code{
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.86em;
  background:var(--accent-soft);padding:.1em .4em;border-radius:2px
}

.table-wrap{overflow-x:auto;margin:2.2em 0 2.6em;border:1px solid var(--rule);border-radius:2px}
table{border-collapse:collapse;width:100%;font-size:13.5px;font-family:var(--sans);line-height:1.7}
th,td{padding:8px 11px;text-align:left;border-bottom:1px solid var(--rule);vertical-align:top}
th{background:var(--accent-soft);font-weight:600;color:var(--ink);white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:rgba(138,90,31,.05)}

.colophon{
  background:var(--paper);padding:16vh 8vw;text-align:center;border-top:1px solid var(--rule)
}
.colophon p{font-family:var(--sans);font-size:11px;letter-spacing:.26em;color:var(--ink-3);line-height:2.6;margin:0}

/* 工具 */
#tools{position:fixed;right:20px;bottom:20px;display:flex;flex-direction:column;gap:8px;z-index:60}
#tools button{
  width:38px;height:38px;border-radius:50%;border:1px solid var(--rule);
  background:var(--paper);color:var(--ink-2);cursor:pointer;font-size:13px;
  font-family:var(--sans);display:flex;align-items:center;justify-content:center;
  box-shadow:0 2px 10px rgba(0,0,0,.06);transition:.2s
}
#tools button:hover{color:var(--accent);border-color:var(--accent)}
@media(max-width:900px){
  :root{--sbw:0px}
  #sidebar{transform:translateX(-100%);transition:transform .25s;width:min(300px,82vw)}
  body.sb-open #sidebar{transform:translateX(0)}
  #sb-toggle{display:flex}
  .cover{padding-left:8vw;padding-right:8vw}
}
@media(max-width:640px){
  body{font-size:16px}
  .cover .en{font-size:10.5px;letter-spacing:.16em;line-height:2.4}
  .chapter,.toc-wrap{padding-left:6vw;padding-right:6vw}
  .chap-body p{text-align:left}
}

@media print{
  :root{--bg:#fff;--paper:#fff;--sbw:0px}
  #sidebar,#sb-toggle,#tools,#bar{display:none !important}
  body{font-size:11.5pt;line-height:1.85}
  .cover{min-height:100vh;page-break-after:always;border:0}
  .toc-wrap{page-break-after:always;border-top:0}
  .part-page{page-break-before:always;min-height:auto;height:100vh;border:0}
  .chapter{page-break-before:always;border-top:0;padding:0 0 2em}
  .chap-head h1{font-size:20pt}
  .chap-body h2{font-size:13pt}
  .chap-body blockquote{background:#faf6ef}
  table{font-size:8.5pt}
  .colophon{page-break-before:always}
  @page{margin:18mm 16mm}
}
</style>
</head>
<body>
<div id="bar"></div>

<button id="sb-toggle" title="目录">☰</button>
<aside id="sidebar">
  <div class="sb-head">
    <p class="sb-title">彩蛋</p>
    <p class="sb-sub">影响世界的顶级商人 · 目录</p>
  </div>
  <nav class="sb-nav">
__SIDEBAR__
  </nav>
</aside>

<section class="cover">
  <div class="cover-mark">非 虚 构 的 商 业 史</div>
  <h1>彩蛋</h1>
  <p class="cn-sub">影响世界的顶级商人</p>
  <div class="author">作者：揖光尘</div>
  <div class="rule"></div>
  <div class="en">THE EASTER EGG<br />THE MERCHANTS WHO CHANGED THE WORLD</div>

  <svg viewBox="0 0 560 280" fill="none" aria-hidden="true">
    <defs>
      <clipPath id="eeEgg">
        <path d="M280 28 C332 28 360 118 360 164 C360 212 326 244 280 244 C234 244 200 212 200 164 C200 118 228 28 280 28 Z" />
      </clipPath>
    </defs>

    <!-- 蛋壳 -->
    <path d="M280 28 C332 28 360 118 360 164 C360 212 326 244 280 244 C234 244 200 212 200 164 C200 118 228 28 280 28 Z"
          stroke="currentColor" stroke-width="1.4" opacity=".72" />

    <!-- 腰间缎带与圆点花纹（裁在蛋内） -->
    <g clip-path="url(#eeEgg)">
      <path d="M188 160 C240 146 320 146 372 160" stroke="currentColor" stroke-width="11" opacity=".16" />
      <path d="M188 160 C240 146 320 146 372 160" stroke="currentColor" stroke-width="1" opacity=".5" />
      <path d="M188 182 C240 168 320 168 372 182" stroke="currentColor" stroke-width="1" opacity=".32" />
      <g fill="currentColor" opacity=".42">
        <circle cx="246" cy="108" r="2.6" />
        <circle cx="280" cy="102" r="2.6" />
        <circle cx="314" cy="108" r="2.6" />
        <circle cx="262" cy="212" r="2.6" />
        <circle cx="298" cy="212" r="2.6" />
      </g>
    </g>

    <!-- 裂缝：从顶端斜下，光从里面透出来 -->
    <path d="M294 30 L284 66 L300 94 L288 126 L302 154"
          stroke="var(--accent)" stroke-width="1.8" stroke-linejoin="round" fill="none" opacity=".92" />
    <g fill="var(--accent)">
      <circle cx="326" cy="58" r="2.4" opacity=".9" />
      <circle cx="340" cy="40" r="1.7" opacity=".7" />
      <circle cx="314" cy="26" r="1.5" opacity=".6" />
      <circle cx="348" cy="72" r="1.3" opacity=".5" />
      <path d="M334 92 l1.5 4.2 4.2 1.5 -4.2 1.5 -1.5 4.2 -1.5 -4.2 -4.2 -1.5 4.2 -1.5 z" opacity=".8" />
    </g>

    <!-- 落影 -->
    <path d="M222 256 Q280 268 338 256" stroke="currentColor" stroke-width="1" opacity=".32" />
  </svg>
</section>

<section class="toc-wrap">
  <div class="toc-inner">
    <h2>目 录</h2>
    <ul class="toc">
__TOC__
    </ul>
  </div>
</section>

__BODY__

<section class="colophon">
  <p>彩 蛋 · 影 响 世 界 的 顶 级 商 人</p>
  <p>正文约 __CHARS__ 千字　|　单行本　__DATE__</p>
</section>

<div id="tools">
  <button id="theme" title="切换明暗">◐</button>
  <button id="top" title="回到顶部">↑</button>
  <button id="print" title="打印 / 另存为 PDF">⎙</button>
</div>

<script>
(function(){
  var bar = document.getElementById('bar');
  function onScroll(){
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    bar.style.width = (max > 0 ? (h.scrollTop / max * 100) : 0) + '%';
  }
  window.addEventListener('scroll', onScroll, {passive:true});
  onScroll();

  var root = document.documentElement;
  document.getElementById('theme').onclick = function(){
    root.dataset.theme = root.dataset.theme === 'night' ? 'paper' : 'night';
    try{ localStorage.setItem('ee-theme', root.dataset.theme); }catch(e){}
  };
  try{
    var saved = localStorage.getItem('ee-theme');
    if(saved) root.dataset.theme = saved;
  }catch(e){}

  document.getElementById('top').onclick = function(){
    window.scrollTo({top:0, behavior:'smooth'});
  };
  document.getElementById('print').onclick = function(){ window.print(); };

  // 侧栏：移动端开合 + 当前章节高亮
  var toggle = document.getElementById('sb-toggle');
  toggle.onclick = function(){ document.body.classList.toggle('sb-open'); };
  var links = Array.prototype.slice.call(document.querySelectorAll('.sb-link'));
  var arts = links.map(function(a){ return document.getElementById('ch' + a.dataset.idx); });
  function markActive(){
    var y = window.scrollY + window.innerHeight * 0.28, cur = -1;
    for(var i=0;i<arts.length;i++){
      if(arts[i] && arts[i].offsetTop <= y) cur = i; else break;
    }
    links.forEach(function(a,i){ a.classList.toggle('active', i === cur); });
    var act = links[cur];
    if(act){
      var nav = act.parentNode, r = act.getBoundingClientRect(), nr = nav.getBoundingClientRect();
      if(r.top < nr.top || r.bottom > nr.bottom){
        nav.scrollTop += (r.top - nr.top) - nav.clientHeight * 0.4;
      }
    }
  }
  window.addEventListener('scroll', function(){ onScroll(); markActive(); }, {passive:true});
  links.forEach(function(a){
    a.addEventListener('click', function(){
      if(window.innerWidth <= 900) document.body.classList.remove('sb-open');
    });
  });
  markActive();
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
