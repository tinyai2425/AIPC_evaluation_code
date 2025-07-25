from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

def get_sha256(url):
    """
    从目标网页提取 SHA256 值
    Args:
        url (str): 目标网页URL
    Returns:
        str: 成功返回 SHA256，失败返回 None
    """
    print(f"\n[开始] 正在处理URL: {url}")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")  # 重要！WSL 需要这个
    options.add_argument("--disable-dev-shm-usage")  # 重要！避免内存问题
    options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.page_load_strategy = 'eager'

    driver = None
    try:
        print("[1/6] 正在启动 Chrome 浏览器...")
        driver = webdriver.Chrome(options=options)
        print("[2/6] 浏览器启动成功，正在加载页面...")
        
        driver.get(url)
        print(f"[3/6] 页面加载完成 | 标题: {driver.title} | URL: {driver.current_url}")
        
        # 检查页面是否有效（404/500错误）
        if "404" in driver.title or "500" in driver.title:
            print("[!] 错误: 页面返回404/500状态")
            return None
        
        print("[4/6] 正在等待关键信息出现（最多5秒）...")
        WebDriverWait(driver, 5).until(
            lambda d: "文件信息总览" in d.page_source or "SHA256" in d.page_source
        )
        print("[5/6] 关键信息加载完成，正在提取SHA256...")
        
        # 提取 SHA256
        page_text = driver.find_element(By.TAG_NAME, "body").text
        if "SHA256：" in page_text:
            sha256 = page_text.split("SHA256：")[1].split()[0]
            print(f"[✓] 成功提取 SHA256: {sha256}")
            return sha256
        else:
            print("[!] 警告: 页面中未找到'SHA256：'文本")
            return None

    except TimeoutException:
        print("[!] 超时: 5秒内未找到'文件信息总览'或'SHA256'关键字")
        print(f"当前页面源码片段: {driver.page_source[:500]}...")  # 打印前500字符供调试
        return None
    except WebDriverException as e:
        print(f"[!] 浏览器异常: {str(e)}")
        return None
    except Exception as e:
        print(f"[!] 未知异常: {type(e).__name__}: {str(e)}")
        return None
    finally:
        if driver:
            print("[6/6] 正在关闭浏览器...")
            driver.quit()
        print("[结束] 处理完成\n")