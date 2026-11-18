'use strict';
const $ = id => document.getElementById(id);
const LEVELS = { easy: ['Dễ', 2, '0,5'], medium: ['Vừa', 3, '1'], hard: ['Khó', 4, '1,5'] };
// 3×3 levels are plain search depths; 'hard' searches the whole game tree.
const SMALL_HINTS = { easy: 'Nhìn trước 1 nước', medium: 'Nhìn trước 2 nước', hard: 'Duyệt toàn bộ cây' };
function savedSize() {
  try { return localStorage.getItem('caroSize') === '3' ? 3 : 15; } catch { return 15; }
}
function savedLevel() {
  try { const value = localStorage.getItem('caroLevel'); return LEVELS[value] ? value : 'hard'; } catch { return 'hard'; }
}
const state = { game: null, busy: false, counting: false, mode: null, focus: 112, level: savedLevel(), size: savedSize(), n: 0 };
// The AI always takes at least this long (plus a little jitter) so its moves are easy to follow.
const AI_MIN_DELAY = 1100, AI_JITTER = 500;
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
// The 15×15 sidebar rule text, restored when leaving a 3×3 game.
const RULE_15 = ['ruleTitle', 'ruleMarks', 'ruleText'].map(id => $(id).innerHTML);
const RULE_3 = ['Đủ 3 là thắng', '× × ×', 'Ngang, dọc hoặc chéo.<br>Bàn đầy là hòa.'];

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
// The app never resizes the native window (that would also drop full screen);
// the game screen fills whatever size the window has and the board scales to it.
function fitBoard() {
  const panel = $('boardPanel'), content = panel.parentElement, n = state.n;
  if ($('gameScreen').hidden || !n) return;
  const style = getComputedStyle(content), row = style.flexDirection === 'row';
  const px = name => parseFloat(style[name]) || 0;
  // Side by side: the board gets the content width minus the sidebar; stacked
  // (narrow screens): the panel's own share of the height.
  const width = row ? content.clientWidth - px('paddingLeft') - px('paddingRight') - $('boardPanel').nextElementSibling.offsetWidth - px('columnGap') : panel.clientWidth;
  const height = row ? content.clientHeight - px('paddingTop') - px('paddingBottom') : panel.clientHeight;
  // Board frame: coordinates + borders + padding = 33px wide, 35px tall; legend ≈ 24px.
  const cell = Math.max(n === 3 ? 48 : 14, Math.floor(Math.min(width - 33, height - 35 - 24) / n));
  panel.style.setProperty('--cell', `${cell}px`); panel.style.setProperty('--n', n);
  // Size the panel to the board so board + sidebar stay centred together.
  panel.style.flex = row ? `0 0 ${n * cell + 33}px` : '';
}
function showGame(open) {
  $('mainWindow').hidden = open; $('gameScreen').hidden = !open;
  if (open) fitBoard();
}
function leaveGame() {
  if (state.busy) return;
  showGame(false); showStep('mode', false);
  $(state.mode === 'pvp' ? 'pvpBtn' : 'pveBtn').focus();
}
function syncBusy() {
  for (const id of ['pvpBtn', 'pveBtn', 'restartBtn', 'gameBack', 'closeGame', 'levelSelect', 'sizeSelect', 'confirmStart', 'restartConfirm']) $(id).disabled = state.busy;
  $('board').setAttribute('aria-busy', String(state.busy));
}
function buildBoard(size) {
  state.n = size; state.focus = Math.floor(size * size / 2);
  for (const id of ['topCoords', 'leftCoords', 'board']) $(id).replaceChildren();
  $('boardWrap').dataset.size = size;
  $('board').setAttribute('aria-label', `Bàn cờ Caro ${size} nhân ${size}`);
  for (let n = 1; n <= size; n++) {
    for (const id of ['topCoords', 'leftCoords']) { const span = document.createElement('span'); span.textContent = n; $(id).append(span); }
  }
  fitBoard();
  for (let row = 0; row < size; row++) {
    const rowEl = document.createElement('div'); rowEl.className = 'board-row'; rowEl.setAttribute('role', 'row');
    for (let col = 0; col < size; col++) {
      const cell = document.createElement('button'); cell.type = 'button'; cell.className = 'cell'; cell.setAttribute('role', 'gridcell');
      cell.tabIndex = row * size + col === state.focus ? 0 : -1;
      cell.addEventListener('click', () => move(row, col));
      cell.addEventListener('keydown', event => {
        const deltas = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
        if (!deltas[event.key]) return;
        event.preventDefault(); const [dr, dc] = deltas[event.key];
        const r = Math.max(0, Math.min(size - 1, row + dr)), c = Math.max(0, Math.min(size - 1, col + dc));
        state.focus = r * size + c;
        document.querySelectorAll('.cell').forEach((el, i) => { el.tabIndex = i === state.focus ? 0 : -1; if (i === state.focus) el.focus(); });
      });
      rowEl.append(cell);
    }
    $('board').append(rowEl);
  }
}
function render() {
  syncBusy(); const game = state.game; if (!game) return;
  const pve = game.mode === 'pve', finished = !!game.winner, n = game.size, small = n === 3;
  if (state.n !== n) buildBoard(n);
  $('sizePicker').hidden = !pve; $('sizeSelect').value = String(n);
  (small ? RULE_3 : RULE_15).forEach((html, i) => { $(['ruleTitle', 'ruleMarks', 'ruleText'][i]).innerHTML = html; });
  $('modeLabel').textContent = pve ? 'NGƯỜI vs AI' : 'NGƯỜI vs NGƯỜI';
  $('starterLabel').textContent = `Bốc thăm: ${pve ? (game.starter === 'X' ? 'bạn' : 'AI') : game.starter} đi trước`;
  $('playerXName').textContent = pve ? 'Bạn' : 'Người chơi X';
  $('playerOName').textContent = pve ? 'Máy tính' : 'Người chơi O';
  const [levelName, depth, seconds] = LEVELS[state.level];
  $('levelPicker').hidden = !pve; $('levelSelect').value = state.level;
  $('levelHint').textContent = small ? SMALL_HINTS[state.level] : `Độ sâu ${depth} · ${seconds} giây`;
  $('oDetail').textContent = pve ? `${game.llm_enabled && !small ? 'Minimax + LLM' : 'Minimax'} · ${levelName}` : 'Quân O';
  $('playerX').classList.toggle('active', !finished && game.turn === 'X');
  $('playerO').classList.toggle('active', !finished && game.turn === 'O');
  const wins = new Set((game.win_cells || []).map(([r, c]) => r * n + c));
  document.querySelectorAll('.cell').forEach((cell, i) => {
    const row = Math.floor(i / n), col = i % n, mark = game.board[row][col];
    cell.textContent = mark === '.' ? '' : mark;
    cell.className = `cell ${mark === '.' ? '' : mark}${game.last_move?.[0] === row && game.last_move?.[1] === col ? ' last' : ''}${wins.has(i) ? ' winning' : ''}`;
    cell.setAttribute('aria-disabled', String(state.busy || finished || mark !== '.' || (pve && game.turn !== 'X')));
    cell.setAttribute('aria-label', `Hàng ${row + 1}, cột ${col + 1}, ${mark === '.' ? 'trống' : mark}${wins.has(i) ? ', chuỗi thắng' : ''}`);
  });
  $('moveCount').textContent = `${game.moves} / ${n * n} nước`;
  const symbol = $('turnSymbol'), status = $('statusText'), sub = $('statusSub');
  symbol.className = `turn-symbol ${game.turn.toLowerCase()}`;
  if (game.winner === 'draw') { symbol.textContent = '='; status.textContent = 'Hòa rồi!'; sub.textContent = 'Bàn cờ đã đầy. Thử lại một ván nữa nhé.'; }
  else if (finished) { symbol.textContent = game.winner; status.textContent = pve ? (game.winner === 'X' ? 'Bạn chiến thắng!' : 'Máy tính thắng!') : `${game.winner} chiến thắng!`; sub.textContent = `${small ? 'Đủ 3' : 'Đúng 5'} quân liên tiếp. Chọn Ván mới để chơi tiếp.`; }
  else if (state.counting) { symbol.textContent = game.turn; status.textContent = 'Chuẩn bị…'; sub.textContent = 'Ván đấu sắp bắt đầu.'; }
  else if (state.busy && pve && game.turn === 'O') { symbol.textContent = '⋯'; symbol.classList.add('thinking'); status.textContent = 'AI đang suy nghĩ'; sub.textContent = 'Đang tìm nước đi tốt nhất…'; }
  else if (pve && game.turn === 'O') { symbol.textContent = 'O'; status.textContent = 'Đến lượt AI'; sub.textContent = 'Nhấn thử lại để tiếp tục ván đấu.'; }
  else { symbol.textContent = game.turn; status.textContent = pve ? 'Đến lượt bạn' : `Đến lượt ${game.turn}`; sub.textContent = state.busy ? 'Đang ghi nhận nước đi…' : 'Chọn một ô trống để đánh.'; }
  $('retryAiBtn').hidden = state.busy || finished || !pve || game.turn !== 'O';
  $('aiNote').hidden = !pve; $('aiNote').textContent = game.ai_note || (game.llm_enabled && !small ? 'Đã kết nối cấu hình LLM.' : 'AI sẵn sàng chơi offline.');
  $('gameFooter').textContent = finished ? 'Ván đấu đã kết thúc' : state.counting ? 'Ván đấu sắp bắt đầu…' : state.busy ? 'Đang xử lý nước đi…' : 'Chúc bạn có một ván cờ vui!';
  $('gameDot').classList.toggle('busy', state.busy);
}
async function aiTurn() {
  if (state.game.mode === 'pve' && state.game.turn === 'O' && !state.game.winner) {
    render();
    const thinking = sleep(AI_MIN_DELAY + Math.random() * AI_JITTER);
    const next = await api(`/api/game/${state.game.id}/ai`, { revision: state.game.moves, level: state.level });
    await thinking; state.game = next; render();
  }
}
async function recover(error) {
  toast(error.message);
  if (state.game) {
    try { state.game = await api(`/api/game/${state.game.id}`); } catch { /* Keep the last confirmed board and show the error. */ }
  }
}
// 3 → 2 → 1 → who moves first (e.g. "BẠN ĐI TRƯỚC") in a small XP dialog;
// resolves when the game may start. The starter is only revealed at the end.
async function countdown() {
  const game = state.game, number = $('countdownNumber');
  const first = game.mode === 'pve' ? (game.starter === 'X' ? 'Bạn đi trước' : 'Máy đi trước') : `${game.starter} đi trước`;
  $('countdownSub').textContent = `Bàn ${game.size} × ${game.size}${game.mode === 'pve' ? ` · Độ khó ${LEVELS[state.level][0]}` : ' · Hai người chơi'}`;
  $('countdownLabel').textContent = 'VÁN ĐẤU BẮT ĐẦU SAU';
  const show = (text, mark = '') => {
    number.textContent = text; number.className = `countdown-number${mark ? ` go ${mark}` : ''}`;
    void number.offsetWidth; number.classList.add('pop');
  };
  state.counting = true; render();
  $('countdownDialog').showModal();
  for (const n of [3, 2, 1]) { show(String(n)); await sleep(1000); }
  $('countdownLabel').textContent = 'BỐC THĂM LƯỢT ĐI ĐẦU';
  show(first.toUpperCase(), game.starter.toLowerCase()); await sleep(1200);
  $('countdownDialog').close();
  state.counting = false;
}
async function newGame(mode) {
  if (state.busy) return;
  state.busy = true; syncBusy();
  try {
    state.game = await api('/api/game', mode === 'pve' ? { mode, level: state.level, size: state.size } : { mode }); state.mode = mode;
    const entering = $('gameScreen').hidden;
    if (entering) showGame(true);
    render();
    await countdown();
    document.querySelector('.cell[tabindex="0"]')?.focus();
    await aiTurn();
  } catch (error) { await recover(error); }
  finally {
    if ($('countdownDialog').open) $('countdownDialog').close();
    state.counting = false; state.busy = false; render();
  }
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
$('levelSelect').onchange = event => {
  state.level = LEVELS[event.target.value] ? event.target.value : 'hard';
  try { localStorage.setItem('caroLevel', state.level); } catch { /* The choice still applies to this session. */ }
  render(); toast(`Độ khó: ${LEVELS[state.level][0]} — áp dụng từ nước tiếp theo của AI.`);
};
// "Ván mới" and changing the board size mid-game both ask before discarding the game.
let restartSize = 15;
function askRestart(size) {
  const game = state.game;
  if (!game || state.busy) return;
  restartSize = size; const pve = game.mode === 'pve';
  $('restartLead').textContent = game.winner ? 'Chơi thêm một ván?' : 'Bắt đầu một ván mới?';
  $('restartNote').textContent = game.winner ? 'Lượt đi đầu sẽ được bốc thăm lại.' : 'Ván đang chơi sẽ bị hủy và không được lưu lại.';
  $('restartMode').textContent = pve ? 'Người vs Máy' : 'Người vs Người';
  $('restartSize').textContent = `${size} × ${size}${size !== game.size ? ' (đổi bàn)' : ''}`;
  $('restartLevelLabel').hidden = $('restartLevel').hidden = !pve;
  $('restartLevel').textContent = LEVELS[state.level][0];
  $('restartDialog').showModal(); $('restartConfirm').focus();
}
function cancelRestart() {
  $('restartDialog').close();
  if (state.game) $('sizeSelect').value = String(state.game.size);
  $('restartBtn').focus();
}
$('restartConfirm').onclick = () => {
  if (state.busy) return;
  if (state.mode === 'pve' && restartSize !== state.size) {
    state.size = restartSize;
    try { localStorage.setItem('caroSize', String(state.size)); } catch { /* The choice still applies to this session. */ }
  }
  $('restartDialog').close();
  newGame(state.mode);
};
$('restartCancel').onclick = $('restartClose').onclick = cancelRestart;
$('restartDialog').addEventListener('cancel', event => { event.preventDefault(); cancelRestart(); });
$('countdownDialog').addEventListener('cancel', event => event.preventDefault());
$('sizeSelect').onchange = event => askRestart(event.target.value === '3' ? 3 : 15);
// PVE setup: board size, then difficulty, then a confirmation dialog.
const LEVEL_COPY = {
  15: { easy: 'Phù hợp để làm quen với luật đúng 5.', medium: 'Máy phòng thủ chắc và biết phản công.', hard: 'Máy tìm sâu nhất, khó bị bắt bài.' },
  3: { easy: 'Máy chỉ thấy nước thắng ngay trước mắt.', medium: 'Máy biết chặn, nhưng thua nếu bạn tạo thế đôi.', hard: 'Máy duyệt toàn bộ cây — không thể thắng được máy.' },
};
const setup = { size: state.size, level: state.level };
const STEPS = { mode: ['stepMode', 'modeHeading'], size: ['stepSize', 'sizeHeading'], level: ['stepLevel', 'levelHeading'] };
function showStep(step, focus = true) {
  for (const [name, [id]] of Object.entries(STEPS)) $(id).hidden = name !== step;
  $('modeSection').setAttribute('aria-labelledby', STEPS[step][1]);
  if (focus) {
    const target = step === 'size' ? `[data-size="${setup.size}"]` : step === 'level' ? `[data-level="${setup.level}"]` : '#pveBtn';
    document.querySelector(`#${STEPS[step][0]} ${target}`)?.focus();
  }
}
function fillLevelStep() {
  $('levelHeading').textContent = `Chọn độ khó · Bàn ${setup.size} × ${setup.size}`;
  document.querySelectorAll('#stepLevel [data-level]').forEach(button => {
    const level = button.dataset.level, [, depth, seconds] = LEVELS[level];
    button.querySelector('small').textContent = (setup.size === 3 ? SMALL_HINTS[level] : `Độ sâu ${depth} · ${seconds} giây`).toUpperCase();
    button.querySelector('.mode-copy > span').textContent = LEVEL_COPY[setup.size][level];
  });
}
function openConfirm() {
  const small = setup.size === 3, level = setup.level;
  $('confirmSize').textContent = `${setup.size} × ${setup.size} (${setup.size * setup.size} ô)`;
  $('confirmRule').textContent = small ? 'Đủ 3 quân ngang, dọc hoặc chéo' : 'Đúng 5 quân liên tiếp';
  $('confirmLevel').textContent = `${LEVELS[level][0]} · ${small ? SMALL_HINTS[level] : `độ sâu ${LEVELS[level][1]}`}`;
  $('confirmDialog').showModal(); $('confirmStart').focus();
}
function closeConfirm() {
  if (state.busy) return;
  $('confirmDialog').close();
  document.querySelector(`#stepLevel [data-level="${setup.level}"]`)?.focus();
}
$('pveBtn').onclick = () => { setup.size = state.size; setup.level = state.level; showStep('size'); };
document.querySelectorAll('#stepSize [data-size]').forEach(button => button.onclick = () => {
  setup.size = Number(button.dataset.size); fillLevelStep(); showStep('level');
});
document.querySelectorAll('#stepLevel [data-level]').forEach(button => button.onclick = () => {
  setup.level = button.dataset.level; openConfirm();
});
$('sizeBack').onclick = () => showStep('mode');
$('levelBack').onclick = () => showStep('size');
$('modeSection').addEventListener('keydown', event => {
  if (event.key !== 'Escape') return;
  if (!$('stepSize').hidden) showStep('mode'); else if (!$('stepLevel').hidden) showStep('size');
});
$('confirmBack').onclick = $('confirmClose').onclick = closeConfirm;
$('confirmDialog').addEventListener('cancel', event => { event.preventDefault(); closeConfirm(); });
$('confirmStart').onclick = async () => {
  if (state.busy) return;
  state.size = setup.size; state.level = setup.level;
  try { localStorage.setItem('caroSize', String(state.size)); localStorage.setItem('caroLevel', state.level); } catch { /* The choice still applies to this session. */ }
  $('confirmDialog').close();
  await newGame('pve');
  // Back on the menu after the game the player starts from the mode choice again.
  if (!$('gameScreen').hidden) showStep('mode', false);
  else document.querySelector(`#stepLevel [data-level="${setup.level}"]`)?.focus();
};
$('pvpBtn').onclick = () => newGame('pvp');
$('restartBtn').onclick = () => askRestart(state.game?.size ?? 15);
$('closeGame').onclick = $('gameBack').onclick = leaveGame;
document.addEventListener('keydown', event => {
  // Escape leaves the game screen, as closing the old game dialog did.
  if (event.key === 'Escape' && !$('gameScreen').hidden && !document.querySelector('dialog[open]') && event.target.tagName !== 'SELECT') leaveGame();
});
new ResizeObserver(fitBoard).observe(document.querySelector('#gameScreen .game-content'));
$('helpBtn').onclick = () => { if ($('stepMode').hidden) showStep('mode', false); $('rulesDetails').open = !$('rulesDetails').open; };
$('minimizeBtn').onclick = () => window.pywebview?.api?.minimize?.();
buildBoard(15);
api('/api/config').then(config => {
  $('engineStatus').textContent = config.llm_configured ? 'Sẵn sàng · Minimax + Claude' : 'Sẵn sàng · AI offline';
}).catch(error => toast(error.message));
