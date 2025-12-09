import json
import os
import threading
import inspect
from datetime import datetime, timedelta
from typing import Optional, Dict

from Config import Config as cf
from OnionScraperLib import FileOperate as fo
from OnionScraperLib import Log

_write_lock = threading.Lock()


def _sanitize_group_name(group_name: str) -> str:
    safe = ''.join(ch for ch in group_name if ch.isalnum() or ch in ('_', '-'))
    return safe or 'unknown_group'


def _group_dir(group_name: str) -> str:
    dir_path = os.path.join(cf.PATH_LOG2_ROOT, _sanitize_group_name(group_name))
    fo.Func_CreateDirectry(dir_path)
    return dir_path


def _cleanup_old_logs(dir_path: str) -> None:
    retention_days = getattr(cf, 'LOG2_RETENTION_DAYS', 0)
    if retention_days <= 0:
        return

    cutoff = datetime.now() - timedelta(days=retention_days)
    try:
        for entry in os.listdir(dir_path):
            path = os.path.join(dir_path, entry)
            if os.path.isfile(path):
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                if mtime < cutoff:
                    os.remove(path)
    except Exception as exc:
        Log.LoggingWithFormat('GroupLogger', logCategory='E', logtext=f'cleanup failed: {exc}', note='')


def log(group_name: str, stage: str, message: str, level: str = 'INFO', extra: Optional[Dict] = None) -> None:
    if getattr(cf, 'LOG2_ENABLED', False) is False:
        return

    try:
        dir_path = _group_dir(group_name)
        _cleanup_old_logs(dir_path)

        timestamp = datetime.now()
        caller = inspect.stack()[1]
        frame = caller.frame
        entry = {
            'timestamp': timestamp.isoformat(),
            'level': level,
            'stage': stage,
            'message': message,
            'source_file': os.path.basename(frame.f_code.co_filename),
            'function': frame.f_code.co_name,
            'line': frame.f_lineno,
            'thread': threading.current_thread().name,
            'lineCount': len(message.splitlines()),
            'extra': extra or {}
        }

        file_path = os.path.join(dir_path, f'{timestamp.strftime("%Y-%m-%d")}.jsonl')
        with _write_lock:
            with open(file_path, 'a', encoding='utf-8') as stream:
                json.dump(entry, stream, ensure_ascii=False)
                stream.write('\n')
    except Exception as exc:
        Log.LoggingWithFormat('GroupLogger', logCategory='E', logtext=f'log failed: {exc}', note='')
