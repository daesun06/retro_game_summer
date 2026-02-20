# Retro Game Summer - Setup Instructions

## Prerequisites

Before proceeding, ensure you have the following installed on your system:
- **Git**: [https://git-scm.com/](https://git-scm.com/)
- **Python**: Version 3.8 or higher ([https://www.python.org/](https://www.python.org/))
- **pip**: Usually comes with Python (verify with `python -m pip --version`)

---

## 1. Cloning and Pulling the Repository

### Initial Clone (First Time Setup)

Clone the repository to your local machine:

```bash
git clone https://github.com/daesun06/retro_game_summer.git
cd retro_game_summer
```

### Pulling the Latest Changes from q_learning Branch

This project uses the `q_learning` branch. First, switch to this branch:

```bash
git checkout q_learning
git pull origin q_learning
```

Or in one command (newer Git versions):

```bash
git switch q_learning
git pull origin q_learning
```

### Checking Your Current Branch

To see which branch you're currently on:

```bash
git branch
```

The current branch will be marked with an asterisk (`*`). You should see `q_learning` listed.

### Using GitKraken to Switch Branches

If you prefer a graphical interface, you can use GitKraken:

1. Open **GitKraken**
2. Click **File** > **Open Repository** and select your project folder
3. In the left sidebar under **Branches**, find and right-click on **q_learning**
4. Select **Checkout q_learning**
5. Click the **Pull** button (or use the keyboard shortcut) to fetch the latest changes

Alternatively, click on the **q_learning** branch and select **Pull** from the toolbar.

---

## 2. Installing Poetry Using pipx

Poetry is a dependency management and packaging tool for Python. Using `pipx` ensures Poetry is installed in an isolated environment and available globally.

### Installing pipx

#### Windows
```bash
python -m pip install --user pipx
python -m pipx ensurepath
```

After running these commands, **restart your terminal** for the changes to take effect.

#### macOS
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

Or using Homebrew (if installed):
```bash
brew install pipx
pipx ensurepath
```

#### Linux
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

Or using your package manager:

**Ubuntu/Debian:**
```bash
sudo apt-get install pipx
pipx ensurepath
```

**Fedora:**
```bash
sudo dnf install pipx
pipx ensurepath
```

**Arch:**
```bash
sudo pacman -S python-pipx
pipx ensurepath
```

### Installing Poetry via pipx

Once `pipx` is installed, install Poetry:

#### Windows, macOS, and Linux
```bash
pipx install poetry
```

### Verifying Poetry Installation

Check if Poetry is correctly installed:

```bash
poetry --version
```

You should see output similar to: `Poetry (version 1.7.0)`

---

## 3. Installing Project Dependencies Using Poetry

Once Poetry is installed and you're in the project directory, follow these steps:

### Step 1: Install All Dependencies

```bash
poetry install
```

This command will:
- Read the `pyproject.toml` file
- Download and install all required dependencies
- Create a virtual environment for the project
- Generate a `poetry.lock` file (if it doesn't exist)

### Step 2: Verify Installation

To confirm all dependencies are installed correctly:

```bash
poetry show
```

This displays all installed packages and their versions.

### Step 3: Running the Project

To run the project within the Poetry environment, use:

```bash
poetry run python <script_name>.py
```

Or for this specific project:

```bash
poetry run pgzrun bunner-master/main.py
```

### Step 4: Activating the Virtual Environment (Optional)

If you want to work directly inside the Poetry virtual environment:

```bash
poetry env activate
```

Once activated, your terminal prompt will change to indicate you're in the virtual environment. You can then run Python commands directly:

```bash
python script_name.py
pgzrun bunner-master/main.py
```

To exit the virtual environment, type:

```bash
exit
```

### Adding New Dependencies

If you need to install additional packages:

```bash
poetry add <package_name>
```

### Updating Dependencies

To update all dependencies to their latest versions:

```bash
poetry update
```

---

## Quick Start Summary

```bash
# 1. Install pipx (one-time setup)
python -m pip install --user pipx
python -m pipx ensurepath

# 2. Install Poetry (one-time setup)
pipx install poetry

# 3. Clone the repository (first time only)
git clone https://github.com/daesun06/retro_game_summer.git
cd retro_game_summer

# 4. Switch to q_learning branch and pull latest changes
git checkout q_learning
git pull origin q_learning

# 5. Install project dependencies
poetry install

# 6. Run the project
poetry run pgzrun bunner-master/main.py
```

---

## Troubleshooting

### `poetry: command not found`
- Ensure you ran `pipx ensurepath` and **restarted your terminal**
- Check that pipx installation was successful with `pipx --version`

### `Git branch conflicts`
If you encounter merge conflicts when pulling:
```bash
git status
```
Resolve conflicts manually, then:
```bash
git add .
git commit -m "Resolve merge conflicts"
```

### `Poetry virtual environment issues`
Rebuild the virtual environment:
```bash
poetry env remove <python_version>
poetry install
```

Find your Python version with:
```bash
poetry env list
```

---

## Additional Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [Git Documentation](https://git-scm.com/doc)
- [pipx Documentation](https://pipx.pypa.io/)

---

# - Инструкции по установке

## Предварительные требования

Перед началом убедитесь, что в вашей системе установлены следующие компоненты:
- **Git**: [https://git-scm.com/](https://git-scm.com/)
- **Python**: Версия 3.8 или выше ([https://www.python.org/](https://www.python.org/))
- **pip**: Обычно поставляется с Python (проверьте командой `python -m pip --version`)

---

## 1. Клонирование и получение обновлений репозитория

### Первоначальное клонирование (первая настройка)

Клонируйте репозиторий на ваш компьютер:

```bash
git clone https://github.com/daesun06/retro_game_summer.git
cd retro_game_summer
```

### Получение последних изменений из ветки q_learning

Этот проект использует ветку `q_learning`. Сначала переключитесь на эту ветку:

```bash
git checkout q_learning
git pull origin q_learning
```

Или одной командой (для новых версий Git):

```bash
git switch q_learning
git pull origin q_learning
```

### Проверка текущей ветки

Чтобы узнать, на какой ветке вы сейчас находитесь:

```bash
git branch
```

Текущая ветка будет отмечена звёздочкой (`*`). Вы должны увидеть `q_learning` в списке.

### Использование GitKraken для переключения веток

Если вы предпочитаете графический интерфейс, вы можете использовать GitKraken:

1. Откройте **GitKraken**
2. Нажмите **File** > **Open Repository** и выберите папку проекта
3. На левой боковой панели под **Branches** найдите и щёлкните правой кнопкой мыши на **q_learning**
4. Выберите **Checkout q_learning**
5. Нажмите кнопку **Pull** (или используйте сочетание клавиш) для получения последних изменений

Кроме того, вы можете щёлкнуть на ветку **q_learning** и выбрать **Pull** из панели инструментов.

---

## 2. Установка Poetry с помощью pipx

Poetry — это инструмент управления зависимостями и упаковки для Python. Использование `pipx` гарантирует, что Poetry устанавливается в изолированную среду и доступен глобально.

### Установка pipx

#### Windows
```bash
python -m pip install --user pipx
python -m pipx ensurepath
```

После выполнения этих команд **перезагрузите ваш терминал**, чтобы изменения вступили в силу.

#### macOS
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

Или используя Homebrew (если установлен):
```bash
brew install pipx
pipx ensurepath
```

#### Linux
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

Или используя менеджер пакетов вашего дистрибутива:

**Ubuntu/Debian:**
```bash
sudo apt-get install pipx
pipx ensurepath
```

**Fedora:**
```bash
sudo dnf install pipx
pipx ensurepath
```

**Arch:**
```bash
sudo pacman -S python-pipx
pipx ensurepath
```

### Установка Poetry через pipx

После установки `pipx` установите Poetry:

#### Windows, macOS и Linux
```bash
pipx install poetry
```

### Проверка установки Poetry

Проверьте, правильно ли установлена Poetry:

```bash
poetry --version
```

Вы должны увидеть вывод, похожий на: `Poetry (version 1.7.0)`

---

## 3. Установка зависимостей проекта с помощью Poetry

После установки Poetry и нахождения в директории проекта выполните следующие шаги:

### Шаг 1: Установка всех зависимостей

```bash
poetry install
```

Эта команда:
- Прочитает файл `pyproject.toml`
- Загрузит и установит все необходимые зависимости
- Создаст виртуальное окружение для проекта
- Сгенерирует файл `poetry.lock` (если его ещё нет)

### Шаг 2: Проверка установки

Чтобы убедиться, что все зависимости установлены корректно:

```bash
poetry show
```

Эта команда отображает все установленные пакеты и их версии.

### Шаг 3: Запуск проекта

Чтобы запустить проект в окружении Poetry, используйте:

```bash
poetry run python <имя_скрипта>.py
```

Или для этого конкретного проекта:

```bash
poetry run pgzrun bunner-master/main.py
```

### Шаг 4: Активация виртуального окружения (опционально)

Если вы хотите работать напрямую внутри виртуального окружения Poetry:

```bash
poetry env activate
```

После активации приглашение вашего терминала изменится, указывая, что вы находитесь в виртуальном окружении. Затем вы можете запускать команды Python напрямую:

```bash
python имя_скрипта.py
pgzrun bunner-master/main.py
```

Чтобы выйти из виртуального окружения, введите:

```bash
exit
```

### Добавление новых зависимостей

Если вам нужно установить дополнительные пакеты:

```bash
poetry add <имя_пакета>
```

### Обновление зависимостей

Чтобы обновить все зависимости до их последних версий:

```bash
poetry update
```

---

## Краткое резюме для быстрого запуска

```bash
# 1. Установите pipx (однократная настройка)
python -m pip install --user pipx
python -m pipx ensurepath

# 2. Установите Poetry (однократная настройка)
pipx install poetry

# 3. Клонируйте репозиторий (только в первый раз)
git clone https://github.com/daesun06/retro_game_summer.git
cd retro_game_summer

# 4. Переключитесь на ветку q_learning и получите последние изменения
git checkout q_learning
git pull origin q_learning

# 5. Установите зависимости проекта
poetry install

# 6. Запустите проект
poetry run pgzrun bunner-master/main.py
```

---

## Устранение неполадок

### `poetry: command not found`
- Убедитесь, что вы выполнили `pipx ensurepath` и **перезагрузили ваш терминал**
- Проверьте, что pipx установлен успешно, командой `pipx --version`

### `Конфликты при слиянии Git`
Если вы столкнулись с конфликтами при получении обновлений:
```bash
git status
```
Разрешите конфликты вручную, затем:
```bash
git add .
git commit -m "Разрешение конфликтов слияния"
```

### `Проблемы с виртуальным окружением Poetry`
Пересоздайте виртуальное окружение:
```bash
poetry env remove <версия_python>
poetry install
```

Найдите вашу версию Python с помощью:
```bash
poetry env list
```

---

## Дополнительные ресурсы

- [Документация Poetry](https://python-poetry.org/docs/)
- [Документация Git](https://git-scm.com/doc)
- [Документация pipx](https://pipx.pypa.io/)
