# coding: utf-8

from time import perf_counter as _perf_counter

from user_agents import parse as parse_ua
from loguru import logger as l


def test_ua(ua: str) -> bool:
    '''
    return whether is browser or not
    '''
    lower = ua.lower()
    l.debug(f'[test_ua] ua: {lower}')
    for i in [
        # 经典命令行工具
        'curl', 'wget', 'w3m', 'lynx', 'links', 'elinks',

        # HTTP 客户端库 / 工具
        'httpclient', 'http_client', 'okhttp', 'axios', 'fetch', 'node-fetch',
        'python-requests', 'python-urllib', 'urllib/', 'requests/',
        'java/', 'jakarta', 'apache-http', 'apacheclient', 'lwp::', 'libwww-perl', 'www-mechanize',

        # 各种语言内置库
        'go-http-client', 'php/', 'perl/', 'ruby/', 'dalvik/', 'cfnetwork',  # iOS/macOS 原生
        'winhttp', 'wininet', 'powershell/', 'microsoft url control',

        # 爬虫框架
        'scrapy', 'scrapy-redis', 'pyspider', 'colly', 'crawler', 'spider', 'bot/',
        'bot', 'slurp', 'crawler', 'spider', 'archiver', 'feedfetcher', 'mediapartners',
        'adsbot', 'googlebot', 'bingbot', 'yandexbot', 'baiduspider', 'duckduckbot',

        # 监控 / 健康检查 / Uptime / 负载均衡器
        'uptime', 'pingdom', 'newrelic', 'zabbix', 'nagios', 'check_http', 'site24x7',
        'uptimerobot', 'statuscake', 'cloudwatch', 'healthcheck', 'loadbalancer',

        # 各种自动化工具、抓包、测试工具
        'headlesschrome', 'phantomjs', 'casperjs', 'nightmare', 'puppeteer', 'playwright',
        'selenium', 'webdriver', 'chromedriver', 'geckodriver', 'edgedriver',
        'postmanruntime', 'insomnia', 'httpie', 'restsharp', 'faraday',

        # 安全扫描器
        'nessus', 'nmap', 'nikto', 'w3af', 'netsparker', 'acunetix', 'appscan',
        'burpcollaborator', 'sqlmap', 'dirbuster', 'openvas',

        # 其他常见非浏览器
        'dalvik', 'cfnetwork', 'gsa/', 'applewebkit/533', 'applewebkit/534',  # 旧版 iOS 伪装
        'monitor', 'probe', 'scraper', 'analyzer', 'validator', 'lighthouse',
        'gtmetrix', 'pagespeed', 'webpagetest', 'pingdom', 'dareboost',
    ]:
        if i in lower:
            l.debug(f'[test_ua] matched ua: {i}, return False')
            return False
    result = parse_ua(ua)
    l.debug(f'[test_ua] parsed: {result}')
    return any((
        result.is_pc,
        result.is_mobile,
        result.is_tablet,
        result.is_touch_capable
    ))


def perf_counter():
    '''
    获取一个性能计数器, 执行返回函数来结束计时, 并返回保留两位小数的毫秒值
    '''
    start = _perf_counter()
    return lambda: round((_perf_counter() - start)*1000, 2)


def check_domain(host: str, domains: list[str]) -> bool:
    host = host.lower()
    return any(host == d.lower() or host.endswith('.' + d.lower()) for d in domains)


