import copy
import json
import os
from io import BytesIO
from threading import Thread
from urllib import request, error
import unittest
from unittest.mock import patch

from app import GAMES, GAME_LOCKS, Handler, create_server, load_local_config, play_ai
from caro.engine import EMPTY, Game, HUMAN, SECOND, SIZE, is_win, ranked_ai_moves
from caro.llm import choose_move


def blank():
    return [[EMPTY] * SIZE for _ in range(SIZE)]


class RulesTests(unittest.TestCase):
    def test_exact_five_all_directions_including_blocked_ends(self):
        for dr, dc, start in [(0, 1, (7, 5)), (1, 0, (5, 7)), (1, 1, (5, 5)), (1, -1, (5, 9))]:
            for player in (HUMAN, SECOND):
                with self.subTest(direction=(dr, dc), player=player):
                    board = blank()
                    other = SECOND if player == HUMAN else HUMAN
                    for i in (-1, 5):
                        board[start[0]+i*dr][start[1]+i*dc] = other
                    for i in range(5):
                        row, col = start[0]+i*dr, start[1]+i*dc
                        board[row][col] = player
                    self.assertTrue(is_win(board, row, col, player))

    def test_overline_does_not_win_in_any_direction(self):
        for dr, dc, start in [(0, 1, (7, 4)), (1, 0, (4, 7)), (1, 1, (4, 4)), (1, -1, (4, 10))]:
            game = Game('pvp', turn=HUMAN)
            for i in (0, 1, 3, 4, 5):
                game.board[start[0]+i*dr][start[1]+i*dc] = HUMAN
            game.moves = 5
            game.play(start[0]+2*dr, start[1]+2*dc)
            self.assertIsNone(game.winner)
            self.assertEqual(game.win_cells, [])

    def test_five_in_one_direction_wins_even_if_other_is_overline(self):
        game = Game('pvp', turn=HUMAN)
        for c in (4, 5, 6, 8, 9): game.board[7][c] = HUMAN
        for r in (3, 4, 5, 6): game.board[r][7] = HUMAN
        game.moves = 9
        game.play(7, 7)
        self.assertEqual(game.winner, HUMAN)
        self.assertEqual(len(game.win_cells), 5)

    def test_real_full_board_draw(self):
        # Alternating pairs offset each row: no exact fives in any direction.
        game = Game('pvp', turn=HUMAN)
        game.board = [[HUMAN if (r+2*c) % 4 < 2 else SECOND for c in range(SIZE)] for r in range(SIZE)]
        for r in range(SIZE):
            for c in range(SIZE): self.assertFalse(is_win(game.board, r, c, game.board[r][c]))
        game.board[0][0] = EMPTY
        game.moves = 224
        game.play(0, 0)
        self.assertEqual(game.winner, 'draw')

    def test_win_takes_priority_on_last_cell(self):
        game = Game('pvp', turn=HUMAN)
        game.board = [[HUMAN if (r+2*c) % 4 < 2 else SECOND for c in range(SIZE)] for r in range(SIZE)]
        game.board[0][:6] = [HUMAN, HUMAN, EMPTY, HUMAN, HUMAN, SECOND]
        game.moves = 224
        game.play(0, 2)
        self.assertEqual(game.winner, HUMAN)

    def test_illegal_moves_and_finished_game(self):
        game = Game('pvp', turn=HUMAN)
        for r, c in [(-1, 0), (15, 0), (True, 1), (1.0, 0), ('1', 0)]:
            with self.assertRaises(ValueError): game.play(r, c)
        game.play(7, 7)
        with self.assertRaises(ValueError): game.play(7, 7)
        game.winner = HUMAN
        with self.assertRaises(ValueError): game.play(7, 8)

    def test_random_starter_in_both_modes(self):
        for mode in ('pvp', 'pve'):
            for first in (HUMAN, SECOND):
                with patch('caro.engine.choice', return_value=first) as random_choice:
                    game = Game(mode)
                    self.assertEqual(game.turn, first)
                    self.assertEqual(game.starter, first)
                    random_choice.assert_called_once_with((HUMAN, SECOND))

    def test_public_state_hides_config(self):
        game = Game('pve', api_key='secret-value')
        self.assertNotIn('secret-value', json.dumps(game.public()))
        self.assertNotIn('api_key', game.public())


