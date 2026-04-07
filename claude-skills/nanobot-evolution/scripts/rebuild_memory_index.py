#!/usr/bin/env python3
import json
import re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path('/Users/onekey/.nanobot/workspace')
MEMORY_DIR = WORKSPACE / 'memory'
INDEX_DIR = MEMORY_DIR / 'index'
DOCS = INDEX_DIR / 'docs.jsonl'


def tokenize(text: str):
    return sorted(set(re.findall(r'[A-Za-z0-9_:/.-]+|[\u4e00-\u9fff]{2,}', text.lower())))


def add_doc(out, doc_id, source, path, title, text, timestamp=''):
    text = text.strip()
    if not text:
        return
    obj = {
        'id': doc_id,
        'source': source,
        'path': str(path),
        'title': title[:200],
        'timestamp': timestamp,
        'text': text[:6000],
        'tokens': tokenize(text)[:200],
    }
    out.write(json.dumps(obj, ensure_ascii=False) + '\n')


def parse_history(out, path: Path):
    buf = []
    ts = ''
    idx = 0
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        if line.startswith('[') and '] ' in line:
            if buf:
                add_doc(out, f'history:{idx}', 'history', path, buf[0][:120], '\n'.join(buf), ts)
                idx += 1
            ts = line[1:17]
            buf = [line]
        else:
            if buf:
                buf.append(line)
    if buf:
        add_doc(out, f'history:{idx}', 'history', path, buf[0][:120], '\n'.join(buf), ts)


def parse_memory_md(out, path: Path):
    current = []
    title = path.name
    idx = 0
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        if line.startswith('#'):
            if current:
                add_doc(out, f'memory:{idx}', 'memory', path, title, '\n'.join(current))
                idx += 1
            title = line.lstrip('# ').strip()
            current = [line]
        else:
            current.append(line)
    if current:
        add_doc(out, f'memory:{idx}', 'memory', path, title, '\n'.join(current))


def parse_jsonl_docs(out, path: Path, source: str):
    if not path.exists():
        return
    for i, line in enumerate(path.read_text(encoding='utf-8', errors='ignore').splitlines()):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        text = obj.get('text') or json.dumps(obj, ensure_ascii=False)
        title = obj.get('title') or obj.get('topic') or obj.get('id') or path.name
        add_doc(out, f'{source}:{i}', source, path, title, text, obj.get('timestamp', ''))


def main():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with DOCS.open('w', encoding='utf-8') as out:
        mem = MEMORY_DIR / 'MEMORY.md'
        hist = MEMORY_DIR / 'HISTORY.md'
        if mem.exists():
            parse_memory_md(out, mem)
        if hist.exists():
            parse_history(out, hist)
        for p in sorted((MEMORY_DIR / 'evolution').glob('*.jsonl')):
            parse_jsonl_docs(out, p, 'learning')
        parse_jsonl_docs(out, INDEX_DIR / 'session_rollups.jsonl', 'session_rollup')
        for bucket in ['episodic', 'semantic', 'procedural']:
            d = MEMORY_DIR / bucket
            if d.exists():
                for file in sorted(d.rglob('*.md')):
                    add_doc(out, f'{bucket}:{file.relative_to(MEMORY_DIR)}', bucket, file, file.stem, file.read_text(encoding='utf-8', errors='ignore'))
    meta = {
        'updated_at': datetime.now().astimezone().isoformat(timespec='seconds'),
        'docs_path': str(DOCS),
    }
    (INDEX_DIR / 'index_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    count = sum(1 for _ in DOCS.open('r', encoding='utf-8')) if DOCS.exists() else 0
    print(json.dumps({'ok': True, 'docs': count, 'path': str(DOCS)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
