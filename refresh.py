#!/usr/bin/env python3
"""Publish the Smṛtimuktāphalam from dharmasastra-gcp/smp into this repo.

    ./refresh.py            copy, transform, verify, report
    ./refresh.py --check    verify what is already here; copy nothing

This repository is a *deployment*, not a source tree. Nothing here is authored
by hand except README.md, .nojekyll and this file. Everything else is built
next door and copied in:

    dharmasastra-gcp/smp/out/smp_index.html     -> index.html
    dharmasastra-gcp/smp/out/smpN.html          -> smpN.html
    dharmasastra-gcp/smp/out/smpN.md, _blocks.jsonl, _toc.tsv, _headings.tsv,
                         smp2_sources.tsv       -> text/
    dharmasastra-gcp/output_text/smpN_pages/batch_page-NNN_raw.md
                                                -> ocr/smpN/pages/leaf-NNN.md
                    (and _toc, _front the same way)
    dharmasastra-gcp/smp/smpN_manifest.tsv      -> ocr/smpN/manifest.tsv

The loop is the same as the atlas's and the bhāṣaṇam pages': rebuild there,
refresh here, commit here.

    dharmasastra-gcp$  python3 -u smp/smp_build.py
    smp$               ./refresh.py
    smp$               git add -A && git commit -m "refresh" && git push

TWO EDITS, AND WHY THEY ARE HERE AND NOT UPSTREAM. `smp_site.py` writes its
pages for claude.ai artifact hosting, where the host supplies the document
head, so they begin at <title>. GitHub Pages supplies nothing, so each page
gets a doctype, <html lang="sa"> and the charset and viewport metas. And the
anukramaṇikā is `smp_index.html` there and must be `index.html` here, so the
file is renamed and every link to it rewritten. The upstream set is left alone:
it still has to work off a file:// path, and `smp_publish.py` still reads it.

These two edits reproduce the first, hand-made commit of this repository
byte for byte. That was the test this script was written against: run it over
that commit and `git status` must come back clean.

WHY IT VERIFIES INSTEAD OF JUST COPYING. Each kāṇḍa page carries its whole
digest as one embedded JSON blob, and the page renders from it. A blob that
parses but holds the wrong volume, or half a volume, renders a plausible page.
So every page is held to smp.db: its sections, units and quotations must be the
database's counts for that tag, and every relative link in every page must name
a file that exists here. The script exits non-zero rather than leave a page
that disagrees with its own database.
"""
import argparse
import filecmp
import json
import os
import re
import shutil
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get('SMP_SRC', '/home/wipro/projects/dharmasastra-gcp')
OUT = os.path.join(SRC, 'smp', 'out')
TAGS = ['smp%d' % n for n in range(1, 8)]

HEAD = ('<!doctype html>\n<html lang="sa">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n')

# Hand-authored here; never touched, never deleted.
KEEP = {'README.md', '.nojekyll', 'refresh.py', '.git', '.gitignore'}

DATA = re.compile(r'<script id="data" type="application/json">(.*?)</script>', re.S)


def page(src_name, dst_name):
    html = open(os.path.join(OUT, src_name), encoding='utf-8').read()
    if not html.lstrip().lower().startswith('<!doctype'):
        html = HEAD + html
    return html.replace('smp_index.html', 'index.html')


def plan():
    """Every (source, destination, transform) this repo should hold."""
    jobs = [(os.path.join(OUT, 'smp_index.html'), 'index.html', 'page')]
    for t in TAGS:
        jobs.append((os.path.join(OUT, t + '.html'), t + '.html', 'page'))
        for suffix in ('.md', '_blocks.jsonl', '_toc.tsv', '_headings.tsv', '_sources.tsv'):
            s = os.path.join(OUT, t + suffix)
            if os.path.exists(s):
                jobs.append((s, 'text/' + t + suffix, 'copy'))
        jobs.append((os.path.join(SRC, 'smp', t + '_manifest.tsv'),
                     'ocr/%s/manifest.tsv' % t, 'copy'))
        for kind in ('pages', 'toc', 'front'):
            d = os.path.join(SRC, 'output_text', '%s_%s' % (t, kind))
            if not os.path.isdir(d):
                continue
            for f in sorted(os.listdir(d)):
                m = re.match(r'batch_page-(\d+)_raw\.md$', f)
                if m:
                    jobs.append((os.path.join(d, f),
                                 'ocr/%s/%s/leaf-%s.md' % (t, kind, m.group(1)), 'copy'))
    return jobs


