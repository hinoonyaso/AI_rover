#!/usr/bin/env python3
"""Back up or restore an offline local knowledge index.

한글: 사용 중이지 않은 로컬 지식 색인을 백업하거나 복원한다.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'backend'))
from knowledge import Knowledge, STORE
from knowledge_archive import export_index, restore_index


def main():
    """Export the active generation or restore to a new directory. / 활성 세대 백업 또는 새 경로 복원."""
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='action', required=True)
    backup = sub.add_parser('backup')
    backup.add_argument('archive', type=Path)
    restore = sub.add_parser('restore')
    restore.add_argument('archive', type=Path)
    restore.add_argument('destination', type=Path)
    args = parser.parse_args()
    if args.action == 'backup':
        store = Knowledge(STORE)
        try:
            result = export_index(store, args.archive)
        finally:
            store.client.close()
    else:
        result = restore_index(args.archive, args.destination)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
