# utils.py
import os
import csv
import json
import time
import logging
import socket
from datetime import datetime
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path
from urllib.parse import urlparse
import asyncio

# Настройка логирования в папку logs
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"ddos_tester_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_modules():
    """Проверка всех необходимых модулей при запуске (без scapy)."""
    required_modules = [
        'asyncio',
        'aiohttp',
        'ping3',
        'concurrent.futures',
        'tqdm',
        'matplotlib'
    ]
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError as e:
            missing.append(module)
            logger.warning(f"Модуль {module} не найден: {e}")
    if missing:
        logger.error(f"Отсутствуют модули: {', '.join(missing)}. Установите их с помощью pip install {' '.join(missing)}.")
        print(f"❌ Отсутствуют модули: {', '.join(missing)}")
        sys.exit(1)
    logger.info("Все модули успешно проверены.")

def show_loading_screen():
    """Показ загрузки скрипта при запуске с улучшенным дизайном."""
    try:
        print("\n" + "═"*50)
        print("          🚀 Инициализация DDoS-ТЕСТЕР v4.0... 🚀")
        print("═"*50)
        for i in range(11):
            bar = "█" * i + "░" * (10 - i)
            progress = f"[{bar}] {i*10}%"
            print(f"\r{progress}", end='', flush=True)
            time.sleep(0.15)
        print("\n✅ Инициализация завершена! Запуск меню...\n")
    except Exception as e:
        logger.error(f"Ошибка при показе загрузки: {e}")

def validate_input(value: str, type_check: callable, min_val: int = 0, max_val: Optional[int] = None, error_msg: str = "Неверный ввод.") -> Optional[Any]:
    """Углубленная валидация ввода пользователя."""
    try:
        val = type_check(value.strip())
        if val < min_val:
            raise ValueError(f"Значение должно быть >= {min_val}.")
        if max_val and val > max_val:
            raise ValueError(f"Значение должно быть <= {max_val}.")
        return val
    except ValueError as e:
        logger.warning(f"{error_msg}: {e}")
        print(f"❌ {error_msg} {e}")
        return None

def validate_ip(ip_str: str) -> bool:
    """Валидация IP адреса."""
    try:
        socket.inet_aton(ip_str)
        return True
    except socket.error:
        logger.warning(f"Неверный IP: {ip_str}")
        return False

def validate_url(url: str) -> bool:
    """Валидация URL."""
    parsed = urlparse(url)
    is_valid = bool(parsed.scheme in ['http', 'https'] and parsed.netloc)
    if not is_valid:
        logger.warning(f"Неверный URL: {url}")
    return is_valid

def is_root() -> bool:
    """Проверка root привилегий."""
    try:
        return os.getuid() == 0
    except AttributeError:
        # Windows
        return True  # Нет строгой проверки

def save_results_to_file(results: List[Dict[str, Any]], filename: Optional[str] = None) -> bool:
    """Сохранение результатов в CSV-файл."""
    try:
        if not results:
            logger.warning("Нет результатов для сохранения.")
            return False
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ddos_test_results_{timestamp}.csv"
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = set().union(*(r.keys() for r in results))
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        logger.info(f"Результаты сохранены в {filename}")
        print(f"✅ Сохранено в {filename}")
        return True
    except (IOError, OSError, KeyError) as e:
        logger.error(f"Ошибка при сохранении в CSV: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при сохранении: {e}")
        return False

def load_config_from_file(filename: str = "config.json") -> Dict[str, Any]:
    """Загрузка конфигурации из JSON-файла."""
    try:
        if not os.path.exists(filename):
            logger.warning(f"Файл конфигурации {filename} не найден. Используется пустая конфигурация.")
            return {}
        with open(filename, 'r', encoding='utf-8') as f:
            config = json.load(f)
            if 'max_requests' in config and not isinstance(config['max_requests'], int):
                del config['max_requests']
                logger.warning("Неверный параметр в конфиге: max_requests")
            logger.info(f"Конфигурация загружена из {filename}")
            return config
    except (json.JSONDecodeError, IOError, OSError) as e:
        logger.error(f"Ошибка при загрузке конфигурации: {e}")
        return {}
    except Exception as e:
        logger.error(f"Неожиданная ошибка при загрузке конфигурации: {e}")
        return {}

def generate_report(results: List[Dict[str, Any]]) -> str:
    """Генерация текстового отчета."""
    try:
        if not results:
            return "❌ Нет результатов для отчета."
        total = len(results)
        successful = sum(1 for r in results if r.get("status") in [200, "success", "sent", "held", "amplified", "held_timeout", "slow_read"])
        failed = total - successful
        times = [r["time"] for r in results if r["time"] is not None and r["time"] > 0]
        avg_time = sum(times) / len(times) if times else 0
        total_size = sum(r.get("size", 0) for r in results)
        amps = [r.get("amp", 0) for r in results if r.get("amp")]
        avg_amp = sum(amps) / len(amps) if amps else 0
        report = f"""📊 Подробный отчет по тесту:
Всего запросов: {total}
Успешных: {successful}
Неуспешных: {failed}
Среднее время: {avg_time:.3f} сек
Общий трафик: {total_size / 1024:.2f} KB
Коэффициент усиления (если применимо): {avg_amp:.2f}x

Ошибки: {failed}
"""
        if failed > 0:
            report += "\nПримеры ошибок:\n"
            errors = [r.get("error", "") for r in results if r.get("error")]
            report += "\n".join(errors[:3])
        logger.info("Отчет сгенерирован.")
        return report
    except Exception as e:
        logger.error(f"Ошибка при генерации отчета: {e}")
        return "❌ Ошибка при генерации отчета."

