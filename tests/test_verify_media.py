from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/yijie-digital-human-no-music-video/scripts/verify_media.py'
SPEC = importlib.util.spec_from_file_location('verify_media', SCRIPT)
media = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(media)


class MediaBasicTests(unittest.TestCase):
    def test_incomplete_name_is_not_a_deliverable(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'video.mp4.part'
            file.write_bytes(b'synthetic')
            with self.assertRaisesRegex(ValueError, 'unfinished_or_non_mp4'):
                media.verify(file)

    def test_promotion_refuses_existing_file_without_modifying_it(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'video.mp4.part'
            target = Path(directory) / 'video.mp4'
            source.write_bytes(b'synthetic')
            target.write_bytes(b'preserve original')
            with self.assertRaisesRegex(ValueError, 'destination_already_exists'):
                media.verify(source, promote_to=target)
            self.assertEqual(target.read_bytes(), b'preserve original')
            self.assertTrue(source.exists())


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg tools not installed')
class MediaIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def fixture(self, filename='synthetic.mp4', audio=True):
        target = self.root / filename
        arguments = [shutil.which('ffmpeg'), '-nostdin', '-v', 'error',
                     '-f', 'lavfi', '-i', 'color=c=blue:s=128x128:r=10:d=1']
        if audio:
            arguments += ['-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-shortest']
        arguments += ['-c:v', 'mpeg4', '-c:a', 'aac', '-f', 'mp4', str(target)]
        subprocess.run(arguments, capture_output=True, check=True, timeout=20)
        return target

    def test_real_mp4_decodes_and_reports_limits(self):
        result = media.verify(self.fixture())
        self.assertEqual(result['status'], 'passed')
        self.assertGreater(result['duration_seconds'], 0)
        self.assertEqual(len(result['sha256']), 64)
        self.assertFalse(result['content_identity_checked'])
        self.assertFalse(result['background_music_listened'])

    def test_valid_part_is_promoted_only_after_full_verification(self):
        source = self.fixture('synthetic.mp4.part')
        target = self.root / 'synthetic.mp4'
        result = media.verify(source, promote_to=target)
        self.assertTrue(target.is_file())
        self.assertFalse(source.exists())
        self.assertEqual(result['file'], str(target.resolve()))

    def test_html_disguised_as_mp4_fails(self):
        file = self.root / 'shell.mp4'
        file.write_bytes(b'<html>' + b'error page ' * 200)
        with self.assertRaisesRegex(ValueError, 'not_mp4_header'):
            media.verify(file)

    def test_missing_narration_audio_fails(self):
        with self.assertRaisesRegex(ValueError, 'narration_requires_video_and_audio'):
            media.verify(self.fixture(audio=False))

    def test_truncated_container_cannot_be_promoted(self):
        source = self.fixture('broken.mp4.part')
        content = source.read_bytes()
        source.write_bytes(content[:max(1100, len(content) // 2)])
        with self.assertRaises(ValueError):
            media.verify(source, promote_to=self.root / 'broken.mp4')
        self.assertTrue(source.exists())
        self.assertFalse((self.root / 'broken.mp4').exists())


if __name__ == '__main__':
    unittest.main()
