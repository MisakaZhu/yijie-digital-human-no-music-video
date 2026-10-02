from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/yijie-digital-human-no-music-video/scripts/recent_sources.py'
SPEC = importlib.util.spec_from_file_location('recent_sources', SCRIPT)
recent = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recent)
NOW = datetime(2026, 10, 2, 8, 0, tzinfo=timezone.utc)
SOURCE_ID = '1000000000000000001'
SOURCE = f'https://www.douyin.com/video/{SOURCE_ID}'


class RecentSourcesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / 'runs'
        self.root.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def record(self, run='run-a', **overrides):
        data = {'run_id': run, 'source_url': SOURCE, 'source_video_id': SOURCE_ID,
                'created_at': (NOW - timedelta(hours=2)).isoformat(),
                'completed_at': (NOW - timedelta(hours=1)).isoformat(),
                'generation_status': 'verified', 'local_validation_status': 'passed',
                'result_identity_evidence': {'opening': 'synthetic narration'},
                'title': '测试 | 标题', 'local_file': str(self.root / 'missing.mp4')}
        data.update(overrides)
        directory = self.root / run
        directory.mkdir()
        (directory / 'task-checkpoint.json').write_text(json.dumps(data), encoding='utf-8')
        return data

    def test_same_video_id_across_url_forms_is_duplicate_even_if_file_missing(self):
        self.record()
        result, code = recent.check(self.root, f'https://www.douyin.com/?modal_id={SOURCE_ID}', None, None, NOW)
        self.assertEqual((result['status'], code), ('duplicate', 10))
        self.assertEqual(result['matches'][0]['local_file_status'], 'verified_but_missing')

    def test_source_created_long_ago_but_completed_recently_is_counted(self):
        self.record(created_at=(NOW - timedelta(days=30)).isoformat())
        self.assertEqual(recent.check(self.root, SOURCE, None, None, NOW)[1], 10)

    def test_old_verified_result_expires_but_active_task_does_not(self):
        self.record(completed_at=(NOW - timedelta(hours=169)).isoformat())
        self.assertEqual(recent.check(self.root, SOURCE, None, None, NOW)[0]['status'], 'no_match')
        self.record('run-b', generation_status='submitted', local_validation_status=None,
                    result_identity_evidence=None, created_at=(NOW - timedelta(days=30)).isoformat())
        result, code = recent.check(self.root, SOURCE, None, None, NOW)
        self.assertEqual(code, 10)
        self.assertTrue(result['matches'][0]['active'])

    def test_exclude_current_run_and_failed_tasks(self):
        self.record()
        self.record('run-b', generation_status='failed', phase='failed')
        result, code = recent.check(self.root, SOURCE, None, 'run-a', NOW)
        self.assertEqual((result['status'], code), ('no_match', 0))

    def test_file_alone_or_submission_never_counts_as_completed_generation(self):
        present = self.root / 'arbitrary.mp4'
        present.write_bytes(b'not actually a video')
        self.record(generation_status='submitted', local_file=str(present),
                    result_identity_evidence=None, local_validation_status=None)
        result = recent.refresh(self.root, self.root / 'index.md', NOW)
        self.assertEqual((result['records'], result['unique']), (0, 0))

    def test_unresolved_short_link_is_unknown_unless_exact_link_matches(self):
        short = 'https://v.douyin.com/synthetic-example/'
        self.assertEqual(recent.check(self.root, short, None, None, NOW)[1], 11)
        self.record(source_url=short)
        self.assertEqual(recent.check(self.root, short, None, None, NOW)[1], 10)

    def test_conflicting_ids_and_naive_times_fail_closed(self):
        self.record(source_video_id='1000000000000000002')
        result, code = recent.check(self.root, SOURCE, None, None, NOW)
        self.assertEqual((result['status'], code), ('evidence_incomplete', 12))
        self.record('run-b', completed_at='2026-10-02T07:00:00')
        self.assertEqual(len(recent.load_records(self.root, NOW)[1]), 2)

    def test_corrupt_json_does_not_overwrite_existing_index(self):
        directory = self.root / 'broken'
        directory.mkdir()
        (directory / 'task-checkpoint.json').write_text('{broken', encoding='utf-8')
        output = self.root / 'index.md'
        output.write_text('previous verified index', encoding='utf-8')
        result = recent.refresh(self.root, output, NOW)
        self.assertFalse(result['output_written'])
        self.assertEqual(output.read_text(encoding='utf-8'), 'previous verified index')

    def test_refresh_deduplicates_and_redacts_query_and_fragment(self):
        self.record(source_url=SOURCE + '?trace=synthetic-only#synthetic-fragment')
        self.record('run-b')
        output = self.root / 'index.md'
        result = recent.refresh(self.root, output, NOW)
        text = output.read_text(encoding='utf-8')
        self.assertEqual((result['records'], result['unique']), (2, 1))
        self.assertNotIn('trace=', text)
        self.assertNotIn('#synthetic-fragment', text)
        self.assertIn(r'测试 \| 标题', text)
        safe = recent.check(self.root, SOURCE, None, None, NOW)[0]
        self.assertNotIn('trace=', json.dumps(safe))

    def test_direct_copy_is_not_a_source_and_empty_index_has_zero_records(self):
        self.record(source_url=None, source_video_id=None)
        result = recent.refresh(self.root, self.root / 'index.md', NOW)
        self.assertEqual(result['records'], 0)

    def test_completed_without_result_identity_is_incomplete(self):
        self.record(result_identity_evidence=None)
        self.assertEqual(recent.check(self.root, SOURCE, None, None, NOW)[1], 12)

    def test_platform_preview_evidence_can_prove_generation_without_local_file(self):
        self.record(local_validation_status=None, local_file=None, preview_status='verified',
                    result_origin='work_library', result_preview_clicked_at=NOW.isoformat())
        result, code = recent.check(self.root, SOURCE, None, None, NOW)
        self.assertEqual(code, 10)
        self.assertEqual(result['matches'][0]['local_file_status'], 'platform_only')


if __name__ == '__main__':
    unittest.main()
