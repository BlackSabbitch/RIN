# РИНциклопедия — LaTeX Проект

Курс лекций по конструированию персонажа и сценарию локального AI-компаньона RIN.

## Структура

```
rinencyclopedia/
├── main.tex              # Главный файл LaTeX
├── chapters/              # Один файл — один подраздел оглавления
│   ├── 0_1.tex .. 0_6.tex  # Глава 0 (✅ готово)
│   ├── 2_6.tex, 2_7.tex    # Глава 2, частично (2.1–2.5 ещё не написаны)
│   └── 3_1.tex             # Глава 3, частично (3.2–3.10 ещё не написаны)
├── references_log.md     # Рабочий журнал внешних референсов → будущий 14.8
├── images/               # Папка для изображений
├── build/                # Папка для скомпилированных PDF
└── README.md             # Этот файл
```

Файлы называются по номеру подраздела из общего оглавления (`4_8.tex` = 4.8).
Файл, открывающий главу верхнего уровня, начинается с
`\setcounter{chapter}{N-1}` и `\chapter{...}`; остальные подразделы той же
главы — просто `\section{...}` без `\chapter`. Если между уже написанными
подразделами есть пропуск (например, глава начинается сразу с X.6), первый
написанный файл дополнительно ставит `\setcounter{section}{X-1}` перед
`\section`, чтобы нумерация в PDF совпадала с оглавлением.

## Компиляция (выбирайте один способ)

### ✅ Способ 1: XeLaTeX (РЕКОМЕНДУЕТСЯ)
```bash
cd rinencyclopedia
mkdir -p build
xelatex -interaction=nonstopmode -output-directory=build main.tex
```

Если ошибка `Unknown option 'russian'`:
```bash
xelatex -no-pdf -interaction=nonstopmode -output-directory=build main.tex
xdvipdfmx -o build/main.pdf build/main.xdv
```

### Способ 2: LuaLaTeX
```bash
mkdir -p build
lualatex -interaction=nonstopmode -output-directory=build main.tex
```

### Способ 3: pdfLaTeX (если других не работает)

Отредактируйте `main.tex` — **замените эти строки**:
```latex
\usepackage{fontspec}
\usepackage[russian]{babel}
\setmainfont{DejaVu Sans}
```

На эти:
```latex
\usepackage[utf8]{inputenc}
\usepackage[T2A]{fontenc}
\usepackage[russian]{babel}
```

Затем компилируйте:
```bash
pdflatex -interaction=nonstopmode -output-directory=build main.tex
```

## Проверка установки

```bash
# Есть ли xelatex?
xelatex --version

# Есть ли русские шрифты?
fc-list | grep -i dejavu
```

## Если не компилируется

1. **Проверьте пути**:
   ```bash
   ls -la chapters/
   ```
   Должны быть файлы: `behavioral_patterns.tex`, `narrative_function.tex`, `attachment_modes.tex`

2. **Проверьте кодировку** (все файлы должны быть UTF-8):
   ```bash
   file main.tex chapters/*.tex
   ```

3. **Очистите build директорию** и пересоберите:
   ```bash
   rm -rf build && mkdir -p build && xelatex -interaction=nonstopmode -output-directory=build main.tex
   ```

4. **Проверьте логи ошибок**:
   ```bash
   cat build/main.log | tail -50
   ```

## Результат

✅ PDF появится в: `build/main.pdf`
