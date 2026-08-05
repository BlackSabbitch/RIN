#!/bin/bash
# Сборка монографии «Конструирование графовой памяти Рин»
set -e
mkdir -p build out

echo "Пытаюсь скомпилировать монографию..."

if command -v xelatex &> /dev/null; then
    echo "Найден xelatex."
    xelatex -interaction=nonstopmode -output-directory=build main.tex > /dev/null 2>&1 || true
    xelatex -interaction=nonstopmode -output-directory=build main.tex 2>&1 | grep -E "(Output|Error|Fatal)" || true
    cp build/main.pdf out/main.pdf
    echo "PDF готов: out/main.pdf"
elif command -v lualatex &> /dev/null; then
    echo "Найден lualatex."
    lualatex -interaction=nonstopmode -output-directory=build main.tex > /dev/null 2>&1 || true
    lualatex -interaction=nonstopmode -output-directory=build main.tex 2>&1 | grep -E "(Output|Error|Fatal)" || true
    cp build/main.pdf out/main.pdf
    echo "PDF готов: out/main.pdf"
else
    echo "Не найден xelatex/lualatex."
    echo "Установите: sudo apt-get install texlive-xetex texlive-lang-cyrillic"
    exit 1
fi

if [ -f out/main.pdf ]; then
    echo "Успех. Размер: $(du -h out/main.pdf | cut -f1)"
else
    echo "Ошибка компиляции — смотрите build/main.log"
    tail -50 build/main.log
    exit 1
fi
