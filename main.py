# main.py
import asyncio
import signal
import sys
import os
from pathlib import Path
from utils import check_modules, show_loading_screen, cleanup_resources, logger, check_network_connectivity
from menu import run_menu

def signal_handler(sig, frame):
    """Обработчик сигналов для graceful shutdown."""
    logger.info("Получен сигнал прерывания. Завершение...")
    cleanup_resources()
    sys.exit(0)

if __name__ == "__main__":
    # Создание папок logs и images
    Path("logs").mkdir(exist_ok=True)
    Path("images").mkdir(exist_ok=True)
    
    # Регистрация обработчика сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        check_modules()
        if not check_network_connectivity():
            logger.warning("Сеть недоступна при запуске. Некоторые функции могут не работать.")
            print("⚠️  Предупреждение: Сеть недоступна.")
        show_loading_screen()
        asyncio.run(run_menu())
    except KeyboardInterrupt:
        logger.info("Основной цикл прерван пользователем")
    except asyncio.CancelledError:
        logger.info("Асинхронная задача отменена")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в main: {e}")
        print(f"❌ Критическая ошибка: {e}")
    finally:
        cleanup_resources()
        logger.info("Программа завершена.")