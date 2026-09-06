#!/usr/bin/env python3
"""Exercise the real Claude binary against a local, credential-free API fixture."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]


class API(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.requests.append(self.path)
        for message in body.get('messages', []):
            content = message.get('content', [])
            if isinstance(content, list):
                for block in content:
                    if block.get('type') == 'tool_result':
                        self.server.results.append(block)
        tools = {tool.get('name') for tool in body.get('tools', [])}
        if not self.server.results and {'Bash', 'Grep'} <= tools:
            content = [
                {'type': 'tool_use', 'id': 'tool_bash', 'name': 'Bash',
                 'input': {'command': 'printf CORE2_SHELL_OK', 'description': 'Check shell execution'}},
                {'type': 'tool_use', 'id': 'tool_grep', 'name': 'Grep',
                 'input': {'pattern': 'CORE2_SEARCH_OK', 'path': 'fixture.txt', 'output_mode': 'content'}},
            ]
            stop = 'tool_use'
        else:
            content = [{'type': 'text', 'text': 'CORE2_COMPAT_OK'}]
            stop = 'end_turn'
        message = {'id': 'msg_fixture', 'type': 'message', 'role': 'assistant',
                   'model': body.get('model', 'claude-sonnet-4-6'), 'content': content,
                   'stop_reason': stop, 'stop_sequence': None,
                   'usage': {'input_tokens': 10, 'output_tokens': 10}}
        self.send_response(200)
        if body.get('stream'):
            self.send_header('Content-Type', 'text/event-stream')
            self.end_headers()

            def event(kind, **data):
                payload = {'type': kind, **data}
                self.wfile.write(('event: ' + kind + '\ndata: ' + json.dumps(payload) + '\n\n').encode())

            event('message_start', message={**message, 'content': [], 'stop_reason': None})
            for index, block in enumerate(content):
                if block['type'] == 'text':
                    event('content_block_start', index=index, content_block={'type': 'text', 'text': ''})
                    event('content_block_delta', index=index, delta={'type': 'text_delta', 'text': block['text']})
                else:
                    event('content_block_start', index=index, content_block={**block, 'input': {}})
                    event('content_block_delta', index=index, delta={'type': 'input_json_delta', 'partial_json': json.dumps(block['input'])})
                event('content_block_stop', index=index)
            event('message_delta', delta={'stop_reason': stop, 'stop_sequence': None}, usage={'output_tokens': 10})
            event('message_stop')
            self.wfile.flush()
        else:
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(message).encode())


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), API)
    server.results = []
    server.requests = []
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with tempfile.TemporaryDirectory(prefix='claude-compat-') as directory:
            work = Path(directory)
            (work / 'fixture.txt').write_text('CORE2_SEARCH_OK\n')
            (work / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True}))
            # Do not inherit Codex's private rg or other tool-only PATH entries.
            env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': directory, 'TERM': 'dumb',
                   'LANG': 'C.UTF-8', 'CLAUDE_CONFIG_DIR': str(work / '.claude'),
                   'ANTHROPIC_API_KEY': 'local-fixture-key-not-a-real-credential',
                   'ANTHROPIC_BASE_URL': 'http://127.0.0.1:' + str(server.server_port),
                   'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1',
                   'DISABLE_AUTOUPDATER': '1'}
            completed = subprocess.run(
                [str(ROOT / 'claude'), '-p', 'Run the shell and search checks, then report success.',
                 '--model', 'claude-sonnet-4-6', '--tools', 'Bash,Grep',
                 '--allowedTools', 'Bash(printf CORE2_SHELL_OK)', 'Grep',
                 '--max-turns', '3', '--no-session-persistence'],
                cwd=work, env=env, text=True, capture_output=True, timeout=180,
            )
            report = {'returncode': completed.returncode, 'stdout': completed.stdout,
                      'stderr': completed.stderr, 'requests': server.requests, 'tool_results': server.results}
            (ROOT / 'logs').mkdir(exist_ok=True)
            (ROOT / 'logs/integration.json').write_text(json.dumps(report, indent=2))
            print(json.dumps(report, indent=2))
            assert completed.returncode == 0, 'Claude failed'
            assert 'CORE2_COMPAT_OK' in completed.stdout, 'No final response'
            by_id = {result['tool_use_id']: result for result in server.results}
            for identifier, marker in [('tool_bash', 'CORE2_SHELL_OK'), ('tool_grep', 'CORE2_SEARCH_OK')]:
                assert identifier in by_id, 'Missing tool result: ' + identifier
                assert not by_id[identifier].get('is_error'), by_id[identifier]
                assert marker in json.dumps(by_id[identifier]['content']), by_id[identifier]
            print('PASS: streaming response, shell subprocess, search subprocess, tool results, final response.')
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


if __name__ == '__main__':
    main()
