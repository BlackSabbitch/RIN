#!/bin/bash
# Скрипт для сборки РИНциклопедии

set -e

mkdir -p build out

echo "🔨 Пытаюсь скомпилировать РИНциклопедию..."

if command -v xelatex &> /dev/null; then
    echo "✅ Найден xelatex, используем его..."
    # Два прохода: оглавление печатается по .toc с предыдущего запуска,
    # поэтому после добавления/переименования глав нужен второй проход.
    xelatex -interaction=nonstopmode -output-directory=build main.tex > /dev/null 2>&1 || true
    xelatex -interaction=nonstopmode -output-directory=build main.tex 2>&1 | grep -E "(Output|Error|Fatal)" || true
    cp build/main.pdf out/main.pdf
    echo "✅ PDF готов: out/main.pdf (также скопирован в build/main.pdf)"

elif command -v lualatex &> /dev/null; then
    echo "✅ Найден lualatex, используем его..."
    lualatex -interaction=nonstopmode -output-directory=build main.tex > /dev/null 2>&1 || true
    lualatex -interaction=nonstopmode -output-directory=build main.tex 2>&1 | grep -E "(Output|Error|Fatal)" || true
    cp build/main.pdf out/main.pdf
    echo "✅ PDF готов: out/main.pdf (также скопирован в build/main.pdf)"

elif command -v pdflatex &> /dev/null; then
    echo "⚠️  xelatex не найден, пытаюсь pdflatex..."
    pdflatex -interaction=nonstopmode -output-directory=build main.tex > /dev/null 2>&1 || true
    pdflatex -interaction=nonstopmode -output-directory=build main.tex 2>&1 | grep -E "(Output|Error|Fatal)" || true
    cp build/main.pdf out/main.pdf
    echo "✅ PDF готов: out/main.pdf (также скопирован в build/main.pdf)"
    
else
    echo "❌ Не найден ни xelatex, ни lualatex, ни pdflatex"
    echo "Установите: sudo apt-get install texlive-xetex texlive-lang-cyrillic"
    exit 1
fi

echo ""
echo "Проверяем результат..."
if [ -f out/main.pdf ]; then
    SIZE=$(du -h out/main.pdf | cut -f1)
    echo "✅ Успех! PDF размер: $SIZE"
    ls -lh out/main.pdf
else
    echo "❌ Ошибка компиляции. Проверьте build/main.log"
    tail -50 build/main.log
    exit 1
fi
