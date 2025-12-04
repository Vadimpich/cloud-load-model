# -*- coding: utf-8 -*-
"""
Точка входа в приложение моделирования облачного приложения с autoscaling.

Запускает GUI приложение на PyQt6.
"""

# Устанавливаем кодировку ДО всех импортов
import os
import sys
import io

# Критически важно установить это до импорта любых модулей
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Переопределяем open() для использования UTF-8 по умолчанию
# Это нужно для SimPy, который читает исходные файлы
try:
    import builtins
    _original_open = builtins.open
    
    def _utf8_open(file, mode='r', buffering=-1, encoding=None, errors=None, 
                   newline=None, closefd=True, opener=None):
        """Версия open() с UTF-8 по умолчанию."""
        if 'b' not in mode and encoding is None:
            encoding = 'utf-8'
        if errors is None and 'b' not in mode:
            errors = 'replace'
        return _original_open(file, mode, buffering, encoding, errors, newline, closefd, opener)
    
    builtins.open = _utf8_open
except Exception:
    pass  # Если не удалось, продолжаем без этого

import traceback
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.icon_creator import create_cloud_icon


def setup_console():
    """Настраивает консоль для вывода ошибок на Windows."""
    if sys.platform == 'win32':
        try:
            # Пытаемся открыть консоль для вывода
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # Выделяем консоль
            kernel32.AllocConsole()
            # Настраиваем кодировку консоли на UTF-8
            kernel32.SetConsoleOutputCP(65001)  # UTF-8
            kernel32.SetConsoleCP(65001)  # UTF-8
            # Перенаправляем stdout и stderr с правильной кодировкой
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, 
                encoding='utf-8', 
                errors='replace',
                line_buffering=True
            )
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, 
                encoding='utf-8', 
                errors='replace',
                line_buffering=True
            )
            print("Консоль отладки активирована (UTF-8)")
        except Exception as e:
            # Если не удалось, просто перенаправляем с правильной кодировкой
            try:
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer, 
                    encoding='utf-8', 
                    errors='replace',
                    line_buffering=True
                )
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer, 
                    encoding='utf-8', 
                    errors='replace',
                    line_buffering=True
                )
                print(f"Консоль настроена (без AllocConsole): {e}")
            except:
                pass


def excepthook(exc_type, exc_value, exc_traceback):
    """Обработчик необработанных исключений."""
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("=" * 80)
    print("НЕОБРАБОТАННОЕ ИСКЛЮЧЕНИЕ:")
    print("=" * 80)
    print(error_msg)
    print("=" * 80)
    
    # Также показываем в GUI, если приложение уже создано
    try:
        from PyQt6.QtWidgets import QMessageBox
        app = QApplication.instance()
        if app:
            QMessageBox.critical(
                None, 
                "Критическая ошибка", 
                f"Произошла критическая ошибка:\n\n{str(exc_value)}\n\n"
                f"Подробности в консоли."
            )
    except:
        pass


def main():
    """Главная функция приложения."""
    
    # Настраиваем консоль для отладки
    setup_console()
    
    # Устанавливаем обработчик исключений
    sys.excepthook = excepthook
    
    # Устанавливаем кодировку по умолчанию
    import locale
    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        pass
    
    try:
        # Создаем приложение PyQt
        app = QApplication(sys.argv)
        
        # Устанавливаем иконку приложения
        app_icon = create_cloud_icon(64)
        app.setWindowIcon(app_icon)
        
        # Устанавливаем стиль приложения
        app.setStyle('Fusion')
        
        # Создаем и показываем главное окно
        window = MainWindow()
        window.show()
        
        print("Приложение запущено успешно")
        
        # Запускаем цикл обработки событий
        sys.exit(app.exec())
    except Exception as e:
        error_msg = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        print("=" * 80)
        print("ОШИБКА ПРИ ЗАПУСКЕ:")
        print("=" * 80)
        print(error_msg)
        print("=" * 80)
        raise


if __name__ == '__main__':
    main()

