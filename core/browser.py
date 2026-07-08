import os, sys
import subprocess
import traceback
from playwright.sync_api import sync_playwright
from utils.config import DEBUG, get_environment, Environment

PLAYWRIGHT_BROWSERS_PATH = "../chrome"

def install_browser():
    """
    安装 Chromium 浏览器
    """
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
        print("浏览器安装完成，请重新运行程序。")
    except subprocess.CalledProcessError as e:
        print(f"发生未知错误：{e}")


def get_browser():
    """
    启动浏览器实例
    :return: 浏览器实例

    环境变量：
      BROWSER_CHANNEL=chrome  用系统安装的真实 Chrome（更抗反自动化；住宅环境推荐）
      HEADLESS=false          有头运行（配合 xvfb-run 可在无显示服务器上跑）
    """

    # 允许用环境变量覆盖浏览器渠道与有头/无头
    channel = os.getenv("BROWSER_CHANNEL") or None
    headless_env = os.getenv("HEADLESS")
    headless = True if headless_env is None else (headless_env.lower() != "false")

    # 反自动化 + 服务器常用启动参数
    launch_args = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
    ]

    env = get_environment()
    if env == Environment.LOCAL:
        # 指定了系统浏览器渠道时，无需依赖打包的 chromium 路径
        if not channel:
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.abspath(
                os.path.join(os.path.dirname(__file__), PLAYWRIGHT_BROWSERS_PATH)
            )
        if DEBUG and headless_env is None:
            headless = False
    elif env == Environment.PACKED:
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.abspath(
            os.path.join(os.path.dirname(sys.executable), PLAYWRIGHT_BROWSERS_PATH)
        )

    try:
        # 启动浏览器
        playwright = sync_playwright().start()
        launch_kwargs = {"headless": headless, "args": launch_args}
        if channel:
            launch_kwargs["channel"] = channel
        browser = playwright.chromium.launch(**launch_kwargs)
        return playwright, browser
    except Exception as e:
        # 捕获浏览器启动错误
        if "Executable doesn't exist" in str(e) and env != Environment.GITHUBACTION:
            print("浏览器可执行文件不存在！")
            install_browser()
            sys.exit(1)
        else:
            traceback.print_exc()
