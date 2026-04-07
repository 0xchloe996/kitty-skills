#!/usr/bin/env python3
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

WORKSPACE = Path('/Users/onekey/.nanobot/workspace')
SESSIONS_DIR = WORKSPACE / 'sessions'
INDEX_DIR = WORKSPACE / 'memory' / 'index'
OUT = INDEX_DIR / 'session_rollups.jsonl'
STATE = INDEX_DIR / '.session_rollups_state.json'


def tokenize(text: str):
    return re.findall(r'[A-Za-z0-9_:/.-]+|[\u4e00-\u9fff]{2,}', text.lower())


def top_terms(texts, n=12):
    stop = {'the','and','for','that','with','this','from','you','have','are','was','will','not','use','tool','用户','需要','完成','一个','这个','进行','可以','不要','以及','然后','如果','已经','现在'}
    c = Counter()
    for t in texts:
        for tok in tokenize(t):
            if len(tok) >= 2 and tok not in stop:
                c[tok] += 1
    return [k for k,_ in c.most_common(n)]


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding='utf-8'))
    return {}


def save_state(obj):
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def parse_session(path: Path):
    user_msgs, assistant_msgs, tool_errors = [], [], []
    first_ts = None
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if not first_ts:
            first_ts = obj.get('timestamp')
        role = obj.get('role')
        content = obj.get('content') or ''
        if role == 'user':
            user_msgs.append(content[:500])
        elif role == 'assistant' and content:
            assistant_msgs.append(content[:500])
        elif role == 'tool':
            c = obj.get('content') or ''
            if 'Error:' in c or 'STDERR:' in c or 'Exit code:' in c:
                tool_errors.append(c[:500])
    joined = user_msgs[:3] + user_msgs[-2:] + assistant_msgs[:2] + tool_errors[:3]
    keywords = top_terms(joined)
    summary = {
        'id': f'session:{path.name}',
        'source': 'session_rollup',
        'path': str(path),
        'timestamp': first_ts or datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        'title': path.name,
        'user_count': len(user_msgs),
        'assistant_count': len(assistant_msgs),
        'tool_error_count': len(tool_errors),
        'keywords': keywords,
        'highlights': {
            'first_user': user_msgs[:2],
            'last_user': user_msgs[-2:],
            'tool_errors': tool_errors[:3],
        },
        'text': ' | '.join(joined)[:4000],
        'tokens': keywords,
        'mtime': path.stat().st_mtime,
    }
    return summary


def main():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    state = load_state()
    seen = state.get('files', {})
    existing = set()
    if OUT.exists():
        for line in OUT.read_text(encoding='utf-8', errors='ignore').splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                existing.add(obj.get('id'))
            except Exception:
                pass
    appended = []
    for path in sorted(SESSIONS_DIR.glob('*.jsonl')):
        mtime = path.stat().st_mtime
        if seen.get(path.name) == mtime:
            continue
        rollup = parse_session(path)
        appended.append(rollup)
        seen[path.name] = mtime
    if appended:
        with OUT.open('a', encoding='utf-8') as f:
            for obj in appended:
                f.write(json.dumps(obj, ensure_ascii=False) + '\n')
    save_state({'files': seen, 'updated_at': datetime.now().astimezone().isoformat(timespec='seconds')})
    print(json.dumps({'ok': True, 'updated': len(appended), 'output': str(OUT)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