def replace_error_icon(before: str) -> str:
    return before.replace(r'''data:image/svg+xml;utf8,%3Csvg%20id%3D%22a%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2047.9145%2047.9641%22%3E%3Ccircle%20cx%3D%2223.9572%22%20cy%3D%2223.982%22%20r%3D%2223.4815%22%20style%3D%22fill%3A%20%23bd2426%3B%22/%3E%3Cline%20x1%3D%2219.0487%22%20y1%3D%2219.0768%22%20x2%3D%2227.8154%22%20y2%3D%2228.8853%22%20style%3D%22fill%3A%20none%3B%20stroke%3A%20%23fff%3B%20stroke-linecap%3A%20round%3B%20stroke-linejoin%3A%20round%3B%20stroke-width%3A%203px%3B%22/%3E%3Cline%20x1%3D%2227.8154%22%20y1%3D%2219.0768%22%20x2%3D%2219.0487%22%20y2%3D%2228.8853%22%20style%3D%22fill%3A%20none%3B%20stroke%3A%20%23fff%3B%20stroke-linecap%3A%20round%3B%20stroke-linejoin%3A%20round%3B%20stroke-width%3A%203px%3B%22/%3E%3C/svg%3E''', r'''data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIiB3aWR0aD0iNDgiIGhlaWdodD0iNDgiPjxkZWZzPjxmaWx0ZXIgaWQ9ImRhcmtyZWFkZXItaW1hZ2UtZmlsdGVyIj48ZmVDb2xvck1hdHJpeCB0eXBlPSJtYXRyaXgiIHZhbHVlcz0iMC4yNDkgLTAuNjE0IC0wLjY3MiAwLjAwMCAxLjAzNSAtMC42NDYgMC4yODggLTAuNjY0IDAuMDAwIDEuMDIwIC0wLjYzNiAtMC42MDkgMC4yNTAgMC4wMDAgMC45OTQgMC4wMDAgMC4wMDAgMC4wMDAgMS4wMDAgMC4wMDAiIC8+PC9maWx0ZXI+PC9kZWZzPjxpbWFnZSB3aWR0aD0iNDgiIGhlaWdodD0iNDgiIGZpbHRlcj0idXJsKCNkYXJrcmVhZGVyLWltYWdlLWZpbHRlcikiIHhsaW5rOmhyZWY9ImRhdGE6aW1hZ2UvcG5nO2Jhc2U2NCxpVkJPUncwS0dnb0FBQUFOU1VoRVVnQUFBREFBQUFBd0NBTUFBQUJnM0FtMUFBQUJJRkJNVkVVQUFBRC9nSUQvVlZYVUtpcS9KQzdCTEN6REtpcTlLU25CSnllOUtTbStLQ2kvSnlmQUtDaTlLQ2kvSkNpOEp5ZTlKeWU5SkNlK0p5ZS9KaWE4SmltOUpTaStKaWE4SmlpK0pTZStKU2U5SlNhOUpDYTlKQ2U5SlNlOUpTYTlKU2ErSkNhOUpDZTlKU2U4SlNlOUpTYTlKU2U5SlNhOEpTYTlKU2E5SkNlOUpDZTlKU2E5SlNhOUpDZTlKQ2E5SlNhOEpTZTlKQ2E5SkNhOUpDYTlKU2E5SlNlOUpDYThKQ2E5SlNhOUpTZTlKQ2E5SlNlK0p5bS9LU3ZBTFMvQk1UUEtUbERMVkZiVmNuUFdkbmZYZW52WGUzelhmSDNhaElYYWhZYmJob2ZjaTR6ZmxaWGtwYWJtcmE3bnI3RG5zYkxwdHJmcnZMM3J2YjNydnI3dXhzZngwTkR4MGRMeTB0UHoyTm4wMnRyNTYrdjU3T3o3OGZIOSt2ci8vdjcvLy85Q3ZGcm1BQUFBT25SU1RsTUFBZ01HSEIwZUh5RXlNelE1T2tCQlFsVldWMWhaY25OMWRwS1RvcVdtcDZpcXE2eXRzck8wdkwyK3ljck56dVhtNk9ucTYrenc4Zkw2VjEzUHhnQUFBYXRKUkVGVVNNZWxWbWxUd2tBTURVV0UxZ01FQkMxNGNDaW5naUJVWXhIRkd4RnZSUVh5Ly8rRkh6Z0d1a3U3SGQ2WHpyeSsxMHlTYnJJQWM4TWhoNks1UWhXcmhWdzBMRHVzNUxKYXdrbVVWTmxNN3MwaWk2eDNsdHk5aDN6c3U3bjZOUTFuUWZPemNrbEZNNmlTUWUrTW96bml6dW52NzZJVllsTXhWTFNHT3FIM293Z0NZLzJDSm1UUVhDTkRBc1dRR09wWFVSU3JBME5hMkpBR0FJQWxGSWNpV3RMSjBqcktOZ3hsQjRCc0pLOSsyem9pb3Y3MGQ4MDRaSUN3a2ZzbWFpRWl0b2grR0VNWVlNdklQUkJSRTdFNWVCaXdBM0RBa0MyaWZxUFJKM28rWTk0ZEFod3hwUDVHMU9zUmZkVFlyQXNBcHl4Yjd4QVJkZXFjTXAwQThLcDNRVVIweVMwc044TDVwMWtFVGc2dmd4emVkVzRPSmxWcUlhOUsyMGJ1bm9nZUIzMjQ0L1ZodzhoOURSdkE3ZlFtd0xLUnUrbSsxQkFSOVhiM2xqR3NBRWpIZHY1V0NRQWlOcytEL1JNSEdXRjl4dTdVR0cyS3BLQStPUnBrTHNISnR6aWVsUUVoUTlEbTlJNU03WWVZOVdDVjV0cEE5bmNjQUFSTnR1ZzZkKzk2VWpQMEtjK3MxZTdqM2dSOFpwY0hKVktaVWxjaWl0WDFSRkpDMFh4UlE2MllqNFlWSnRkL293YVRFTW1nanpNQUFBQUFTVVZPUks1Q1lJST0iIC8+PC9zdmc+''')
