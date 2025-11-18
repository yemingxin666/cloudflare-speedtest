"""
IP测试模块
实现TCP连接延迟测试和下载速度测试
"""

import socket
import time
import requests
import logging
import warnings
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """测试结果数据类"""
    ip: str
    port: int
    tcp_delay: Optional[float] = None  # TCP连接延迟(毫秒)
    download_speed: Optional[float] = None  # 下载速度(MB/s)
    success: bool = False
    error: Optional[str] = None


class IPTester:
    """IP测试器"""

    def __init__(self, tcp_timeout: int = 5, speed_test_timeout: int = 30):
        self.tcp_timeout = tcp_timeout
        self.speed_test_timeout = speed_test_timeout

    def test_tcp_delay(self, ip: str, port: int, retries: int = 2) -> Tuple[bool, Optional[float], Optional[str]]:
        """
        测试TCP连接延迟(支持重试)

        Args:
            ip: IP地址
            port: 端口号
            retries: 失败后重试次数

        Returns:
            (成功标志, 延迟时间(ms), 错误信息)
        """
        last_error = None

        for attempt in range(retries + 1):
            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.tcp_timeout)

                # 设置TCP参数优化连接
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                if hasattr(socket, 'TCP_NODELAY'):
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                start_time = time.time()
                sock.connect((ip, port))
                end_time = time.time()

                delay_ms = (end_time - start_time) * 1000  # 转换为毫秒
                logger.debug(f"{ip}:{port} TCP延迟: {delay_ms:.2f}ms (尝试 {attempt + 1}/{retries + 1})")
                return True, delay_ms, None

            except socket.timeout:
                last_error = "连接超时"
                if attempt < retries:
                    logger.debug(f"{ip}:{port} TCP超时,重试 {attempt + 1}/{retries}")
                    time.sleep(0.5)  # 短暂延迟后重试
                    continue
            except ConnectionRefusedError:
                last_error = "连接被拒绝"
                # 连接被拒绝通常不需要重试
                break
            except OSError as e:
                last_error = f"网络错误: {e}"
                if attempt < retries:
                    logger.debug(f"{ip}:{port} 网络错误,重试 {attempt + 1}/{retries}")
                    time.sleep(0.5)
                    continue
            except Exception as e:
                last_error = str(e)
                break
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass

        logger.warning(f"{ip}:{port} TCP连接失败 (重试{retries}次): {last_error}")
        return False, None, last_error

    def test_download_speed(self, ip: str, port: int, use_tls: bool = True,
                           custom_speed_url: Optional[str] = None) -> Tuple[bool, Optional[float], Optional[str]]:
        """
        通过下载公共文件测试速度

                - 优先使用API返回的速度测试URL: speed.mingri.icu/50MB.7z
        - Fallback到公共CDN端点

        Args:
            ip: IP地址
            port: 端口号
            use_tls: 是否使用TLS
            custom_speed_url: 自定义速度测试URL (从API获取,格式: "domain.com/path")

        Returns:
            (成功标志, 下载速度(MB/s), 错误信息)
        """
        scheme = "https" if use_tls else "http"

        # 测试端点列表（按优先级）
        test_paths = []

        # 1. 如果有自定义速度测试URL (从API获取)
        if custom_speed_url:
            # 解析 URL: "speed.mingri.icu/50MB.7z" -> ("50MB.7z", "speed.mingri.icu")
            parts = custom_speed_url.split('/', 1)
            if len(parts) == 2:
                domain, path = parts[0], '/' + parts[1]
                test_paths.append((path, domain))
                logger.info(f"使用自定义速度测试URL: {custom_speed_url}")
        # 2. Fallback到公共CDN端点
        test_paths.extend([
            ("/", "cloudflare.com"),           # 根路径，使用通用域名作为SNI
            ("/cdn-cgi/trace", "cloudflare.com"),  # Cloudflare trace
            ("/", "www.google.com"),           # 尝试Google
            ("/generate_204", "connectivitycheck.gstatic.com"),  # Google连通性检查
        ])

        # 目标下载量（字节）
        target_size = 5 * 1024 * 1024  # 5MB
        min_size = 100 * 1024          # 最小100KB才认为有效

        best_speed = 0.0
        success = False
        last_error = None

        for path, sni_hostname in test_paths:
            try:
                url = f"{scheme}://{ip}:{port}{path}"
                logger.debug(f"尝试测速URL: {url} (SNI: {sni_hostname})")

                # 创建自定义session，设置SNI
                session = requests.Session()

                if use_tls:
                    # 配置SSL/TLS以支持SNI
                    from urllib3.util.ssl_ import create_urllib3_context
                    import ssl

                    # 创建SSL上下文
                    ctx = create_urllib3_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE

                    # 创建自定义的HTTPAdapter with SNI
                    from requests.adapters import HTTPAdapter
                    from urllib3.poolmanager import PoolManager

                    class SNIAdapter(HTTPAdapter):
                        def __init__(self, sni_host, *args, **kwargs):
                            self.sni_host = sni_host
                            super().__init__(*args, **kwargs)

                        def init_poolmanager(self, *args, **kwargs):
                            kwargs['server_hostname'] = self.sni_host
                            kwargs['assert_hostname'] = False
                            return super().init_poolmanager(*args, **kwargs)

                    adapter = SNIAdapter(sni_hostname)
                    session.mount('https://', adapter)

                session.verify = False

                headers = {
                    'Host': sni_hostname,  # 设置Host header
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': '*/*',
                    'Accept-Encoding': 'identity',  # 禁用压缩
                    'Connection': 'close'
                }

                start_time = time.time()
                downloaded = 0

                with session.get(url, headers=headers, stream=True,
                               timeout=self.speed_test_timeout) as response:

                    # 接受所有非错误状态码
                    if response.status_code >= 400:
                        last_error = f"HTTP {response.status_code}"
                        logger.debug(f"{url} 返回 {response.status_code}")
                        continue

                    # 开始下载数据
                    for chunk in response.iter_content(chunk_size=65536):
                        if chunk:
                            downloaded += len(chunk)
                            # 下载足够数据后停止
                            if downloaded >= target_size:
                                break

                    elapsed = time.time() - start_time

                    # 检查是否下载了足够的数据
                    if downloaded >= min_size and elapsed > 0:
                        speed_mbps = (downloaded / (1024 * 1024)) / elapsed

                        # 更新最佳速度
                        if speed_mbps > best_speed:
                            best_speed = speed_mbps
                            success = True

                        logger.info(f"{ip}:{port} 从 {path} 下载速度: {speed_mbps:.2f} MB/s "
                                  f"(下载 {downloaded/1024/1024:.2f}MB 用时 {elapsed:.2f}s)")

                        # 成功就不再尝试其他端点
                        break
                    else:
                        last_error = f"下载数据不足 ({downloaded} bytes)"
                        logger.debug(f"{url} 下载数据不足: {downloaded} bytes")
                        continue

            except requests.exceptions.Timeout:
                last_error = "下载超时"
                logger.debug(f"{url} 超时")
                continue
            except requests.exceptions.ConnectionError as e:
                last_error = f"连接错误: {str(e)}"
                logger.debug(f"{url} 连接失败: {e}")
                continue
            except Exception as e:
                last_error = str(e)
                logger.debug(f"{url} 测试失败: {e}")
                continue

        if success:
            return True, best_speed, None
        else:
            logger.warning(f"{ip}:{port} 所有测速端点均失败，最后错误: {last_error}")
            return False, None, last_error or "所有测速端点均不可用"

    def test_ip(self, ip: str, port: int, test_speed: bool = True, use_tls: bool = True,
               custom_speed_url: Optional[str] = None) -> TestResult:
        """
        完整测试单个IP

        Args:
            ip: IP地址
            port: 端口号
            test_speed: 是否测试下载速度
            use_tls: 是否使用TLS
            custom_speed_url: 自定义速度测试URL (从API的/speed端点获取)

        Returns:
            测试结果
        """
        result = TestResult(ip=ip, port=port)

        # 第一步: 测试TCP连接延迟
        tcp_success, tcp_delay, tcp_error = self.test_tcp_delay(ip, port)

        if not tcp_success:
            result.error = tcp_error
            return result

        result.tcp_delay = tcp_delay
        result.success = True

        # 第二步: 如果需要,测试下载速度
        if test_speed:
            speed_success, download_speed, speed_error = self.test_download_speed(
                ip, port, use_tls, custom_speed_url
            )
            if speed_success:
                result.download_speed = download_speed
            else:
                # 速度测试失败不影响整体成功状态,但记录错误
                logger.debug(f"{ip}:{port} 速度测试失败: {speed_error}")

        return result


class BatchIPTester:
    """批量IP测试器"""

    def __init__(self, max_workers: int = 10, tcp_timeout: int = 5, speed_test_timeout: int = 30):
        self.max_workers = max_workers
        self.tester = IPTester(tcp_timeout=tcp_timeout, speed_test_timeout=speed_test_timeout)

    def test_ips(self, ip_list: list, test_speed: bool = True, use_tls: bool = True,
                 custom_speed_url: Optional[str] = None, progress_callback=None) -> list:
        """
        批量测试IP列表

        Args:
            ip_list: IP位置列表
            test_speed: 是否测试下载速度
            use_tls: 是否使用TLS
            custom_speed_url: 自定义速度测试URL (从API的/speed端点获取)
            progress_callback: 进度回调函数

        Returns:
            测试结果列表
        """
        results = []
        total = len(ip_list)

        logger.info(f"开始批量测试 {total} 个IP...")
        if custom_speed_url:
            logger.info(f"使用自定义速度测试URL: {custom_speed_url}")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_ip = {}
            for location in ip_list:
                future = executor.submit(
                    self.tester.test_ip,
                    location.ip,
                    location.port,
                    test_speed,
                    use_tls,
                    custom_speed_url  # 传递自定义速度测试URL
                )
                future_to_ip[future] = location

            # 收集结果
            completed = 0
            for future in as_completed(future_to_ip):
                location = future_to_ip[future]
                try:
                    result = future.result()
                    results.append(result)

                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total, result)

                except Exception as e:
                    logger.error(f"测试 {location.ip}:{location.port} 时发生异常: {e}")
                    results.append(TestResult(
                        ip=location.ip,
                        port=location.port,
                        success=False,
                        error=str(e)
                    ))

        logger.info(f"批量测试完成,成功: {sum(1 for r in results if r.success)}/{total}")
        return results

    def filter_best_ips(self, results: list, max_delay: float = 300, min_speed: float = 0,
                        top_n: int = 10) -> list:
        """
        筛选最优IP

        Args:
            results: 测试结果列表
            max_delay: 最大延迟限制(ms)
            min_speed: 最小速度限制(MB/s)
            top_n: 返回前N个最优结果

        Returns:
            排序后的最优IP列表
        """
        # 筛选成功的结果
        valid_results = [r for r in results if r.success and r.tcp_delay is not None]

        # 应用延迟过滤
        if max_delay > 0:
            valid_results = [r for r in valid_results if r.tcp_delay <= max_delay]

        # 应用速度过滤
        if min_speed > 0:
            valid_results = [r for r in valid_results if r.download_speed and r.download_speed >= min_speed]

        # 排序: 优先延迟低,其次速度快
        valid_results.sort(key=lambda r: (
            r.tcp_delay,  # 延迟越小越好
            -(r.download_speed or 0)  # 速度越大越好(负号反转排序)
        ))

        return valid_results[:top_n]
