"""
Cloudflare CDN 测试配置模块

提供测试端点配置和地理位置信息管理功能。
所有配置信息均从本地文件加载，无需外部 API 依赖。

主要功能:
- 从本地 JSON 文件加载 IATA 地理位置信息
- 提供硬编码的速度测试 URL 和 TCP 测试域名
- 支持地理位置筛选和查询
"""

import json
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class IATALocation:
    """IATA机场位置信息数据类"""
    iata: str
    city: str
    region: str
    country: str  # cca2国家代码
    lat: float
    lon: float


@dataclass
class ServerEndpoint:
    """IP位置信息数据类(用于测速结果)"""
    ip: str
    port: int
    source_port: Optional[int] = None
    tls: bool = False
    datacenter: str = ""
    region: str = ""
    country: str = ""
    city: str = ""
    iata: str = ""
    asn: Optional[int] = None
    tcp_delay: Optional[float] = None
    download_speed: Optional[float] = None


class BestIPAPIClient:
    """
    Cloudflare CDN 测试配置客户端

    提供测试所需的配置信息，包括:
    1. IATA 地理位置信息 (从本地 JSON 文件加载)
    2. 速度测试 URL (硬编码)
    3. TCP 测试域名 (硬编码)

    所有数据均为本地加载，无需网络请求。
    """

    # 硬编码的测试端点配置
    DEFAULT_SPEED_TEST_URL = "speed.mingri.icu/50MB.7z"  # 10MB 下载测试
    DEFAULT_TCP_TEST_DOMAIN = "www.visa.cn"  # TCP 连接测试域名

    # 备用测试端点
    FALLBACK_SPEED_TEST_URLS = [
        "speed.cloudflare.com/__down?bytes=10000000",
        "speed.cloudflare.com/__down?bytes=5000000",
    ]

    FALLBACK_TCP_TEST_DOMAINS = [
        "www.cloudflare.com",
        "cloudflare.com",
        "1.1.1.1",
    ]

    def __init__(self, api_server: str = "", timeout: int = 30):
        """
        初始化配置客户端

        Args:
            api_server: 已废弃参数，保留以兼容旧代码
            timeout: 已废弃参数，保留以兼容旧代码
        """
        self.timeout = timeout
        self._locations_cache: Optional[List[IATALocation]] = None
        self._locations_file = self._find_locations_file()

        logger.info("Cloudflare CDN 配置客户端初始化完成 (本地模式)")

    def _find_locations_file(self) -> Path:
        """
        查找 locations.json 文件路径

        按以下顺序查找:
        1. D:\\项目\\bestIp\\locations\\locations.json (绝对路径)
        2. ../locations/locations.json (相对于 src 目录)
        3. ./locations/locations.json (相对于当前工作目录)

        Returns:
            文件路径对象
        """
        # 优先使用绝对路径
        absolute_path = Path(r"D:\项目\bestIp\locations\locations.json")
        if absolute_path.exists():
            return absolute_path

        # 相对于当前文件的路径
        current_file = Path(__file__).resolve()
        relative_path = current_file.parent.parent / "locations" / "locations.json"
        if relative_path.exists():
            return relative_path

        # 相对于当前工作目录
        cwd_path = Path.cwd() / "locations" / "locations.json"
        if cwd_path.exists():
            return cwd_path

        # 返回默认路径（即使不存在）
        logger.warning(f"未找到 locations.json 文件，使用默认路径: {absolute_path}")
        return absolute_path

    def get_locations(self, iata: str = "", port: int = 0, asn: int = 0) -> List[ServerEndpoint]:
        """
        此方法已废弃，保留以兼容旧代码

        请使用 cloudflare_ips.CloudflareCDNProvider 生成 IP 列表

        Returns:
            空列表
        """
        logger.warning("get_locations() 已废弃，请使用 cloudflare_ips.CloudflareCDNProvider")
        return []

    def get_iata_locations(self) -> List[IATALocation]:
        """
        从本地 JSON 文件加载 IATA 机场位置列表

        数据来源: locations/locations.json
        包含全球 298 个机场位置数据

        Returns:
            IATA 位置信息列表
        """
        # 使用缓存避免重复读取文件
        if self._locations_cache is not None:
            logger.info(f"使用缓存的 {len(self._locations_cache)} 个 IATA 位置")
            return self._locations_cache

        try:
            if not self._locations_file.exists():
                logger.error(f"位置数据文件不存在: {self._locations_file}")
                return []

            logger.info(f"从本地文件加载 IATA 位置: {self._locations_file}")

            with open(self._locations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            locations = []

            if isinstance(data, list):
                for item in data:
                    location = IATALocation(
                        iata=item.get('iata', ''),
                        city=item.get('city', ''),
                        region=item.get('region', ''),
                        country=item.get('cca2', ''),
                        lat=item.get('lat', 0.0),
                        lon=item.get('lon', 0.0)
                    )
                    locations.append(location)

                logger.info(f"成功加载 {len(locations)} 个 IATA 位置")
            else:
                logger.warning(f"意外的数据格式: {type(data)}")

            # 缓存结果
            self._locations_cache = locations
            return locations

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析错误: {e}")
            return []
        except Exception as e:
            logger.error(f"加载位置数据失败: {e}")
            return []

    def get_speed_test_url(self) -> Optional[str]:
        """
        获取速度测试 URL

        使用 Cloudflare 官方速度测试端点

        Returns:
            速度测试 URL 字符串
        """
        logger.info(f"使用硬编码速度测试 URL: {self.DEFAULT_SPEED_TEST_URL}")
        return self.DEFAULT_SPEED_TEST_URL

    def get_tcp_test_domain(self) -> Optional[str]:
        """
        获取 TCP 测试域名

        使用 Cloudflare 官方域名进行 TCP 连接测试

        Returns:
            TCP 测试域名
        """
        logger.info(f"使用硬编码 TCP 测试域名: {self.DEFAULT_TCP_TEST_DOMAIN}")
        return self.DEFAULT_TCP_TEST_DOMAIN

    def get_fallback_speed_test_urls(self) -> List[str]:
        """
        获取备用速度测试 URL 列表

        Returns:
            备用 URL 列表
        """
        return self.FALLBACK_SPEED_TEST_URLS.copy()

    def get_fallback_tcp_test_domains(self) -> List[str]:
        """
        获取备用 TCP 测试域名列表

        Returns:
            备用域名列表
        """
        return self.FALLBACK_TCP_TEST_DOMAINS.copy()

    def filter_locations_by_region(self, region: str) -> List[IATALocation]:
        """
        按地区筛选 IATA 位置

        Args:
            region: 地区名称 (如: "Asia", "Europe", "North America")

        Returns:
            匹配的位置列表
        """
        all_locations = self.get_iata_locations()
        filtered = [loc for loc in all_locations if loc.region.lower() == region.lower()]
        logger.info(f"筛选地区 '{region}': {len(filtered)} 个位置")
        return filtered

    def filter_locations_by_country(self, country_code: str) -> List[IATALocation]:
        """
        按国家代码筛选 IATA 位置

        Args:
            country_code: ISO 3166-1 alpha-2 国家代码 (如: "CN", "US", "JP")

        Returns:
            匹配的位置列表
        """
        all_locations = self.get_iata_locations()
        filtered = [loc for loc in all_locations if loc.country.upper() == country_code.upper()]
        logger.info(f"筛选国家 '{country_code}': {len(filtered)} 个位置")
        return filtered

    def get_location_by_iata(self, iata_code: str) -> Optional[IATALocation]:
        """
        根据 IATA 代码获取单个位置信息

        Args:
            iata_code: IATA 机场代码 (如: "HKG", "LAX", "NRT")

        Returns:
            匹配的位置信息，未找到返回 None
        """
        all_locations = self.get_iata_locations()
        for loc in all_locations:
            if loc.iata.upper() == iata_code.upper():
                return loc
        logger.warning(f"未找到 IATA 代码: {iata_code}")
        return None

    def close(self):
        """关闭客户端 (保留以兼容旧代码)"""
        # 本地模式无需关闭任何连接
        pass
