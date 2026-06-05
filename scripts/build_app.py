# -*- coding: utf-8 -*-
"""Удобный кроссплатформенный старт-пакет для запуска и сборки настольного приложения."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = ROOT / ".venv"
CACHE_DIR = ROOT / ".build-cache"
STATE_FILE = CACHE_DIR / "bootstrap_state.json"
REQUIREMENTS_FILE = ROOT / "requirements.txt"
WINDOWS_SPEC = ROOT / "file_analyzer.spec"   # описание сборки для Windows
MACOS_SPEC = ROOT / "file_analyzer_macos.spec"  # описание сборки для macOS
APP_ENTRYPOINT = ROOT / "run.py"
# имя пакета для pip -> имя модуля для import (они иногда различаются)
RUNTIME_MODULES = {
    "openpyxl": "openpyxl",
    "reportlab": "reportlab",
    "Pillow": "PIL",
}


def detect_target() -> dict[str, str]:
    """Detects the current host OS and architecture for the build."""
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Windows":
        if "arm" in machine:
            target = "windows-arm64"
        else:
            target = "windows-x64"
        spec = WINDOWS_SPEC
    elif system == "Darwin":
        target = "macos-arm64" if "arm" in machine else "macos-x64"
        spec = MACOS_SPEC
    else:
        raise RuntimeError(
            "Сборка поддерживается только на Windows и macOS."
        )

    return {
        "system": system,
        "machine": machine,
        "target": target,
        "spec": str(spec),
    }


def venv_python() -> Path:
    """Возвращает путь к исполняемому файлу Python в локальной виртуальной среде."""
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python3"


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    """Выполняет команду и генерирует исключение в случае сбоя, одновременно передавая вывод в потоковом режиме."""
    print("$", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd or ROOT, check=True)


def ensure_venv() -> Path:
    """Создает виртуальное окружение проекта, если оно еще не существует."""
    python_bin = venv_python()
    if python_bin.exists():
        return python_bin

    print("Создаю локальное окружение .venv ...")
    run([sys.executable, "-m", "venv", str(VENV_DIR)])
    return python_bin


def load_state() -> dict[str, str]:
    """Загружает сохраненное состояние bootstrap с диска."""
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state: dict[str, str]) -> None:
    """Сохраняет состояние начальной загрузки для следующего запуска."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def requirements_signature(*, include_builder: bool) -> str:
    """Создает небольшую сигнатуру, которая изменяется при изменении необходимых пакетов."""
    raw = REQUIREMENTS_FILE.read_text(encoding="utf-8")
    if include_builder:
        return f"{raw}\npyinstaller"
    return raw


def module_available(python_bin: Path, module_name: str) -> bool:
    """Проверяет, можно ли импортировать модуль внутри виртуальной среды."""
    # запускаем мини-скрипт внутри venv: код выхода 0 — модуль найден
    code = (
        "import importlib.util, sys; "
        f"sys.exit(0 if importlib.util.find_spec({module_name!r}) else 1)"
    )
    result = subprocess.run(
        [str(python_bin), "-c", code],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def missing_modules(python_bin: Path, *, include_builder: bool) -> list[str]:
    """Возвращает модули зависимостей, отсутствующие в подготовленной среде."""
    modules = list(RUNTIME_MODULES.values())
    if include_builder:
        modules.append("PyInstaller")
    return [module for module in modules if not module_available(python_bin, module)]


def ensure_dependencies(
    python_bin: Path,
    target: dict[str, str],
    *,
    include_builder: bool,
) -> None:
    """Устанавливает зависимости для среды выполнения или сборки только в том случае, если они устарели."""
    state = load_state()
    mode = "build" if include_builder else "run"
    signature = requirements_signature(include_builder=include_builder)
    cached_signature = state.get(f"{mode}_signature")  # что ставили в прошлый раз
    cached_target = state.get("target")
    missing = missing_modules(python_bin, include_builder=include_builder)

    # пропускаем установку, если состав пакетов и платформа не менялись,
    # и при этом ничего не пропало из окружения
    if (
        cached_signature == signature
        and cached_target == target["target"]
        and not missing
    ):
        print("Зависимости уже подготовлены, повторная установка не нужна.")
        return

    if missing:
        print("Не хватает модулей:", ", ".join(missing))
    print("Устанавливаю зависимости ...")
    run([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python_bin), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])
    if include_builder:
        run([str(python_bin), "-m", "pip", "install", "pyinstaller"])

    state["target"] = target["target"]
    state[f"{mode}_signature"] = signature
    save_state(state)


def clean_previous_builds() -> None:
    """Удаляет старые папки сборки перед новой сборкой."""
    for folder_name in ("build", "dist"):
        folder = ROOT / folder_name
        if folder.exists():
            shutil.rmtree(folder)


def build_application(python_bin: Path, target: dict[str, str]) -> None:
    """Создает приложение для рабочего стола для текущей хост-платформы."""
    spec_file = target["spec"]
    print(f"Собираю приложение для {target['target']} ...")
    clean_previous_builds()
    run([str(python_bin), "-m", "PyInstaller", spec_file])


def launch_application(python_bin: Path) -> None:
    """Запускает приложение из подготовленной виртуальной среды."""
    print("Запускаю приложение ...")
    run([str(python_bin), str(APP_ENTRYPOINT)])


def parse_args() -> argparse.Namespace:
    """Анализирует аргументы командной строки для режимов запуска."""
    parser = argparse.ArgumentParser(
        description="Удобный стартовый набор для запуска и настройки File Analyzer."
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("run", "build"),
        help="run: запустить приложение, build: собрать под текущую платформу",
    )
    return parser.parse_args()


def choose_command_interactively() -> str:
    """Запрашивает действие, выполняемое при запуске стартера без аргументов."""
    print("")
    print("Анализатор файлов · стартер")
    print("1. Запустить приложение")
    print("2. Собрать приложение под текущую платформу")
    print("")
    choice = input("Выберите действие [1]: ").strip() or "1"
    return {
        "1": "run",
        "2": "build",
        "run": "run",
        "build": "build",
    }.get(choice.lower(), "run")


def main() -> None:
    """Загружает среду, а затем запускает или упаковывает приложение."""
    if sys.version_info < (3, 10):
        raise RuntimeError("Нужен Python 3.10 или новее.")

    os.chdir(ROOT)
    args = parse_args()
    command = args.command or choose_command_interactively()
    target = detect_target()
    print(
        f"Платформа: {target['system']} | "
        f"архитектура: {target['machine']} | "
        f"таргет: {target['target']}"
    )
    python_bin = ensure_venv()
    ensure_dependencies(
        python_bin,
        target,
        include_builder=command == "build",
    )

    if command == "run":
        launch_application(python_bin)
    else:
        build_application(python_bin, target)
        print("Сборка завершена. Артефакты находятся в папке dist/.")


if __name__ == "__main__":
    main()
