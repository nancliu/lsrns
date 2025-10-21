"""
Playwright 测试配置文件
"""

import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def browser():
    """创建浏览器实例（session级别，所有测试共享）"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # 显示浏览器窗口，方便调试
            slow_mo=500      # 每个操作延迟500ms，方便观察
        )
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def browser_headless():
    """创建无头浏览器实例（用于CI/CD）"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()
