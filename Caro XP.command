#!/bin/zsh
cd "${0:A:h}" || exit 1
if [[ ! -x .venv/bin/python ]]; then
  print 'Chưa có môi trường Python. Hãy làm theo README.md để cài đặt.'
  read '?Nhấn Enter để đóng…'
  exit 1
fi
.venv/bin/python desktop.py
