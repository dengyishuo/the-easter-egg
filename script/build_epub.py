#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《彩蛋：影响世界的顶级商人》EPUB 3 构建脚本

复用 build.py 的 ORDER / PART_SUB / md_to_html，把 draft/*.md 打包成标准 EPUB 3。
不依赖 ebooklib 与 pandoc，直接按 EPUB 3 规范手写容器。

用法： python3 script/build_epub.py
产物： output/彩蛋-影响世界的顶级商人.epub
"""

import os
import re
import io
import html
import uuid
import zipfile
import datetime

import build as B   # 同一目录下的 build.py

ROOT = B.ROOT
DRAFT = B.DRAFT
OUT = B.OUT
MEDIA = os.path.join(ROOT, "media")
COVER_IMG = os.path.join(MEDIA, "cover.png")

BOOK_ID = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL,
                                       "https://github.com/dengyishuo/the-easter-egg"))
LANG = "zh-CN"

CSS = """
@charset "utf-8";

body {
  margin: 0 0.6em;
  font-family: "Songti SC", "Noto Serif SC", "Source Han Serif SC", serif;
  font-size: 1em;
  line-height: 1.75;
  color: #1c1a17;
  text-align: justify;
  -webkit-hyphens: auto;
}

/* 封面 */
.cover { margin: 0; padding: 0; text-align: center; }
.cover img { max-width: 100%; max-height: 100%; }

