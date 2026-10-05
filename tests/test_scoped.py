"""Verify scope argument boundaries and failure propagation with a fake manager."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ScopeTests(unittest.TestCase):
    def test_forwarding_and_manager_failure(self):
        with tempfile.TemporaryDirectory(prefix='scope test ') as directory:
            root = Path(directory)
            manager = root / 'manager'
            manager.write_text('#!/usr/bin/python3\nimport json,os,sys\nprint(json.dumps({"args":sys.argv[1:],"cwd":os.getcwd(),"marker":os.environ.get("TEST_MARKER")}))\nsys.exit(int(os.environ.get("TEST_EXIT","0")))\n')
            manager.chmod(0o755)
            launcher = root / 'claude-scoped'
            launcher.write_text((ROOT / 'claude-scoped').read_text().replace('/usr/bin/systemd-run', '"' + str(manager) + '"'))
            launcher.chmod(0o755)
            link = root / 'symlink'
            link.symlink_to(launcher)
            env={'PATH':'/usr/bin:/bin','HOME':str(root),'TEST_MARKER':'kept'}
            command=[str(link),'-p','argument with spaces','--model','example']
            result=subprocess.run(command,cwd=root,env=env,capture_output=True,text=True,check=True)
            data=json.loads(result.stdout)
            self.assertEqual(data['args'],['--user','--scope','--quiet','--collect','--slice=claude.slice',str(root/'claude'),*command[1:]])
            self.assertEqual(data['cwd'],str(root))
            self.assertEqual(data['marker'],'kept')
            env['TEST_EXIT']='7'
            self.assertEqual(subprocess.run(command,cwd=root,env=env,capture_output=True).returncode,7)

    def test_fast_version_checks_selected_installation(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            shutil.copy2(ROOT/'claude-scoped',root/'claude-scoped')
            (root/'current').write_text('2.1.263\n')
            env={'PATH':'/usr/bin:/bin','HOME':directory}
            args=[str(root/'claude-scoped'),'--version']
            self.assertNotEqual(subprocess.run(args,env=env,capture_output=True).returncode,0)
            for name in ['downloads/claude-2.1.263','tools/qemu/usr/bin/qemu-x86_64']:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text('#!/bin/sh\nexit 99\n');p.chmod(0o755)
            result=subprocess.run(args,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0)
            self.assertEqual(result.stdout,'2.1.263 (Claude Code)\n')
            (root/'current').write_text('../invalid')
            self.assertNotEqual(subprocess.run(args,env=env,capture_output=True).returncode,0)
