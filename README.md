# Cloudflare SpeedTest

> Cloudflare CDN Node Speed Test Tool - Professional Anycast Network Performance Testing Solution
>
> Cloudflare CDN 节点测速工具 - 专业的 Anycast 网络性能测试解决方案

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com)

---

**[English](#english) | [中文](#chinese)**

---

<a name="english"></a>
## 🌐 English

### Introduction

Cloudflare SpeedTest is a high-performance tool for testing and selecting optimal IP nodes from Cloudflare's global Anycast network. It operates entirely locally without external API dependencies.

### Key Features

- ✅ **Global Coverage** - Support for 298 IATA geographic locations of Cloudflare CDN nodes
- ✅ **Smart IP Generation** - Intelligent target generation based on official Cloudflare IP ranges
- ✅ **Dual Testing Mode** - TCP latency test + HTTP/HTTPS download speed test
- ✅ **High Concurrency** - Multi-threaded concurrent testing with customizable worker count
- ✅ **Quality Grading System** - Built-in premium IP database with quality scoring based on real test data
- ✅ **Geographic Filtering** - Filter by IATA code, country, or region
- ✅ **Flexible Output** - Export results in CSV or JSON format
- ✅ **Auto Retry** - Automatic retry on TCP connection failure
- ✅ **TLS/SNI Support** - Full support for HTTPS speed testing and SNI configuration
- ✅ **Offline Capable** - No external API dependency, all data stored locally

### Quick Start

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Basic Usage

```bash
# Test all Cloudflare IPs, show top 10 results
python src/main.py

# Test only Hong Kong region (HKG) IPs
python src/main.py --iata HKG

# Test Los Angeles region, port 443, show top 5 IPs
python src/main.py --iata LAX --port 443 --top 5

# Test TCP latency only, no speed test, max 50 IPs
python src/main.py --no-speed --max-ips 50

# Filter IPs with latency < 200ms and save results
python src/main.py --max-delay 200 --save

# Use 20 concurrent workers, save as JSON
python src/main.py --workers 20 --save --format json
```

### Command Line Arguments

#### Test Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--iata` | IATA airport code filter (e.g., HKG, LAX, NRT) | None |
| `--port` | Port number filter | 443 |
| `--max-ips` | Maximum number of IPs to test | 0 (unlimited) |
| `--workers` | Number of concurrent test threads | 10 |
| `--tcp-timeout` | TCP connection timeout (seconds) | 5 |
| `--speed-timeout` | Speed test timeout (seconds) | 30 |
| `--no-speed` | Skip download speed test, only test TCP latency | False |

#### Filter Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--max-delay` | Maximum latency limit (ms) | 300 |
| `--min-speed` | Minimum speed limit (MB/s) | 0 |
| `--top` | Show top N best IPs | 10 |

#### Output Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--save` | Save test results to file | False |
| `--format` | Output format (`csv` or `json`) | `csv` |
| `--output-dir` | Results output directory | `results` |
| `--verbose` | Show detailed logs | False |

### Project Structure

```
cloudflare-speedtest/
├── src/
│   ├── main.py              # Main entry point
│   ├── api_client.py        # Configuration manager (local mode)
│   ├── ip_tester.py         # IP tester (TCP latency, speed test)
│   └── cloudflare_ips.py    # Cloudflare IP database (IP generation, geo mapping)
├── locations/
│   └── locations.json       # 298 global IATA locations dataset
├── results/                 # Test results output directory
├── requirements.txt         # Dependencies
├── LICENSE                  # MIT License
└── README.md               # This file
```

### How It Works

1. **IP Generation** - Generate test IPs from official Cloudflare IP ranges (no API needed)
2. **Configuration Loading** - Load test endpoints from local configuration
3. **Concurrent Testing** - Test all IPs using thread pool
4. **Result Filtering** - Sort and filter best IPs by latency and speed
5. **Output** - Display results and optionally save to file

### Test Endpoints

The tool uses Cloudflare's official endpoints for testing:

- **Speed Test**: `speed.mingri.icu/50MB.7z,speed.cloudflare.com/__down?bytes=10000000` (10MB download)
- **TCP Test**: `www.visa.cn,www.cloudflare.com`

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<a name="chinese"></a>
## 🇨🇳 中文

### 项目简介

Cloudflare SpeedTest 是一款高性能的 Cloudflare CDN 节点测速工具，用于测试和筛选全球 Cloudflare Anycast 网络中的最优 IP 节点。完全本地运行，无需外部 API 依赖。

### 核心特性

- ✅ **全球节点覆盖** - 支持 298 个 IATA 地理位置的 Cloudflare CDN 节点
- ✅ **智能IP生成** - 基于 Cloudflare 官方 IP 段，智能生成测试目标
- ✅ **双重测试模式** - TCP 延迟测试 + HTTP/HTTPS 下载速度测试
- ✅ **高并发支持** - 多线程并发测试，可自定义并发数
- ✅ **质量分级系统** - 内置优质 IP 库，基于实测数据的质量评分
- ✅ **地理位置筛选** - 支持按 IATA 代码、国家、地区筛选
- ✅ **灵活的结果输出** - 支持 CSV、JSON 格式导出
- ✅ **自动重试机制** - TCP 连接失败自动重试
- ✅ **TLS/SNI 支持** - 完整支持 HTTPS 测速和 SNI 配置
- ✅ **离线运行** - 无外部 API 依赖，所有数据本地存储

### 快速开始

#### 安装依赖

```bash
pip install -r requirements.txt
```

#### 基础使用

```bash
# 测试所有 Cloudflare IP，显示前 10 个最优结果
python src/main.py

# 只测试香港地区 (HKG) 的 IP
python src/main.py --iata HKG

# 测试洛杉矶地区，使用 443 端口，显示前 5 个最优 IP
python src/main.py --iata LAX --port 443 --top 5

# 只测试 TCP 延迟，不测速度，最多测试 50 个 IP
python src/main.py --no-speed --max-ips 50

# 筛选延迟 < 200ms 的 IP 并保存结果
python src/main.py --max-delay 200 --save

# 使用 20 个并发线程，保存为 JSON 格式
python src/main.py --workers 20 --save --format json
```

### 命令行参数

#### 测试参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--iata` | IATA 机场代码筛选 (如: HKG, LAX, NRT) | 不限 |
| `--port` | 端口号 | 443 |
| `--max-ips` | 最大测试 IP 数量 | 0 (不限) |
| `--workers` | 并发测试线程数 | 10 |
| `--tcp-timeout` | TCP 连接超时时间(秒) | 5 |
| `--speed-timeout` | 速度测试超时时间(秒) | 30 |
| `--no-speed` | 不测试下载速度，仅测 TCP 延迟 | False |

#### 筛选参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--max-delay` | 最大延迟限制(ms) | 300 |
| `--min-speed` | 最小速度限制(MB/s) | 0 |
| `--top` | 显示前 N 个最优 IP | 10 |

#### 输出参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--save` | 保存测试结果到文件 | False |
| `--format` | 输出格式 (`csv` 或 `json`) | `csv` |
| `--output-dir` | 结果输出目录 | `results` |
| `--verbose` | 显示详细日志 | False |

### 使用场景

#### 场景 1: 快速找到本地最优 IP

```bash
# 测试少量 IP，使用内置的优质 IP 库
python src/main.py --max-ips 20 --save
```

#### 场景 2: 特定地区的全面测试

```bash
# 测试日本东京地区所有可用 IP，筛选延迟 < 150ms 的节点
python src/main.py --iata NRT --max-delay 150 --save
```

#### 场景 3: 仅测试连通性

```bash
# 快速测试 TCP 连接，不测速度，适合大批量筛选
python src/main.py --no-speed --max-ips 100 --workers 30
```

#### 场景 4: 高速节点筛选

```bash
# 筛选下载速度 > 5MB/s 且延迟 < 200ms 的节点
python src/main.py --min-speed 5 --max-delay 200 --save
```

### 项目结构

```
cloudflare-speedtest/
├── src/
│   ├── main.py              # 主程序入口
│   ├── api_client.py        # 配置管理器 (本地模式)
│   ├── ip_tester.py         # IP 测试器 (TCP 延迟测试、速度测试)
│   └── cloudflare_ips.py    # Cloudflare IP 数据库 (IP 生成、地理位置映射)
├── locations/
│   └── locations.json       # 298 个全球 IATA 位置数据集
├── results/                 # 测试结果输出目录
├── requirements.txt         # 依赖列表
├── LICENSE                  # MIT 许可证
└── README.md               # 本文件
```

### 工作原理

1. **IP 生成阶段** - 从 Cloudflare 官方 IP 段生成测试 IP（无需 API）
2. **配置加载** - 从本地配置加载测试端点
3. **并发测试** - 使用线程池并发测试所有 IP
4. **结果筛选** - 按延迟和速度排序筛选最优 IP
5. **结果输出** - 显示结果并可选保存到文件

### 测试端点

工具使用 Cloudflare 官方端点进行测试：

- **速度测试**: `speed.mingri.icu/50MB.7z,speed.cloudflare.com/__down?bytes=10000000` (10MB 下载)
- **TCP 测试**: `www.visa.cn,www.cloudflare.com`

### 常见 IATA 代码

| 代码 | 城市 | 国家 |
|------|------|------|
| HKG | 香港 | 中国 |
| NRT | 东京 | 日本 |
| SIN | 新加坡 | 新加坡 |
| LAX | 洛杉矶 | 美国 |
| SJC | 圣何塞 | 美国 |
| LHR | 伦敦 | 英国 |
| FRA | 法兰克福 | 德国 |

### 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

### 致谢

- Cloudflare 提供的全球 Anycast 网络
- [Cloudflare IP Ranges](https://www.cloudflare.com/ips/) 官方文档
- IATA 机场代码标准

---

**免责声明 / Disclaimer**: 本工具仅用于网络性能测试和学习目的，请遵守当地法律法规和 Cloudflare 服务条款。This tool is for network performance testing and educational purposes only. Please comply with local laws and Cloudflare's Terms of Service.
