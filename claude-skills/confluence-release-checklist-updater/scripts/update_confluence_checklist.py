#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import uuid
import urllib.request
from pathlib import Path

CONFIG_PATH = Path('/Users/onekey/.nanobot/confluence.json')
CLIENTS = [
    'IOS-TF包',
    'OneKey-WEB',
    '安卓',
    'Desktop-TF 包',
    'OneKey-Desktop-RN（测Mac平台）',
    'OneKey-Desktop-RN（测window平台）',
    'ipad',
]


def load_config() -> dict:
    data = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    data['baseUrl'] = data['baseUrl'].rstrip('/')
    return data


def auth_header(cfg: dict) -> str:
    return 'Basic ' + base64.b64encode(f"{cfg['email']}:{cfg['token']}".encode()).decode()


def parse_page_id(value: str) -> str:
    value = value.strip()
    if value.isdigit():
        return value
    m = re.search(r'/pages/(\d+)(?:/|$|\?)', value)
    if m:
        return m.group(1)
    raise SystemExit('Unable to parse Confluence page id')


def api_get(url: str, auth: str) -> dict:
    req = urllib.request.Request(url, headers={'Authorization': auth, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def api_put(url: str, auth: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': auth,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        },
        method='PUT',
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def build_task_list(items: list[str], start_id: int = 70000) -> str:
    parts = ['<ac:task-list>']
    counter = start_id
    for item in items:
        counter += 1
        parts.extend([
            '<ac:task>',
            f'<ac:task-id>{counter}</ac:task-id>',
            f'<ac:task-uuid>{uuid.uuid4()}</ac:task-uuid>',
            '<ac:task-status>incomplete</ac:task-status>',
            f'<ac:task-body><span class="placeholder-inline-tasks">{item}</span></ac:task-body>',
            '</ac:task>',
        ])
    parts.append('</ac:task-list>')
    return ''.join(parts)


def replace_checklist_content_column(storage_html: str, items_map: dict[str, list[str]]) -> str:
    anchor = '最终要发布的包必须完成以下 checklist'
    anchor_idx = storage_html.find(anchor)
    if anchor_idx == -1:
        raise SystemExit('Checklist anchor not found')

    table_start = storage_html.find('<table', anchor_idx)
    table_end = storage_html.find('</table>', table_start)
    if table_start == -1 or table_end == -1:
        raise SystemExit('Checklist table not found')

    table_html = storage_html[table_start:table_end + len('</table>')]
    start_id = 70000
    for client in CLIENTS:
        if client not in items_map:
            continue
        pattern = re.compile(
            rf'(<tr[^>]*>\s*<td[^>]*>.*?{re.escape(client)}.*?</td>\s*)(<td[^>]*>.*?</td>)(\s*<td[^>]*>.*?</td>\s*</tr>)',
            re.S,
        )
        new_td = f'<td>{build_task_list(items_map[client], start_id=start_id)}</td>'
        table_html, n = pattern.subn(rf'\1{new_td}\3', table_html, count=1)
        if n != 1:
            raise SystemExit(f'Failed to update row: {client}')
        start_id += 100

    return storage_html[:table_start] + table_html + storage_html[table_end + len('</table>'):]


def load_items_map(path: str) -> dict[str, list[str]]:
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise SystemExit('items-map JSON must be an object')
    return {k: list(v) for k, v in data.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description='Update only the Checklist 的内容 column in a Confluence release checklist page')
    parser.add_argument('--page', required=True, help='Confluence page URL or page ID')
    parser.add_argument('--items-map', required=True, help='Path to JSON file: {client: [items...]}')
    parser.add_argument('--dry-run', action='store_true', help='Validate and render replacement without writing back to Confluence')
    args = parser.parse_args()

    cfg = load_config()
    auth = auth_header(cfg)
    page_id = parse_page_id(args.page)
    items_map = load_items_map(args.items_map)

    page = api_get(f"{cfg['baseUrl']}/wiki/rest/api/content/{page_id}?expand=body.storage,version,space", auth)
    new_html = replace_checklist_content_column(page['body']['storage']['value'], items_map)

    if args.dry_run:
        print(json.dumps({
            'updated': False,
            'dry_run': True,
            'page_id': page_id,
            'title': page['title'],
            'next_version': page['version']['number'] + 1,
            'url': f"{cfg['baseUrl']}/wiki/spaces/{page['space']['key']}/pages/{page_id}",
            'html_changed': new_html != page['body']['storage']['value'],
        }, ensure_ascii=False, indent=2))
        return 0

    result = api_put(
        f"{cfg['baseUrl']}/wiki/rest/api/content/{page_id}",
        auth,
        {
            'id': page_id,
            'type': page['type'],
            'title': page['title'],
            'version': {'number': page['version']['number'] + 1},
            'body': {'storage': {'value': new_html, 'representation': 'storage'}},
        },
    )
    print(json.dumps({
        'updated': True,
        'page_id': result['id'],
        'title': result['title'],
        'version': result['version']['number'],
        'url': f"{cfg['baseUrl']}/wiki/spaces/{page['space']['key']}/pages/{page_id}",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
