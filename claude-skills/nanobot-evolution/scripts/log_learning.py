#!/usr/bin/env python3
import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

WORKSPACE = Path('/Users/onekey/.nanobot/workspace')
EVOLUTION_DIR = WORKSPACE / 'memory' / 'evolution'
INDEX_DIR = WORKSPACE / 'memory' / 'index'


def ensure_dirs():
    EVOLUTION_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)


def tokenize(text: str):
    parts = re.findall(r'[A-Za-z0-9_:/.-]+|[\u4e00-\u9fff]{2,}', text.lower())
    return sorted(set(p for p in parts if len(p) >= 2))


def append_jsonl(path: Path, obj: dict):
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--kind', required=True, choices=['error', 'correction', 'request', 'practice', 'preference'])
    p.add_argument('--topic', default='')
    p.add_argument('--command', default='')
    p.add_argument('--error', dest='error_msg', default='')
    p.add_argument('--fix', default='')
    p.add_argument('--wrong', default='')
    p.add_argument('--correct', default='')
    p.add_argument('--request', dest='request_text', default='')
    p.add_argument('--acceptance', default='')
    p.add_argument('--practice', default='')
    p.add_argument('--reason', default='')
    p.add_argument('--context', default='')
    p.add_argument('--source', default='manual')
    p.add_argument('--severity', default='medium')
    p.add_argument('--tags', default='')
    args = p.parse_args()

    ensure_dirs()
    now = datetime.now().astimezone().isoformat(timespec='seconds')
    tags = [t.strip() for t in args.tags.split(',') if t.strip()]
    entry = {
        'timestamp': now,
        'kind': args.kind,
        'topic': args.topic,
        'command': args.command,
        'error': args.error_msg,
        'fix': args.fix,
        'wrong': args.wrong,
        'correct': args.correct,
        'request': args.request_text,
        'acceptance': args.acceptance,
        'practice': args.practice,
        'reason': args.reason,
        'context': args.context,
        'source': args.source,
        'severity': args.severity,
        'tags': tags,
    }
    text = ' '.join(str(v) for v in entry.values() if v)
    entry['tokens'] = tokenize(text)
    path = EVOLUTION_DIR / f'{args.kind}s.jsonl'
    append_jsonl(path, entry)
    append_jsonl(INDEX_DIR / 'learning_docs.jsonl', {
        'id': f"learning:{args.kind}:{now}",
        'source': 'learning',
        'subtype': args.kind,
        'timestamp': now,
        'path': str(path),
        'title': args.topic or args.command or args.request_text[:80] or args.practice[:80] or args.kind,
        'text': text,
        'tokens': entry['tokens'],
    })
    print(json.dumps({'ok': True, 'path': str(path), 'kind': args.kind, 'timestamp': now}, ensure_ascii=False))


if __name__ == '__main__':
    main()
