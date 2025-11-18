"""
CloudflareSpeedTest - Cloudflare CDN节点测速工具主程序

- 使用Cloudflare IP数据库生成测试IP
- 从API获取真实的测速端点和TCP测试域名
- 完全复刻"""

import argparse
import sys
import json
import csv
from pathlib import Path
from datetime import datetime
import logging
from typing import List

from api_client import BestIPAPIClient, ServerEndpoint
from ip_tester import BatchIPTester, TestResult
from cloudflare_ips import CloudflareCDNProvider

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class CloudflareSpeedTestApp:
    """BestIP应用主类"""

    def __init__(self, args):
        self.args = args
        self.api_client = BestIPAPIClient(
            api_server=args.api_server,
            timeout=args.timeout
        )
        self.cf_ip_db = CloudflareCDNProvider()  # Cloudflare IP数据库
        self.batch_tester = BatchIPTester(
            max_workers=args.workers,
            tcp_timeout=args.tcp_timeout,
            speed_test_timeout=args.speed_timeout
        )
        self.results_dir = Path(args.output_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def progress_callback(self, completed: int, total: int, result: TestResult):
        """进度回调"""
        percentage = (completed / total) * 100
        status = "[OK]" if result.success else "[FAIL]"
        delay_str = f"{result.tcp_delay:.2f}ms" if result.tcp_delay else "N/A"
        speed_str = f"{result.download_speed:.2f}MB/s" if result.download_speed else "N/A"

        # 使用 logger 而不是 print,避免编码问题
        msg = f"[{completed}/{total} {percentage:.1f}%] {status} {result.ip}:{result.port} 延迟:{delay_str} 速度:{speed_str}"
        logger.info(msg)

    def save_results(self, results: List[TestResult], locations: List[ServerEndpoint], format: str = 'csv'):
        """保存结果到文件（仅保存有延迟数据的IP）"""
        # 过滤掉延迟为空的结果
        original_count = len(results)
        filtered_results = [r for r in results if r.tcp_delay is not None]
        filtered_count = len(filtered_results)
        skipped_count = original_count - filtered_count

        # 如果没有有效结果，不保存
        if filtered_count == 0:
            logger.warning("没有有效的测试结果（所有IP延迟为空），跳过保存")
            return

        # 记录过滤统计
        logger.info(f"准备保存结果: 总计 {original_count} 个，有效 {filtered_count} 个，跳过 {skipped_count} 个（延迟为空）")


        if format == 'csv':
            filename = self.results_dir / f"cf_speedtest_results.csv"
            self._save_csv(filtered_results, locations, filename)
        elif format == 'json':
            filename = self.results_dir / f"cf_speedtest_results.json"
            self._save_json(filtered_results, locations, filename)
        else:
            logger.error(f"不支持的格式: {format}")
            return

        logger.info(f"结果已保存到: {filename} (共 {filtered_count} 条记录)")

    def _save_csv(self, results: List[TestResult], locations: List[ServerEndpoint], filename: Path):
        """保存为CSV格式"""
        # 创建IP到位置的映射
        location_map = {f"{loc.ip}:{loc.port}": loc for loc in locations}

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'IP地址', '端口', '回源端口', 'TLS', '数据中心', '地区', '国家', '城市',
                'IATA', 'ASN', 'TCP延迟(ms)', '下载速度(MB/s)', '状态'
            ])

            for result in results:
                key = f"{result.ip}:{result.port}"
                loc = location_map.get(key)

                row = [
                    result.ip,
                    result.port,
                    loc.source_port if loc else '',
                    'Yes' if (loc and loc.tls) else 'No',
                    loc.datacenter if loc else '',
                    loc.region if loc else '',
                    loc.country if loc else '',
                    loc.city if loc else '',
                    loc.iata if loc else '',
                    loc.asn if loc else '',
                    f"{result.tcp_delay:.2f}" if result.tcp_delay else '',
                    f"{result.download_speed:.2f}" if result.download_speed else '',
                    '成功' if result.success else f'失败: {result.error}'
                ]
                writer.writerow(row)

    def _save_json(self, results: List[TestResult], locations: List[ServerEndpoint], filename: Path):
        """保存为JSON格式"""
        location_map = {f"{loc.ip}:{loc.port}": loc for loc in locations}

        output = []
        for result in results:
            key = f"{result.ip}:{result.port}"
            loc = location_map.get(key)

            item = {
                'ip': result.ip,
                'port': result.port,
                'tcp_delay_ms': result.tcp_delay,
                'download_speed_mbps': result.download_speed,
                'success': result.success,
                'error': result.error
            }

            if loc:
                item.update({
                    'source_port': loc.source_port,
                    'tls': loc.tls,
                    'datacenter': loc.datacenter,
                    'region': loc.region,
                    'country': loc.country,
                    'city': loc.city,
                    'iata': loc.iata,
                    'asn': loc.asn
                })

            output.append(item)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    def run(self):
        """
        运行主程序

        工作流程:
        1. 从Cloudflare IP数据库生成测试IP
        2. 从API获取速度测试URL和TCP测试域名
        3. 并发测试所有IP
        4. 排序输出最优IP
        """
        try:
            logger.info("=" * 60)
            logger.info("CloudflareSpeedTest - Cloudflare CDN节点测速工具 v2.0")
            logger.info("=" * 60)

            # 1. 生成IP列表(使用Cloudflare IP数据库)
            logger.info(f"正在生成测试IP列表...")
            logger.info(f"参数: Port={self.args.port or 443}, IATA={self.args.iata or '不限'}, "
                       f"数量={self.args.max_ips or 100}")

            # 使用众所周知的优选IP或生成新IP
            if self.args.max_ips <= 30:
                # 小数量使用众所周知的优选IP
                locations = self.cf_ip_db.get_verified_premium_ips(
                    port=self.args.port or 443,
                    location_code=self.args.iata  # 传递IATA筛选参数
                )
            else:
                # 大数量从完整IP段生成
                locations = self.cf_ip_db.create_endpoint_list(
                    port=self.args.port or 443,
                    count=self.args.max_ips or 100,
                    location_code=self.args.iata
                )

            if not locations:
                logger.error("未能生成任何测试IP,程序退出")
                return 1

            logger.info(f"成功生成 {len(locations)} 个测试IP")

            # 2. 获取测试端点配置 (本地模式)
            logger.info("正在加载测试端点配置...")

            speed_test_url = "speed.mingri.icu/50MB.7z"
            tcp_test_domain = "www.visa.cn" 

            if speed_test_url:
                logger.info(f"  速度测试URL: {speed_test_url}")
            else:
                logger.warning("  未获取到速度测试URL,将使用fallback端点")

            if tcp_test_domain:
                logger.info(f"  TCP测试域名: {tcp_test_domain}")
            else:
                logger.warning("  未获取到TCP测试域名")

            # 3. 批量测试IP
            print("\n开始测试IP性能...")

            # 根据端口判断是否使用TLS
            tls_ports = {443, 2053, 2083, 2087, 2096, 8443}
            use_tls = self.args.port in tls_ports if self.args.port else True

            # 检查第一个IP的TLS配置
            if locations and hasattr(locations[0], 'tls'):
                use_tls = locations[0].tls

            logger.info(f"使用{'TLS/HTTPS' if use_tls else 'HTTP'}进行测试")

            results = self.batch_tester.test_ips(
                ip_list=locations,
                test_speed=self.args.test_speed,
                use_tls=use_tls,
                custom_speed_url=speed_test_url,  # 使用API返回的真实速度测试URL
                progress_callback=self.progress_callback
            )
            print()  # 换行

            # 4. 筛选最优IP
            best_results = self.batch_tester.filter_best_ips(
                results=results,
                max_delay=self.args.max_delay,
                min_speed=self.args.min_speed,
                top_n=self.args.top_n
            )

            # 5. 显示结果
            logger.info("\n" + "=" * 60)
            logger.info(f"测试完成! 找到 {len(best_results)} 个优选IP:")
            logger.info("=" * 60)

            for i, result in enumerate(best_results, 1):
                delay_str = f"{result.tcp_delay:.2f}ms" if result.tcp_delay else "N/A"
                speed_str = f"{result.download_speed:.2f}MB/s" if result.download_speed else "N/A"
                print(f"{i}. {result.ip}:{result.port} - 延迟: {delay_str}, 速度: {speed_str}")

            # 6. 保存结果
            if self.args.save:
                self.save_results(results, locations, self.args.format)

            logger.info("\n程序执行完成!")
            return 0

        except KeyboardInterrupt:
            logger.warning("\n用户中断程序")
            return 130
        except Exception as e:
            logger.error(f"程序执行出错: {e}", exc_info=True)
            return 1
        finally:
            self.api_client.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='CloudflareSpeedTest - Cloudflare CDN节点测速工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                           # 测试所有IP并自动保存结果
  %(prog)s --iata LAX                # 只测试洛杉矶地区IP
  %(prog)s --port 443 --top 5        # 测试443端口,显示前5个最优IP
  %(prog)s --no-speed --max-ips 50   # 只测试TCP延迟,最多50个IP
  %(prog)s --max-delay 200           # 筛选延迟<200ms的IP并保存
  %(prog)s --no-save                 # 测试但不保存结果
        """
    )

    # API参数
    parser.add_argument('--api-server', default='null',
                       help='API服务器地址 (默认: null)')
    parser.add_argument('--iata', default='', help='IATA机场代码筛选')
    parser.add_argument('--port', type=int, default=0, help='端口号筛选')
    parser.add_argument('--asn', type=int, default=0, help='ASN自治系统号筛选')

    # 测试参数
    parser.add_argument('--max-ips', type=int, default=0,
                       help='最大测试IP数量 (0=不限制)')
    parser.add_argument('--workers', type=int, default=10,
                       help='并发测试线程数 (默认: 10)')
    parser.add_argument('--tcp-timeout', type=int, default=5,
                       help='TCP连接超时时间(秒) (默认: 5)')
    parser.add_argument('--speed-timeout', type=int, default=30,
                       help='速度测试超时时间(秒) (默认: 30)')
    parser.add_argument('--no-speed', dest='test_speed', action='store_false',
                       help='不测试下载速度,仅测TCP延迟')

    # 筛选参数
    parser.add_argument('--max-delay', type=float, default=300,
                       help='最大延迟限制(ms) (默认: 300)')
    parser.add_argument('--min-speed', type=float, default=0,
                       help='最小速度限制(MB/s) (默认: 0)')
    parser.add_argument('--top', dest='top_n', type=int, default=10,
                       help='显示前N个最优IP (默认: 10)')

    # 输出参数
    parser.add_argument('--save', dest='save', action='store_true', default=True,
                       help='保存测试结果到文件 (默认: 启用)')
    parser.add_argument('--no-save', dest='save', action='store_false',
                       help='不保存测试结果到文件')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                       help='输出格式 (默认: csv)')
    parser.add_argument('--output-dir', default='results',
                       help='结果输出目录 (默认: results)')

    # 其他参数
    parser.add_argument('--timeout', type=int, default=30,
                       help='API请求超时时间(秒) (默认: 30)')
    parser.add_argument('--verbose', action='store_true',
                       help='显示详细日志')

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 运行应用
    app = CloudflareSpeedTestApp(args)
    sys.exit(app.run())


if __name__ == '__main__':
    main()