class AiTests(unittest.TestCase):
    def test_takes_win_before_block(self):
        board = blank()
        board[7][4:8] = [SECOND]*4
        board[3][5:9] = [HUMAN]*4
        original = copy.deepcopy(board)
        moves = ranked_ai_moves(board)
        self.assertIn(moves[0][:2], {(7, 3), (7, 8)})
        self.assertEqual(board, original)

    def test_blocks_four_all_directions(self):
        for dr, dc, start in [(0, 1, (7, 5)), (1, 0, (5, 7)), (1, 1, (5, 5)), (1, -1, (5, 9))]:
            board = blank()
            board[start[0]-dr][start[1]-dc] = SECOND
            for i in range(4): board[start[0]+i*dr][start[1]+i*dc] = HUMAN
            moves = ranked_ai_moves(board)
            self.assertEqual(moves[0][:2], (start[0]+4*dr, start[1]+4*dc))
            self.assertEqual(len(moves), 1)

    def test_blocks_broken_four(self):
        board = blank()
        for c in (4, 5, 7, 8): board[7][c] = HUMAN
        self.assertEqual(ranked_ai_moves(board)[0][:2], (7, 6))

    def test_rejects_false_overline_win_and_blocks_real_threat(self):
        board = blank()
        for c in (3, 4, 6, 7, 8): board[7][c] = SECOND
        board[2][2:6] = [HUMAN]*4
        board[2][1] = SECOND
        self.assertEqual(ranked_ai_moves(board)[0][:2], (2, 6))

    def test_search_finds_double_four(self):
        board = blank()
        for r, c in [(7, 5), (7, 6), (7, 8), (5, 7), (6, 7), (8, 7)]: board[r][c] = SECOND
        board[2][2] = HUMAN
        self.assertEqual(ranked_ai_moves(board, time_limit=2)[0][:2], (7, 7))

    def test_search_does_not_mutate_on_timeout(self):
        board = blank(); board[7][7] = HUMAN
        original = copy.deepcopy(board)
        ranked = ranked_ai_moves(board, time_limit=0)
        self.assertTrue(ranked)
        self.assertEqual(board, original)

    def test_empty_and_full_boards(self):
        self.assertEqual(ranked_ai_moves(blank())[0][:2], (7, 7))
        self.assertEqual(ranked_ai_moves([[HUMAN]*SIZE for _ in range(SIZE)]), [])

    def test_llm_failure_fallback_and_unapproved_move(self):
        for response in [ValueError('bad JSON'), (0, 0), (True, 7)]:
            game = Game('pve', turn=SECOND, model='test', base_url='https://example.com/v1')
            with patch('app.ranked_ai_moves', return_value=[(7, 7, 100), (7, 8, 100)]):
                with patch('app.choose_move', side_effect=response if isinstance(response, Exception) else None, return_value=response):
                    play_ai(game)
            self.assertEqual(game.board[7][7], SECOND)
            self.assertIn('đã dùng Minimax', game.ai_note)

    def test_llm_only_receives_equally_best_moves(self):
        game = Game('pve', turn=SECOND, model='test', base_url='https://example.com/v1')
        with patch('app.ranked_ai_moves', return_value=[(7, 7, 100), (7, 8, 100), (0, 0, 99)]):
            with patch('app.choose_move', return_value=(7, 8)) as llm:
                play_ai(game)
                self.assertEqual(llm.call_args.args[1], [(7, 7, 100), (7, 8, 100)])
        self.assertEqual(game.board[7][8], SECOND)


