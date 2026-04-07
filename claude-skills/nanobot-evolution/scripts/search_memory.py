#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

DOCS = Path('/Users/onekey/.nanobot/workspace/memory/index/docs.jsonl')


def tokenize(text: str):
    return re.findall(r'[A-Za-z0-9_:/.-]+|[\u4e00-\u9fff]{2,}', text.lower())


def score(query, doc):
    q_tokens = tokenize(query)
    text = (doc.get('title','') + '\n' + doc.get('text','')).lower()
    s = 0
    for tok in q_tokens:
        if tok in text:
            s += 5 if len(tok) > 3 else 2
    if query.lower() in text:
        s += 15
    if doc.get('source') == 'memory':
        s += 2
    return s


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--query', required=True)
    p.add_argument('--top', type=int, default=8)
    p.add_argument('--json', action='store_true')
    args = p.parse_args()

    if not DOCS.exists():
        raise SystemExit('index not found; run rebuild_memory_index.py first')

    docs = []
    for line in DOCS.read_text(encoding='utf-8', errors='ignore').splitlines():
        if not line.strip():
            continue
        try:
            doc = json.loads(line)
        except Exception:
            continue
        sc = score(args.query, doc)
        if sc > 0:
            doc['_score'] = sc
            docs.append(doc)
    docs.sort(key=lambda x: (-x['_score'], x.get('timestamp','')), reverse=False)
    docs = sorted(docs, key=lambda x: x['_score'], reverse=True)[:args.top]

    if args.json:
        print(json.dumps(docs, ensure_ascii=False, indent=2))
        return

    for i, d in enumerate(docs, 1):
        print(f"[{i}] score={d['_score']} source={d.get('source')} title={d.get('title')}")
        if d.get('timestamp'):
            print(f"    ts: {d['timestamp']}")
        print(f"    path: {d.get('path')}")
        snippet = d.get('text','').replace('\n', ' ')[:220]
        print(f"    {snippet}")
        print()


if __name__ == '__main__':
    main()
