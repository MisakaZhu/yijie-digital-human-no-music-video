#!/usr/bin/env python3
"""Check the public release allowlist, local references and obvious secret patterns."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SKILL = 'skills/yijie-digital-human-no-music-video/'
EXPECTED = {'README.md', 'LICENSE', '.gitignore', 'tests/test_recent_sources.py',
            'tests/test_verify_media.py', 'tools/audit_package.py'}
EXPECTED |= {SKILL + name for name in ('SKILL.md', 'agents/openai.yaml', 'config.example.json',
             'scripts/recent_sources.py', 'scripts/verify_media.py', 'references/configuration.md',
             'references/copy-quality.md', 'references/recent-sources.md', 'references/workflow.md',
             'references/task-isolation.md', 'references/work-library-source.md',
             'references/smart-packaging-preview-download.md', 'references/authorized-local-download.md')}
PATTERNS = {
    'github_token': r'(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{20,}',
    'private_key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'private_windows_path': r'[A-Za-z]:\\(?:Users\\|Downloads\\|WB\\|一姐)',
    'phone_number': r'(?<![0-9])1[3-9][0-9]{9}(?![0-9])',
    'personal_authorization': r'standing_user_preapproval_[0-9]{4}',
    'signed_result_url': r'https?://[^\s<>\"]+[?&](?:Signature|X-Amz-Signature|q-signature)=',
}


def audit(root: Path = ROOT) -> dict:
    errors: list[str] = []
    files: dict[str, str] = {}
    for path in root.rglob('*'):
        relative = path.relative_to(root)
        if '.git' in relative.parts or '__pycache__' in relative.parts:
            continue
        if path.is_symlink():
            errors.append('symlink: ' + relative.as_posix())
        elif path.is_file():
            name = relative.as_posix()
            files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
            if name not in EXPECTED:
                errors.append('unexpected_file: ' + name)
                continue
            try:
                text = path.read_text(encoding='utf-8')
            except UnicodeError:
                errors.append('not_utf8: ' + name)
                continue
            for category, pattern in PATTERNS.items():
                if re.search(pattern, text, re.IGNORECASE):
                    errors.append(category + ': ' + name)
            if path.suffix == '.py':
                try:
                    ast.parse(text, filename=name)
                except SyntaxError:
                    errors.append('invalid_python: ' + name)
            if path.suffix == '.md':
                for href in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)', text):
                    if re.match(r'^[a-z][a-z0-9+.-]*:', href, re.IGNORECASE) or href.startswith('#'):
                        continue
                    target = (path.parent / unquote(href.split('#', 1)[0])).resolve()
                    if not target.is_relative_to(root.resolve()) or not target.exists():
                        errors.append('broken_or_external_local_reference: ' + name + ': ' + href)
    for missing in sorted(EXPECTED - set(files)):
        errors.append('missing_file: ' + missing)
    config = root / (SKILL + 'config.example.json')
    if config.is_file():
        try:
            values = json.loads(config.read_text(encoding='utf-8'))
            if values.get('workbench_url') is not None or values.get('allowed_voice_models') != [] or values.get('avatar_names') != []:
                errors.append('personal_default_in_config')
            if values.get('topic_count') != 5 or values.get('background_music') != '无音乐':
                errors.append('wrong_workflow_defaults')
        except (ValueError, AttributeError):
            errors.append('invalid_example_config')
    return {'status': 'passed' if not errors else 'failed', 'files': len(files),
            'errors': errors, 'sha256': files,
            'scope': 'allowlist_references_and_obvious_patterns_only'}


if __name__ == '__main__':
    report = audit()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report['status'] == 'passed' else 1)