def publish(jobs):
    wrote = same = 0
    for src, rel, how in jobs:
        dst = os.path.join(HERE, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if how == 'page':
            new = page(os.path.basename(src), rel)
            if os.path.exists(dst) and open(dst, encoding='utf-8').read() == new:
                same += 1
                continue
            open(dst, 'w', encoding='utf-8').write(new)
        else:
            if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False):
                same += 1
                continue
            shutil.copyfile(src, dst)
        wrote += 1

    # Anything under the managed trees that the source no longer has is a
    # leaf that was deleted or renumbered upstream; leaving it would publish
    # OCR for a page that is no longer in the book.
    wanted = {rel for _, rel, _ in jobs}
    gone = []
    for tree in ('ocr', 'text'):
        for root, _, files in os.walk(os.path.join(HERE, tree)):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), HERE)
                if rel not in wanted:
                    os.remove(os.path.join(HERE, rel))
                    gone.append(rel)
    for f in os.listdir(HERE):
        if f.endswith('.html') and f not in wanted and f not in KEEP:
            os.remove(os.path.join(HERE, f))
            gone.append(f)
    return wrote, same, gone


def verify(jobs):
    bad = []
    db = sqlite3.connect(os.path.join(OUT, 'smp.db'))
    want = {
        'sections': dict(db.execute('select tag, count(*) from section group by tag')),
        'units': dict(db.execute('select tag, count(*) from unit group by tag')),
        'quotes': dict(db.execute('select tag, count(*) from quotation group by tag')),
    }
    present = {rel for _, rel, _ in jobs if os.path.exists(os.path.join(HERE, rel))}
    missing = [rel for _, rel, _ in jobs if rel not in present]
    if missing:
        bad.append('%d file(s) missing, e.g. %s' % (len(missing), missing[0]))

    rows = []
    for t in TAGS:
        path = os.path.join(HERE, t + '.html')
        if not os.path.exists(path):
            bad.append('%s.html is missing' % t)
            continue
        html = open(path, encoding='utf-8').read()
        if not html.startswith('<!doctype html>'):
            bad.append('%s.html has no doctype — GitHub Pages will render it in quirks mode' % t)
        m = DATA.search(html)
        if not m:
            bad.append('%s.html has no embedded data — it would render empty' % t)
            continue
        try:
            D = json.loads(m.group(1))
        except ValueError as e:
            bad.append('%s.html: embedded data does not parse: %s' % (t, e))
            continue
        if D.get('tag') != t:
            bad.append('%s.html carries the data for %s' % (t, D.get('tag')))
        got = {'sections': len(D.get('sections') or []),
               'units': len(D.get('units') or {}),
               'quotes': len(D.get('quotes') or [])}
        for k in got:
            if got[k] != want[k].get(t, 0):
                bad.append('%s.html: %d %s, smp.db has %d'
                           % (t, got[k], k, want[k].get(t, 0)))
        leaves = len([r for r in present if r.startswith('ocr/%s/pages/' % t)])
        rows.append((t, got['sections'], got['units'], got['quotes'], leaves))

    for f in ['index.html'] + [t + '.html' for t in TAGS]:
        p = os.path.join(HERE, f)
        if not os.path.exists(p):
            continue
        html = open(p, encoding='utf-8').read()
        if 'smp_index.html' in html:
            bad.append('%s still links smp_index.html, which does not exist here' % f)
        for href in set(re.findall(r'href="([^"#:?]+\.html)', html)):
            # A template literal — href="${c.tag}.html" — is built at runtime
            # from the data, not a link on disk; the index's kāṇḍa links are
            # checked by name below instead.
            if '${' in href or '{' in href:
                continue
            if not os.path.exists(os.path.join(HERE, href)):
                bad.append('%s links %s, which does not exist here' % (f, href))
    idx = os.path.join(HERE, 'index.html')
    if os.path.exists(idx):
        linked = set(re.findall(r'href="(smp\d)\.html', open(idx, encoding='utf-8').read()))
        for t in TAGS:
            if t not in linked:
                bad.append('index.html does not link %s' % t)
    return rows, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='verify only; copy nothing')
    a = ap.parse_args()
    if not os.path.isdir(OUT):
        sys.exit('no smp build at %s — set $SMP_SRC' % OUT)

    jobs = plan()
    if not a.check:
        wrote, same, gone = publish(jobs)
        print('%d written, %d unchanged, %d removed' % (wrote, same, len(gone)))
        for g in gone[:10]:
            print('  removed', g)

    rows, bad = verify(jobs)
    print('\n  %-6s %9s %7s %8s %11s' % ('kāṇḍa', 'sections', 'units', 'quotes', 'OCR leaves'))
    for t, s, u, q, l in rows:
        print('  %-6s %9d %7d %8d %11d' % (t, s, u, q, l))
    print('  %-6s %9d %7d %8d %11d' % ('total', *[sum(r[i] for r in rows) for i in range(1, 5)]))
    print()
    if bad:
        for b in bad:
            print('FAIL  ' + b)
        return 1
    print('OK — every page agrees with smp.db, and every link resolves')
    return 0


if __name__ == '__main__':
    sys.exit(main())
