"""Loopback HTTP backend. Browser: python3 app.py; desktop: python3 desktop.py."""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse
from urllib.error import HTTPError
from uuid import uuid4

from caro.engine import Game, HUMAN, SECOND, ranked_ai_moves
from caro.llm import choose_move, ANTHROPIC_BASE_URL, ANTHROPIC_MODEL

WEB = Path(__file__).resolve().parent / 'web'
LOCAL_CONFIG = WEB.parent / '.env'
CONFIG_KEYS = {'ANTHROPIC_API_KEY', 'CARO_LLM_PROVIDER', 'CARO_LLM_BASE_URL',
               'CARO_LLM_MODEL', 'CARO_LLM_API_KEY'}


def load_local_config(path=LOCAL_CONFIG):
    """Read only supported settings from this project's private local file."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        name, value = (part.strip() for part in line.split('=', 1))
        if name in CONFIG_KEYS:
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            os.environ.setdefault(name, value)


load_local_config()
GAMES: dict[str, Game] = {}
GAME_LOCKS: dict[str, Lock] = {}
GAMES_LOCK = Lock()
MAX_BODY = 16_384


def valid_base_url(value):
    parsed = urlparse(value)
    return bool(parsed.netloc and not parsed.username and not parsed.password
                and not parsed.query and not parsed.fragment
                and (parsed.scheme == 'https' or
                     (parsed.scheme == 'http' and parsed.hostname in {'localhost', '127.0.0.1', '::1'})))


def play_ai(game):
    candidates = ranked_ai_moves(game.board)
    if not candidates:
        raise ValueError('AI không còn nước đi.')
    row, col, best_score = candidates[0]
    # Only equally scored best candidates may be passed to the LLM; it cannot
    # override a forced win/block or pick a known weaker minimax result.
    safe = [move for move in candidates if move[2] == best_score]
    game.ai_note = 'Minimax đang chơi offline. Chưa cấu hình Claude trên máy.'
    if game.llm_enabled:
        if len(safe) == 1:
            game.ai_note = 'Minimax chọn nước mạnh nhất; không cần gọi LLM.'
        else:
            try:
                selected = choose_move(game.board, safe, game.api_key, game.base_url, game.model, provider=game.provider)
                if (not isinstance(selected, (tuple, list)) or len(selected) != 2
                    or any(type(n) is not int for n in selected)
                    or tuple(selected) not in {(r, c) for r, c, _ in safe}):
                    raise ValueError('Nước LLM không hợp lệ.')
                row, col = selected
                game.ai_note = 'LLM đã chọn giữa các nước tốt nhất do Minimax đề xuất.'
            except HTTPError as exc:
                reason = {401: 'API key không hợp lệ', 403: 'key chưa có quyền truy cập', 404: 'không tìm thấy model', 429: 'API đang giới hạn lượt gọi'}.get(exc.code, 'API gặp lỗi')
                game.ai_note = f'LLM: {reason}; đã dùng Minimax.'
            except Exception:
                game.ai_note = 'LLM chưa khả dụng hoặc trả về nước sai; đã dùng Minimax.'
    game.play(row, col)


class Handler(BaseHTTPRequestHandler):
    def _json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        if self.headers.get_content_type() != 'application/json':
            raise ValueError('Yêu cầu phải dùng application/json.')
        # The app is local; disallow other sites from driving its API.
        origin = self.headers.get('Origin')
        if origin and origin not in {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}:
            raise ValueError('Nguồn yêu cầu không hợp lệ.')
        length = int(self.headers.get('Content-Length', '0'))
        if not 0 < length <= MAX_BODY:
            raise ValueError('Dữ liệu gửi lên không hợp lệ.')
        data = json.loads(self.rfile.read(length))
        if not isinstance(data, dict):
            raise ValueError('Dữ liệu phải là JSON object.')
        return data

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/api/config':
            return self._json(200, {'llm_configured': bool(os.getenv('ANTHROPIC_API_KEY') or (os.getenv('CARO_LLM_BASE_URL') and os.getenv('CARO_LLM_MODEL')))})
        if path.startswith('/api/game/'):
            game_id = path.removeprefix('/api/game/')
            with GAMES_LOCK:
                game, lock = GAMES.get(game_id), GAME_LOCKS.get(game_id)
            if not game:
                return self._json(404, {'error': 'Không tìm thấy ván đấu.'})
            with lock:
                return self._json(200, {'id': game_id, **game.public()})
        files = {'/': ('index.html', 'text/html'), '/style.css': ('style.css', 'text/css'), '/app.js': ('app.js', 'text/javascript')}
        if path not in files:
            return self._json(404, {'error': 'Không tìm thấy trang.'})
        filename, content_type = files[path]
        body = (WEB / filename).read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', content_type + '; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            data = self._body()
            if self.path == '/api/game':
                return self._new_game(data)
            parts = self.path.strip('/').split('/')
            if len(parts) == 4 and parts[:2] == ['api', 'game'] and parts[3] in {'move', 'ai'}:
                return self._move(parts[2], data, ai=parts[3] == 'ai')
            self._json(404, {'error': 'Không tìm thấy API.'})
        except (ValueError, TypeError, KeyError) as exc:
            self._json(400, {'error': str(exc)})

    def _new_game(self, data):
        mode = data.get('mode')
        if mode not in ('pvp', 'pve'):
            raise ValueError('Chế độ chơi không hợp lệ.')
        game = Game(mode=mode)
        if mode == 'pve':
            game.provider = data.get('provider', os.getenv('CARO_LLM_PROVIDER') or ('anthropic' if os.getenv('ANTHROPIC_API_KEY') else 'openai'))
            if game.provider not in ('anthropic', 'openai'):
                raise ValueError('Nhà cung cấp LLM không hợp lệ.')
            # Local environment is the normal configuration source.
            for field, env in [('api_key', 'CARO_LLM_API_KEY'), ('base_url', 'CARO_LLM_BASE_URL'), ('model', 'CARO_LLM_MODEL')]:
                default = os.getenv(env, '')
                if game.provider == 'anthropic' and field == 'api_key':
                    default = os.getenv('ANTHROPIC_API_KEY') or default
                value = data.get(field, default)
                if not isinstance(value, str):
                    raise ValueError('Cấu hình LLM phải là chuỗi.')
                setattr(game, field, value.strip())
            if game.provider == 'anthropic' and game.api_key:
                game.base_url = game.base_url or ANTHROPIC_BASE_URL
                game.model = game.model or ANTHROPIC_MODEL
            game.base_url = game.base_url.rstrip('/')
            if game.base_url or game.model or game.api_key:
                if not game.model or not valid_base_url(game.base_url):
                    raise ValueError('Hãy điền cả Base URL và model, hoặc để trống để chơi offline.')
                if game.provider == 'anthropic':
                    if game.base_url != ANTHROPIC_BASE_URL:
                        raise ValueError('Claude sử dụng endpoint https://api.anthropic.com/v1.')
                    if not game.api_key:
                        raise ValueError('Hãy nhập Anthropic API key hoặc tắt kết nối LLM.')
        game_id = uuid4().hex
        with GAMES_LOCK:
            # Only the latest 128 local games are retained in memory.
            if len(GAMES) >= 128:
                oldest = next(iter(GAMES))
                GAMES.pop(oldest)
                GAME_LOCKS.pop(oldest)
            GAMES[game_id], GAME_LOCKS[game_id] = game, Lock()
        self._json(201, {'id': game_id, **game.public()})

    def _move(self, game_id, data, ai=False):
        with GAMES_LOCK:
            game, lock = GAMES.get(game_id), GAME_LOCKS.get(game_id)
        if not game:
            return self._json(404, {'error': 'Không tìm thấy ván đấu.'})
        with lock:
            revision = data.get('revision')
            if type(revision) is not int or revision != game.moves:
                return self._json(409, {'error': 'Bàn cờ đã thay đổi. Hãy đồng bộ lại ván đấu.'})
            if game.done:
                raise ValueError('Ván đấu đã kết thúc.')
            if ai:
                if game.mode != 'pve' or game.turn != SECOND:
                    raise ValueError('Chưa đến lượt AI.')
                play_ai(game)
            else:
                if game.mode == 'pve' and game.turn != HUMAN:
                    raise ValueError('Chưa đến lượt người chơi.')
                game.play(data.get('row'), data.get('col'))
                game.ai_note = ''
            self._json(200, {'id': game_id, **game.public()})


def create_server(port=0):
    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main():
    server = create_server(int(os.environ.get('CARO_PORT', '8000')))
    print(f'Caro XP: http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