class ApiTests(unittest.TestCase):
    def setUp(self):
        GAMES.clear(); GAME_LOCKS.clear()
        self.handler = object.__new__(Handler)
        self.handler._json = lambda status, data: setattr(self, 'response', (status, copy.deepcopy(data)))

    def new_game(self, payload, starter=HUMAN):
        with patch('caro.engine.choice', return_value=starter), patch.dict('os.environ', {}, clear=True):
            self.handler._new_game(payload)
        self.assertEqual(self.response[0], 201)
        return self.response[1]

    def test_pvp_random_o_start_and_stale_request(self):
        game = self.new_game({'mode': 'pvp'}, SECOND)
        self.handler._move(game['id'], {'row': 7, 'col': 7, 'revision': 0})
        self.assertEqual(self.response[1]['board'][7][7], SECOND)
        self.handler._move(game['id'], {'row': 7, 'col': 8, 'revision': 0})
        self.assertEqual(self.response[0], 409)
        self.assertEqual(GAMES[game['id']].moves, 1)

    def test_pve_no_key_and_ai_opens(self):
        game = self.new_game({'mode': 'pve'}, SECOND)
        with self.assertRaises(ValueError): self.handler._move(game['id'], {'row': 7, 'col': 7, 'revision': 0})
        self.handler._move(game['id'], {'revision': 0}, ai=True)
        self.assertEqual(self.response[1]['board'][7][7], SECOND)
        self.assertEqual(self.response[1]['turn'], HUMAN)
        self.assertFalse(self.response[1]['llm_enabled'])

    def test_human_and_ai_separate_requests(self):
        game = self.new_game({'mode': 'pve'})
        self.handler._move(game['id'], {'row': 7, 'col': 7, 'revision': 0})
        self.assertEqual(self.response[1]['moves'], 1)
        self.assertEqual(self.response[1]['turn'], SECOND)
        self.handler._move(game['id'], {'revision': 1}, ai=True)
        self.assertEqual(self.response[1]['moves'], 2)
        self.assertEqual(self.response[1]['turn'], HUMAN)

    def test_ai_cannot_play_in_pvp(self):
        game = self.new_game({'mode': 'pvp'})
        with self.assertRaises(ValueError): self.handler._move(game['id'], {'revision': 0}, ai=True)

    def test_bad_settings_rejected(self):
        for payload in [{'mode': []}, {'mode': 'pve', 'model': 'only'}, {'mode': 'pve', 'model': 'x', 'base_url': 'http://example.com/v1'}]:
            with self.assertRaises(ValueError): self.new_game(payload)


class LlmTests(unittest.TestCase):
    def test_valid_and_invalid_llm_responses(self):
        for content, valid in [('{"row":7,"col":8}', True), ('```json\n{"row":7,"col":8}\n```', True), ('{"row":0,"col":0}', False), ('{"row":7.0,"col":8}', False), ('{"row":true,"col":8}', False), ('hello', False)]:
            response = {'choices': [{'message': {'content': content}}]}
            with patch('caro.llm.request.urlopen', return_value=BytesIO(json.dumps(response).encode())):
                if valid:
                    self.assertEqual(choose_move(blank(), [(7, 8, 1)], 'test', 'https://example.com/v1', 'test'), (7, 8))
                else:
                    with self.assertRaises(ValueError): choose_move(blank(), [(7, 8, 1)], 'test', 'https://example.com/v1', 'test')


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server()
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def post(self, path, payload, headers=None):
        req = request.Request(self.base+path, data=json.dumps(payload).encode(), headers=headers or {'Content-Type': 'application/json'})
        return request.urlopen(req)

    def test_http_game_lifecycle(self):
        with patch('caro.engine.choice', return_value=HUMAN):
            with self.post('/api/game', {'mode': 'pvp'}) as response:
                game = json.load(response)
        with self.post(f"/api/game/{game['id']}/move", {'row': 7, 'col': 7, 'revision': 0}) as response:
            self.assertEqual(json.load(response)['board'][7][7], HUMAN)
        with request.urlopen(self.base+'/') as response:
            self.assertIn('Caro XP', response.read().decode())

    def test_reject_external_origin_and_wrong_content_type(self):
        for headers in [{'Content-Type': 'text/plain'}, {'Content-Type': 'application/json', 'Origin': 'https://other.example'}]:
            with self.assertRaises(error.HTTPError) as exc: self.post('/api/game', {'mode': 'pvp'}, headers)
            self.assertEqual(exc.exception.code, 400)


