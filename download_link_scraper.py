# Function/download_link_scraper.py
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_download_link(
    url: str,
    *,
    headless: bool = True,
    timeout_body: int = 10,
    timeout_query: int = 6,
    debug: bool = True,  # 打开即可看到 [1/4]...[4/4]
) -> Optional[str]:
    def log(msg: str):
        if debug:
            print(msg)

    print(f"\n[开始] 正在处理URL: {url}")
    print("[1/4] 启动 Chrome ...")
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.page_load_strategy = "eager"

    driver = None
    try:
        driver = webdriver.Chrome(options=options)

        print("[2/4] 打开页面 ...")
        driver.get(url)
        WebDriverWait(driver, timeout_body).until(lambda d: d.find_elements(By.TAG_NAME, "body"))
        log(f"[i] 标题: {driver.title}")

        print("[3/4] 在 DOM 里查找含 /resolve/ 的 <a> ...")
        try:
            WebDriverWait(driver, timeout_query).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/resolve/']"))
            )
        except Exception:
            print("[!] 未发现含 /resolve/ 的 <a>")
            return None

        anchors: List = driver.find_elements(By.CSS_SELECTOR, "a[href*='/resolve/']")
        hrefs = []
        for a in anchors:
            try:
                h = a.get_attribute("href") or ""
                if h:
                    hrefs.append(h)
            except Exception:
                pass

        if not hrefs:
            print("[!] 找到了元素但无有效 href")
            return None

        zips = [h for h in hrefs if h.lower().endswith(".zip")]
        if zips:
            print(f"[✓] 获取到 /resolve/ 链接: {zips[0]}")
            return zips[0]

        print(f"[i] 无 .zip，返回第一个 /resolve/：{hrefs[0]}")
        return hrefs[0]

    except Exception as e:
        print(f"[!] 异常：{type(e).__name__}: {e}")
        return None
    finally:
        print("[4/4] 关闭浏览器")
        if driver:
            driver.quit()