def plot_results(results: List[Dict[str, Any]]):
    """Построение графика результатов с matplotlib в папку images."""
    try:
        if not results:
            logger.warning("Нет результатов для графика.")
            return
        import matplotlib.pyplot as plt
        import numpy as np
        times = np.array([r["time"] for r in results if r["time"] is not None])
        indices = np.arange(len(times))
        statuses = [r.get("status", "unknown") for r in results if r["time"] is not None]
        plt.figure(figsize=(12, 6))
        colors = {'success': 'green', 'sent': 'blue', 'held': 'orange', 'amplified': 'red', 'timeout': 'gray', 'slow_read': 'purple'}
        for status, color in colors.items():
            mask = np.array([s == status for s in statuses])
            if np.any(mask):
                plt.scatter(indices[mask], times[mask], c=color, label=status, alpha=0.6)
        plt.xlabel('Запрос')
        plt.ylabel('Время (сек)')
        plt.title('Время ответа запросов по статусам')
        plt.legend()
        plt.grid(True, alpha=0.3)
        img_dir = Path("images")
        img_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = img_dir / f"test_plot_{timestamp}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.show()
        logger.info(f"График сохранен как {filename}")
        print(f"📈 График сохранен: {filename}")
    except ImportError:
        logger.error("Matplotlib не установлен для графиков.")
        print("❌ Matplotlib не установлен.")
    except Exception as e:
        logger.error(f"Ошибка при построении графика: {e}")

def send_email_results(results: List[Dict[str, Any]], email: str) -> bool:
    """Симуляция отправки результатов по email (в реальности используйте smtplib)."""
    try:
        report = generate_report(results)
        print(f"📧 Результаты отправлены на {email} (симуляция).\n{report[:200]}...")
        logger.info(f"Результаты отправлены на {email} (симуляция)")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке email: {e}")
        return False

def multi_target_test(targets: List[str], method: str, num_requests: int, concurrent: int) -> List[Dict[str, Any]]:
    """Тест на несколько целей."""
    all_results = []
    try:
        from core import run_http_test, run_ping_test
        for target in targets:
            if not target.strip():
                continue
            print(f"🎯 Тестирование цели: {target.strip()}")
            if method == "1":
                url = f"http://{target.strip()}" if not target.strip().startswith(("http://", "https://")) else target.strip()
                results = asyncio.run(run_http_test(url, num_requests, concurrent))
            else:
                if not validate_ip(target.strip()):
                    print(f"❌ Пропуск неверного IP: {target}")
                    continue
                results = run_ping_test(target.strip(), num_requests, concurrent)
            all_results.extend(results)
    except Exception as e:
        logger.error(f"Ошибка в multi_target_test: {e}")
    return all_results

def ramp_up_concurrency(start_concurrent: int, end_concurrent: int, steps: int, url: str, num_requests: int) -> List[Dict[str, Any]]:
    """Постепенное увеличение concurrency."""
    results = []
    try:
        from core import run_http_test
        if start_concurrent >= end_concurrent:
            raise ValueError("Start concurrent должен быть меньше end concurrent.")
        step_size = max(1, (end_concurrent - start_concurrent) // steps)
        for i in range(steps + 1):
            current_con = start_concurrent + i * step_size
            if current_con > end_concurrent:
                current_con = end_concurrent
            print(f"📈 Тестирование с concurrency: {current_con}")
            step_results = asyncio.run(run_http_test(url, num_requests, current_con))
            results.extend(step_results)
            time.sleep(1)  # Пауза между шагами
    except ValueError as e:
        logger.error(f"Ошибка валидации в ramp_up_concurrency: {e}")
    except Exception as e:
        logger.error(f"Ошибка в ramp_up_concurrency: {e}")
    return results

def stress_test_duration(url: str, duration: int, concurrent: int) -> int:
    """Стресс-тест на фиксированное время."""
    requests_made = 0
    try:
        start_time = time.time()
        from core import run_http_test
        while time.time() - start_time < duration:
            batch_size = min(10, concurrent)  # Батчи для эффективности
            batch_results = asyncio.run(run_http_test(url, batch_size, concurrent))
            requests_made += len([r for r in batch_results if r.get("status")])
            logger.debug(f"Батч {requests_made} выполнен.")
            time.sleep(0.1)  # Поскольку функция синхронная
    except Exception as e:
        logger.error(f"Ошибка в stress_test_duration: {e}")
    return requests_made

def cleanup_resources():
    """Очистка ресурсов после теста."""
    try:
        logger.info("Очистка ресурсов...")
        import gc
        gc.collect()
    except Exception as e:
        logger.error(f"Ошибка при очистке ресурсов: {e}")

def export_to_json(results: List[Dict[str, Any]], filename: Optional[str] = None) -> bool:
    """Экспорт результатов в JSON."""
    try:
        if not results:
            logger.warning("Нет результатов для экспорта.")
            return False
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not filename:
            filename = f"ddos_test_results_{timestamp}.json"
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False, default=str)
        logger.info(f"Результаты экспортированы в {filename}")
        print(f"✅ Экспортировано в {filename}")
        return True
    except (IOError, OSError, TypeError) as e:
        logger.error(f"Ошибка при экспорте в JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при экспорте: {e}")
        return False

def check_network_connectivity(host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> bool:
    """Проверка доступности сети."""
    try:
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port)) == 0
        sock.close()
        socket.setdefaulttimeout(original_timeout)
        return result
    except OSError:
        return False
    except Exception as e:
        logger.error(f"Ошибка проверки сети: {e}")
        return False