class AnthropicTests(unittest.TestCase):
    def test_native_request_and_text_blocks(self):
        from caro.llm import ANTHROPIC_BASE_URL, ANTHROPIC_MODEL
        response = {'content': [{'type': 'thinking', 'thinking': 'ignored'}, {'type': 'text', 'text': '{"row":7,"col":8}'}], 'stop_reason': 'end_turn'}
        with patch('caro.llm.request.urlopen', return_value=BytesIO(json.dumps(response).encode())) as call:
            move = choose_move(blank(), [(7, 8, 10)], 'test-key', ANTHROPIC_BASE_URL, ANTHROPIC_MODEL, provider='anthropic')
        self.assertEqual(move, (7, 8))
        req = call.call_args.args[0]
        self.assertEqual(req.full_url, 'https://api.anthropic.com/v1/messages')
        self.assertEqual(req.get_header('X-api-key'), 'test-key')
        self.assertEqual(req.get_header('Anthropic-version'), '2023-06-01')
        self.assertIsNone(req.get_header('Authorization'))
        payload = json.loads(req.data)
        self.assertIn('system', payload)
        self.assertEqual([m['role'] for m in payload['messages']], ['user'])
        self.assertNotIn('test-key', req.data.decode())
        self.assertEqual(call.call_args.kwargs['timeout'], 12)

    def test_reject_truncated_refused_invalid_and_missing_text(self):
        from caro.llm import ANTHROPIC_BASE_URL
        for response in [
            {'stop_reason': 'max_tokens', 'content': [{'type': 'text', 'text': '{"row":7,"col":8}'}]},
            {'stop_reason': 'refusal', 'content': []},
            {'content': [{'type': 'thinking', 'thinking': '{"row":7,"col":8}'}]},
            {'content': [{'type': 'text', 'text': '{"row":0,"col":0}'}]},
        ]:
            with patch('caro.llm.request.urlopen', return_value=BytesIO(json.dumps(response).encode())):
                with self.assertRaises(ValueError):
                    choose_move(blank(), [(7, 8, 1)], 'test', ANTHROPIC_BASE_URL, 'test', provider='anthropic')

    def test_key_is_not_sent_to_non_anthropic_host(self):
        with patch('caro.llm.request.urlopen') as call:
            with self.assertRaises(ValueError):
                choose_move(blank(), [(7, 8, 1)], 'test', 'https://example.com/v1', 'test', provider='anthropic')
            call.assert_not_called()

    def test_key_only_configuration_and_offline(self):
        from caro.llm import ANTHROPIC_MODEL
        handler = object.__new__(Handler)
        handler._json = lambda status, data: setattr(self, 'response', data)
        with patch.dict('os.environ', {}, clear=True):
            handler._new_game({'mode': 'pve', 'provider': 'anthropic', 'api_key': 'test'})
            game = GAMES[self.response['id']]
            self.assertEqual(game.model, ANTHROPIC_MODEL)
            self.assertTrue(game.llm_enabled)
            self.assertNotIn('api_key', self.response)
            handler._new_game({'mode': 'pve', 'provider': 'anthropic', 'api_key': '', 'model': '', 'base_url': ''})
            self.assertFalse(self.response['llm_enabled'])
            with self.assertRaises(ValueError):
                handler._new_game({'mode': 'pve', 'provider': 'anthropic', 'model': 'test', 'base_url': 'https://api.anthropic.com/v1'})

    def test_anthropic_environment_key_and_offline_override(self):
        handler = object.__new__(Handler)
        handler._json = lambda status, data: setattr(self, 'response', data)
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-env-key'}, clear=True):
            handler._new_game({'mode': 'pve'})
            self.assertTrue(self.response['llm_enabled'])
            self.assertEqual(self.response['provider'], 'anthropic')
            self.assertNotIn('test-env-key', json.dumps(self.response))
            handler._new_game({'mode': 'pve', 'provider': 'anthropic', 'api_key': '', 'model': '', 'base_url': ''})
            self.assertFalse(self.response['llm_enabled'])

    def test_auth_error_falls_back_without_exposing_response(self):
        from urllib.error import HTTPError
        game = Game('pve', turn=SECOND, provider='anthropic', api_key='test', model='test', base_url='https://api.anthropic.com/v1')
        with patch('app.ranked_ai_moves', return_value=[(7, 7, 10), (7, 8, 10)]), patch('app.choose_move', side_effect=HTTPError(game.base_url, 401, 'secret details', {}, None)):
            play_ai(game)
        self.assertEqual(game.board[7][7], SECOND)
        self.assertIn('API key không hợp lệ', game.ai_note)
        self.assertNotIn('secret details', game.ai_note)

    def test_local_config_loads_key_without_overwriting_system_environment(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            config = Path(directory) / '.env'
            config.write_text("ANTHROPIC_API_KEY='local-test-key'\nCARO_LLM_PROVIDER=anthropic\nUNKNOWN_VALUE=ignored\n")
            with patch.dict('os.environ', {'CARO_LLM_PROVIDER': 'openai'}, clear=True):
                load_local_config(config)
                self.assertEqual(os.environ['ANTHROPIC_API_KEY'], 'local-test-key')
                self.assertEqual(os.environ['CARO_LLM_PROVIDER'], 'openai')
                self.assertNotIn('UNKNOWN_VALUE', os.environ)


if __name__ == '__main__':
    unittest.main()
