'use strict';
const $ = id => document.getElementById(id);
const state = { game: null, busy: false, mode: null, focus: 112 };

function toast(message) {
  $('toast').textContent = message; $('toast').hidden = false;
  clearTimeout(toast.timer); toast.timer = setTimeout(() => $('toast').hidden = true, 6000);
}
async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
  let body;
  try { body = await response.json(); } catch { throw new Error('Không đọc được phản hồi từ máy chủ.'); }
  if (!response.ok) throw new Error(body.error || 'Không kết nối được máy chủ.');
  return body;
}
async function resizeDesktop(width, height) {
  if (window.pywebview?.api?.resize) {
    try { await window.pywebview.api.resize(width, height); }
    catch { /* Browser mode and GUI resize failures keep the web layout usable. */ }
  }
}
function resizeMenuToContent() {
  // The native window includes a title bar; leave room for that and a small
  // gutter so the rounded XP border never meets the WebView's clipped edge.
  const height = Math.max(632, Math.ceil($('mainWindow').getBoundingClientRect().height + 48));
  return resizeDesktop(700, height);
}
function syncBusy() {
  for (const id of ['pvpBtn', 'pveBtn', 'restartBtn', 'gameBack', 'closeGame']) $(id).disabled = state.busy;
  $('board').setAttribute('aria-busy', String(state.busy));
}
function buildBoard() {
  for (let n = 1; n <= 15; n++) {
    for (const id of ['topCoords', 'leftCoords']) { const span = document.createElement('span'); span.textContent = n; $(id).append(span); }
  }
  for (let row = 0; row < 15; row++) {
    const rowEl = document.createElement('div'); rowEl.className = 'board-row'; rowEl.setAttribute('role', 'row');
    for (let col = 0; col < 15; col++) {
      const cell = document.createElement('button'); cell.type = 'button'; cell.className = 'cell'; cell.setAttribute('role', 'gridcell');
      cell.tabIndex = row * 15 + col === state.focus ? 0 : -1;
      cell.addEventListener('click', () => move(row, col));
      cell.addEventListener('keydown', event => {
        const deltas = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
        if (!deltas[event.key]) return;
        event.preventDefault(); const [dr, dc] = deltas[event.key];
        const r = Math.max(0, Math.min(14, row + dr)), c = Math.max(0, Math.min(14, col + dc));
        state.focus = r * 15 + c;
        document.querySelectorAll('.cell').forEach((el, i) => { el.tabIndex = i === state.focus ? 0 : -1; if (i === state.focus) el.focus(); });
      });
      rowEl.append(cell);
    }
    $('board').append(rowEl);
  }
}
function render() {
  syncBusy(); const game = state.game; if (!game) return;
  const pve = game.mode === 'pve', finished = !!game.winner;
  $('modeLabel').textContent = pve ? 'NGƯỜI vs AI' : 'NGƯỜI vs NGƯỜI';
  $('starterLabel').textContent = `Bốc thăm: ${pve ? (game.starter === 'X' ? 'bạn' : 'AI') : game.starter} đi trước`;
  $('playerXName').textContent = pve ? 'Bạn' : 'Người chơi X';
  $('playerOName').textContent = pve ? 'Máy tính' : 'Người chơi O';
  $('oDetail').textContent = pve ? (game.llm_enabled ? 'Minimax + LLM' : 'Minimax · Offline') : 'Quân O';
  $('playerX').classList.toggle('active', !finished && game.turn === 'X');
  $('playerO').classList.toggle('active', !finished && game.turn === 'O');
  const wins = new Set((game.win_cells || []).map(([r, c]) => r * 15 + c));
  document.querySelectorAll('.cell').forEach((cell, i) => {
    const row = Math.floor(i / 15), col = i % 15, mark = game.board[row][col];
    cell.textContent = mark === '.' ? '' : mark;
    cell.className = `cell ${mark === '.' ? '' : mark}${game.last_move?.[0] === row && game.last_move?.[1] === col ? ' last' : ''}${wins.has(i) ? ' winning' : ''}`;
    cell.setAttribute('aria-disabled', String(state.busy || finished || mark !== '.' || (pve && game.turn !== 'X')));
    cell.setAttribute('aria-label', `Hàng ${row + 1}, cột ${col + 1}, ${mark === '.' ? 'trống' : mark}${wins.has(i) ? ', chuỗi thắng' : ''}`);
  });
  $('moveCount').textContent = `${game.moves} / 225 nước`;
  const symbol = $('turnSymbol'), status = $('statusText'), sub = $('statusSub');
  symbol.className = `turn-symbol ${game.turn.toLowerCase()}`;
  if (game.winner === 'draw') { symbol.textContent = '='; status.textContent = 'Hòa rồi!'; sub.textContent = 'Bàn cờ đã đầy. Thử lại một ván nữa nhé.'; }
  else if (finished) { symbol.textContent = game.winner; status.textContent = pve ? (game.winner === 'X' ? 'Bạn chiến thắng!' : 'Máy tính thắng!') : `${game.winner} chiến thắng!`; sub.textContent = 'Đúng 5 quân liên tiếp. Chọn Ván mới để chơi tiếp.'; }
  else if (state.busy && pve && game.turn === 'O') { symbol.textContent = '⋯'; symbol.classList.add('thinking'); status.textContent = 'AI đang suy nghĩ'; sub.textContent = 'Đang tìm nước đi tốt nhất…'; }
  else if (pve && game.turn === 'O') { symbol.textContent = 'O'; status.textContent = 'Đến lượt AI'; sub.textContent = 'Nhấn thử lại để tiếp tục ván đấu.'; }
  else { symbol.textContent = game.turn; status.textContent = pve ? 'Đến lượt bạn' : `Đến lượt ${game.turn}`; sub.textContent = state.busy ? 'Đang ghi nhận nước đi…' : 'Chọn một ô trống để đánh.'; }
  $('retryAiBtn').hidden = state.busy || finished || !pve || game.turn !== 'O';
  $('aiNote').hidden = !pve; $('aiNote').textContent = game.ai_note || (game.llm_enabled ? 'Đã kết nối cấu hình LLM.' : 'AI sẵn sàng chơi offline.');
  $('gameFooter').textContent = finished ? 'Ván đấu đã kết thúc' : state.busy ? 'Đang xử lý nước đi…' : 'Chúc bạn có một ván cờ vui!';
  $('gameDot').classList.toggle('busy', state.busy);
}
async function aiTurn() {
  if (state.game.mode === 'pve' && state.game.turn === 'O' && !state.game.winner) {
    render(); state.game = await api(`/api/game/${state.game.id}/ai`, { revision: state.game.moves }); render();
  }
}
async function recover(error) {
  toast(error.message);
  if (state.game) {
    try { state.game = await api(`/api/game/${state.game.id}`); } catch { /* Keep the last confirmed board and show the error. */ }
  }
}
async function newGame(mode) {
  if (state.busy) return;
  state.busy = true; syncBusy();
  try {
    state.game = await api('/api/game', { mode }); state.mode = mode;
    if (!$('gameDialog').open) {
      await resizeDesktop(790, 790);
      $('gameDialog').showModal();
    }
    render(); await aiTurn();
  } catch (error) { await recover(error); }
  finally { state.busy = false; render(); }
}
async function move(row, col) {
  const game = state.game;
  if (!game || state.busy || game.winner || game.board[row][col] !== '.' || (game.mode === 'pve' && game.turn !== 'X')) return;
  state.busy = true; render();
  try {
    state.game = await api(`/api/game/${game.id}/move`, { row, col, revision: game.moves });
    render(); await aiTurn();
  } catch (error) { await recover(error); }
  finally { state.busy = false; render(); }
}
$('retryAiBtn').onclick = async () => {
  if (state.busy) return; state.busy = true; render();
  try { await aiTurn(); } catch (error) { await recover(error); }
  finally { state.busy = false; render(); }
};
$('pvpBtn').onclick = () => newGame('pvp'); $('pveBtn').onclick = () => newGame('pve');
$('restartBtn').onclick = () => newGame(state.mode);
$('closeGame').onclick = $('gameBack').onclick = () => { if (!state.busy) $('gameDialog').close(); };
$('gameDialog').addEventListener('cancel', event => { if (state.busy) event.preventDefault(); });
$('gameDialog').addEventListener('close', resizeMenuToContent);
$('helpBtn').onclick = () => { $('rulesDetails').open = !$('rulesDetails').open; };
$('rulesDetails').addEventListener('toggle', () => requestAnimationFrame(resizeMenuToContent));
$('minimizeBtn').onclick = () => window.pywebview?.api?.minimize?.();
buildBoard();
api('/api/config').then(config => {
  $('engineStatus').textContent = config.llm_configured ? 'Sẵn sàng · Minimax + Claude' : 'Sẵn sàng · AI offline';
}).catch(error => toast(error.message));