/* 书名页 */
.titlepage { text-align: center; padding-top: 22%; }
.titlepage h1 { font-size: 3em; font-weight: normal; letter-spacing: 0.16em; margin: 0 0 0.7em; text-indent: 0.16em; }
.titlepage .sub { font-size: 1.15em; letter-spacing: 0.22em; color: #4a453d; margin: 0 0 2.4em; }
.titlepage .author { font-size: 0.95em; letter-spacing: 0.28em; color: #4a453d; }
.titlepage .en { font-size: 0.7em; letter-spacing: 0.2em; color: #8a8175; line-height: 2.1; margin-top: 3em; }
.titlepage .rule { width: 4em; height: 1px; background: #8a5a1f; margin: 2.4em auto; }

/* 部扉页 */
.partpage { text-align: center; padding-top: 30%; page-break-before: always; }
.partpage .pname { font-size: 1.7em; letter-spacing: 0.18em; margin: 0 0 1em; text-indent: 0.18em; }
.partpage .psub { font-size: 0.85em; letter-spacing: 0.14em; color: #8a8175; margin: 0; }
.partpage .prule { width: 2.4em; height: 1px; background: #ded5c4; margin: 1.6em auto; }

/* 章 */
h2.chapter { font-size: 1.5em; font-weight: normal; line-height: 1.45; letter-spacing: 0.03em;
  margin: 0 0 1.4em; padding-bottom: 0.8em; border-bottom: 1px solid #ded5c4; }
.chapnum { display: block; font-size: 0.62em; letter-spacing: 0.2em; color: #8a5a1f; margin-bottom: 0.9em; }

h3 { font-size: 1.1em; font-weight: bold; margin: 2em 0 0.8em; letter-spacing: 0.04em; }
h4 { font-size: 1em; font-weight: bold; margin: 1.6em 0 0.6em; }

p { margin: 0 0 0.9em; text-indent: 2em; }
p.noindent, li p { text-indent: 0; }

blockquote {
  margin: 1.4em 0; padding: 0.9em 1.1em;
  background: #f6f1e6; border-left: 2px solid #8a5a1f;
  font-size: 0.95em;
}
blockquote p { text-indent: 0; margin: 0 0 0.5em; }
blockquote p:last-child { margin-bottom: 0; }

ul, ol { margin: 0 0 1.1em; padding-left: 1.8em; }
li { margin: 0.3em 0; }

hr { border: 0; height: 1px; background: #ded5c4; margin: 2em 18%; }

strong { font-weight: bold; }
em { font-style: italic; }
code { font-family: monospace; font-size: 0.9em; background: #f6f1e6; padding: 0 0.2em; }

/* 表格：小屏横向可滚，宽表自动缩字 */
.table-wrap { margin: 1.3em 0; overflow-x: auto; -webkit-overflow-scrolling: touch; }
table { border-collapse: collapse; width: 100%; font-size: 0.76em; line-height: 1.55; }
th, td { padding: 0.4em 0.5em; text-align: left; border-bottom: 1px solid #ded5c4; vertical-align: top; }
th { background: #f6f1e6; font-weight: bold; }

/* 版权页 */
.colophon { margin-top: 26%; text-align: center; font-size: 0.72em; color: #8a8175; line-height: 2.2; letter-spacing: 0.16em; }
.colophon p { text-indent: 0; margin: 0 0 0.6em; }
"""


def esc(t):
    return html.escape(t, quote=True)


def xhtml(title, body, extra_class=""):
    """包一层合法的 XHTML 文档"""
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE html>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops" '
        f'xml:lang="{LANG}" lang="{LANG}">\n'
        '<head>\n'
        '  <meta charset="utf-8" />\n'
        f'  <title>{esc(title)}</title>\n'
        '  <link rel="stylesheet" type="text/css" href="../css/style.css" />\n'
        '</head>\n'
        f'<body class="{extra_class}">\n{body}\n</body>\n</html>\n'
    )


def build_items():
    """按 ORDER 收集章节，返回 [(part_or_None, title, disp, html_body)]"""
    items = []
    for fname, part in B.ORDER:
        p = os.path.join(DRAFT, fname)
        if not os.path.exists(p):
            print("缺少文件:", fname)
            continue
        for title, body in B.split_sections(p):
            disp = re.sub(r"^第[一二三四五六七八九十]+章[\s\u3000]*", "", title) if part else title
            items.append({"part": part, "title": title, "disp": disp, "html": body})
    return items


def build():
    os.makedirs(OUT, exist_ok=True)
    items = build_items()

    day = datetime.date.today().isoformat()
    total_chars = sum(len(re.sub(r"<[^>]+>", "", d["html"])) for d in items)

    # ---- 组装 XHTML 文件 ----
    files = {}          # zip 内路径 -> bytes
    spine = []          # [(id, href)]

    # 封面
    files["OEBPS/text/cover.xhtml"] = xhtml(
        "封面",
        '<div class="cover"><img src="../images/cover.png" alt="彩蛋：影响世界的顶级商人" /></div>',
        "cover-page")
    spine.append(("cover", "text/cover.xhtml"))

    # 书名页
    files["OEBPS/text/titlepage.xhtml"] = xhtml(
        "书名页",
        '<div class="titlepage">\n'
        '  <h1>彩蛋</h1>\n'
        '  <p class="sub">影响世界的顶级商人</p>\n'
        '  <p class="author">揖光尘</p>\n'
        '  <div class="rule"></div>\n'
        '  <p class="en">THE EASTER EGG<br />THE MERCHANTS WHO CHANGED THE WORLD</p>\n'
        '</div>')
    spine.append(("titlepage", "text/titlepage.xhtml"))

    # 正文与部扉页
    toc_entries = []    # [(part, part_file_id, [(id, disp)])]
    cur_part = None
    seq = 0
    part_idx = 0

    for i, d in enumerate(items):
        if d["part"] and d["part"] != cur_part:
            cur_part = d["part"]
            part_idx += 1
            pid = f"part{part_idx:02d}"
            sub = B.PART_SUB.get(cur_part, "")
            files[f"OEBPS/text/{pid}.xhtml"] = xhtml(
                cur_part,
                '<div class="partpage">\n'
                f'  <p class="pname">{esc(cur_part)}</p>\n'
                f'  <p class="psub">{esc(sub)}</p>\n'
                '</div>')
            spine.append((pid, f"text/{pid}.xhtml"))
            toc_entries.append([cur_part, pid, []])

        cid = f"ch{i:02d}"
        if d["part"]:
            seq += 1
            num_html = f'<span class="chapnum">第 {seq:02d} 章</span>'
            toc_label = f"{seq:02d}　{d['disp']}"
        else:
            num_html = ""
            toc_label = d["disp"]

        # 章标题固定 h2；正文小节整体降一级（h2→h3、h3→h4），避免与章标题同级
        body_html = re.sub(r"<(/?)h([2-5])([ >])",
                           lambda m: f"<{m.group(1)}h{int(m.group(2)) + 1}{m.group(3)}",
                           d["html"])
        body = (f'<h2 class="chapter">{num_html}{esc(d["disp"])}</h2>\n'
                f'{body_html}')
        files[f"OEBPS/text/{cid}.xhtml"] = xhtml(d["disp"], body)
        spine.append((cid, f"text/{cid}.xhtml"))

        if d["part"]:
            if not toc_entries:
                toc_entries.append(["正文", cid, []])
            toc_entries[-1][2].append((cid, toc_label))
        else:
            toc_entries.append([None, cid, [(cid, toc_label)]])

    # 版权页
    files["OEBPS/text/colophon.xhtml"] = xhtml(
        "版权",
        '<div class="colophon">\n'
        '  <p>彩　蛋</p>\n'
        '  <p>影响世界的顶级商人</p>\n'
        '  <p>　</p>\n'
        '  <p>揖光尘　著</p>\n'
        f'  <p>正文约 {total_chars // 1000} 千字</p>\n'
        f'  <p>{day}</p>\n'
        '</div>')
    spine.append(("colophon", "text/colophon.xhtml"))

    # ---- nav.xhtml（EPUB 3 目录）----
    nav_items = []
    for part, pfile, chaps in toc_entries:
        links = "\n".join(
            f'        <li><a href="text/{cid}.xhtml">{esc(label)}</a></li>'
            for cid, label in chaps)
        if part:
            nav_items.append(
                f'    <li>\n      <span>{esc(part)}</span>\n      <ol>\n{links}\n      </ol>\n    </li>')
        else:
            nav_items.extend(links.split("\n"))

    nav_body = (
        '<nav epub:type="toc" id="toc">\n'
        '  <h1>目录</h1>\n'
        '  <ol>\n'
        + "\n".join(nav_items) + "\n"
        '  </ol>\n'
        '</nav>\n'
    )
    files["OEBPS/nav.xhtml"] = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE html>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops" '
        f'xml:lang="{LANG}" lang="{LANG}">\n'
        '<head>\n  <meta charset="utf-8" />\n  <title>目录</title>\n'
        '  <link rel="stylesheet" type="text/css" href="css/style.css" />\n</head>\n'
        '<body>\n' + nav_body + '</body>\n</html>\n'
    )

    # ---- toc.ncx（EPUB 2 兼容）----
    def ncx_points():
        out, n = [], 0
        for part, pfile, chaps in toc_entries:
            if part:
                n += 1
                pid, porder = n, n          # 父节点先占位，再让子节点往后排
                subs = []
                for cid, label in chaps:
                    n += 1
                    subs.append(
                        f'    <navPoint id="np{n}" playOrder="{n}">'
                        f'<navLabel><text>{esc(label)}</text></navLabel>'
                        f'<content src="text/{cid}.xhtml" /></navPoint>')
                out.append(
                    f'  <navPoint id="np{pid}" playOrder="{porder}">'
                    f'<navLabel><text>{esc(part)}</text></navLabel>'
                    f'<content src="text/{pfile}.xhtml" />\n'
                    + "\n".join(subs) + '\n  </navPoint>')
            else:
                for cid, label in chaps:
                    n += 1
                    out.append(
                        f'  <navPoint id="np{n}" playOrder="{n}">'
                        f'<navLabel><text>{esc(label)}</text></navLabel>'
                        f'<content src="text/{cid}.xhtml" /></navPoint>')
        return "\n".join(out), n

    points, depth = ncx_points()
    files["OEBPS/toc.ncx"] = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="' + LANG + '">\n'
        '  <head>\n'
        f'    <meta name="dtb:uid" content="{BOOK_ID}" />\n'
        f'    <meta name="dtb:depth" content="2" />\n'
        '    <meta name="dtb:totalPageCount" content="0" />\n'
        '    <meta name="dtb:maxPageNumber" content="0" />\n'
        '  </head>\n'
        f'  <docTitle><text>{esc(B.BOOK_TITLE + "：" + B.BOOK_SUB)}</text></docTitle>\n'
        f'  <docAuthor><text>{esc(B.AUTHOR)}</text></docAuthor>\n'
        '  <navMap>\n' + points + '\n  </navMap>\n'
        '</ncx>\n'
    )

    # ---- content.opf ----
    manifest = [
        '    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />',
        '    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />',
        '    <item id="css" href="css/style.css" media-type="text/css" />',
        '    <item id="coverimg" href="images/cover.png" media-type="image/png" properties="cover-image" />',
    ]
    for sid, href in spine:
        props = ""
        manifest.append(
            f'    <item id="{sid}" href="{href}" media-type="application/xhtml+xml"{props} />')

    spine_xml = "\n".join(f'    <itemref idref="{sid}" />' for sid, _ in spine)

    files["OEBPS/content.opf"] = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
        'unique-identifier="bookid" xml:lang="' + LANG + '">\n'
        '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f'    <dc:identifier id="bookid">{BOOK_ID}</dc:identifier>\n'
        f'    <dc:title>{esc(B.BOOK_TITLE + "：" + B.BOOK_SUB)}</dc:title>\n'
        f'    <dc:creator id="creator">{esc(B.AUTHOR)}</dc:creator>\n'
        '    <meta refines="#creator" property="role" scheme="marc:relators">aut</meta>\n'
        f'    <dc:language>{LANG}</dc:language>\n'
        f'    <dc:date>{day}</dc:date>\n'
        '    <dc:publisher>揖光尘</dc:publisher>\n'
        '    <dc:description>从货郎翻山卖一根针讲起，按时代先后梳理商人如何搬运落差，'
        '又如何在近代开始制造落差——蒸汽机、铁路、电报、电话、电灯、汽车、飞机、零售、'
        '计算机、门户、邮箱、搜索、电商、社交网络、电动汽车与电池、机器人、人工智能。</dc:description>\n'
        '    <dc:subject>商业史</dc:subject>\n'
        '    <dc:subject>企业家</dc:subject>\n'
        '    <dc:subject>技术史</dc:subject>\n'
        '    <meta property="dcterms:modified">'
        + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") +
        '</meta>\n'
        '    <meta name="cover" content="coverimg" />\n'
        '  </metadata>\n'
        '  <manifest>\n' + "\n".join(manifest) + '\n  </manifest>\n'
        '  <spine toc="ncx">\n' + spine_xml + '\n  </spine>\n'
        '  <guide>\n'
        '    <reference type="cover" title="封面" href="text/cover.xhtml" />\n'
        '    <reference type="toc" title="目录" href="nav.xhtml" />\n'
        '    <reference type="text" title="正文" href="text/ch00.xhtml" />\n'
        '  </guide>\n'
        '</package>\n'
    )

    files["OEBPS/css/style.css"] = CSS
    files["META-INF/container.xml"] = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        '  <rootfiles>\n'
        '    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />\n'
        '  </rootfiles>\n'
        '</container>\n'
    )

    # ---- 写盘 ----
    out_path = os.path.join(OUT, "彩蛋-影响世界的顶级商人.epub")
    with zipfile.ZipFile(out_path, "w") as z:
        # mimetype 必须是第一个、且不压缩
        zi = zipfile.ZipInfo("mimetype", date_time=(2026, 1, 1, 0, 0, 0))
        zi.compress_type = zipfile.ZIP_STORED
        z.writestr(zi, "application/epub+zip")

        for name, data in sorted(files.items()):
            if isinstance(data, str):
                data = data.encode("utf-8")
            zi = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, data)

        if os.path.exists(COVER_IMG):
            with open(COVER_IMG, "rb") as f:
                zi = zipfile.ZipInfo("OEBPS/images/cover.png", date_time=(2026, 1, 1, 0, 0, 0))
                zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, f.read())
        else:
            print("警告：缺少封面图 media/cover.png")

    size = os.path.getsize(out_path) / 1024
    print(f"生成：{out_path}")
    print(f"章节 {len(items)} 篇　XHTML {len(spine)} 个　封面 {'有' if os.path.exists(COVER_IMG) else '无'}")
    print(f"体积：{size:.0f} KB")


if __name__ == "__main__":
    build()
