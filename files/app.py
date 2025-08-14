# cloud/files/app.py

import pybase64, base64, binascii, requests, os, concurrent.futures
from bs4 import BeautifulSoup
import re

fixed_text = """#profile-title: base64:VjJSYXkgQ29uZmlncw==
#profile-update-interval: 1
#subscription-userinfo: upload=29; download=12; total=10737418240000000; expire=2546249531
#support-url: https://github.com/nekovpn/cloud
#profile-web-page-url: https://github.com/nekovpn/cloud
"""

def decode_base64(encoded):
    # ... (بدون تغییر، همان کد قبلی شما) ...
    decoded = ""
    for encoding in ["utf-8", "iso-8859-1"]:
        try:
            if isinstance(encoded, bytes):
                padded = encoded + b"=" * (-len(encoded) % 4)
            else:
                padded = encoded.encode() + b"=" * (-len(encoded) % 4)
            decoded = pybase64.b64decode(padded).decode(encoding)
            break
        except (UnicodeDecodeError, binascii.Error):
            pass
    return decoded


def get_max_pages(base_url):
    # ... (بدون تغییر، همان کد قبلی شما) ...
    try:
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, "html.parser")
        pagination = soup.find("ul", class_="pagination justify-content-center")
        if pagination:
            page_links = pagination.find_all("a", class_="page-link")
            page_numbers = []
            for link in page_links:
                href = link.get("href", "")
                if href.startswith("?page="):
                    try:
                        page_num = int(href.split("=")[-1])
                        page_numbers.append(page_num)
                    except ValueError:
                        pass
            return max(page_numbers) if page_numbers else 1
        return 1
    except requests.RequestException:
        return 1

def fetch_url_config(url):
    # ... (بدون تغییر، همان کد قبلی شما) ...
    try:
        response = requests.get(url, timeout=10)
        return decode_base64(response.content) if response.content else ""
    except requests.RequestException:
        return ""


def fetch_server_config(server_url):
    # ... (بدون تغییر، همان کد قبلی شما) ...
    try:
        response = requests.get(server_url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        config_div = soup.find("textarea", {"id": "config"})
        if config_div and config_div.get("data-config"):
            return config_div.get("data-config")
        return None
    except requests.RequestException:
        return None

def scrape_v2nodes_links(base_url):
    # ... (بدون تغییر، همان کد قبلی شما) ...
    max_pages = get_max_pages(base_url)
    links = []
    for page in range(1, max_pages + 1):
        try:
            page_url = f"{base_url}?page={page}"
            response = requests.get(page_url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            servers = soup.find_all("div", class_="col-md-12 servers")
            server_urls = [f"{base_url}/servers/{server.get('data-id')}/" for server in servers if server.get("data-id")]
            links.extend(server_urls)
        except requests.RequestException:
            pass
    return links

def decode_urls(urls):
    # ... (بدون تغییر، همان کد قبلی شما) ...
    decoded_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        future_to_url = {executor.submit(fetch_url_config, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            config = future.result()
            if config:
                decoded_data.append(config)
    return decoded_data

def decode_links(links):
    # ... (بدون تغییر، همان کد قبلی شما) ...
    decoded_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        future_to_url = {executor.submit(fetch_server_config, url): url for url in links}
        for future in concurrent.futures.as_completed(future_to_url):
            config = future.result()
            if config:
                decoded_data.append(config)
    return decoded_data

def filter_for_protocols(data, protocols):
    # ... (بدون تغییر، همان کد قبلی شما) ...
    filtered_data = []
    for line in data:
        for config_line in (line.splitlines() if "\n" in line else [line]):
            if any(protocol in config_line for protocol in protocols):
                filtered_data.append(config_line)
    return filtered_data

# ---> تابع جدید برای تغییر نام <---
def rename_configs(configs, new_name):
    renamed_configs = []
    for config in configs:
        # پیدا کردن موقعیت # برای جدا کردن نام
        if '#' in config:
            base_config = config.split('#')[0]
        else:
            base_config = config
        
        # اضافه کردن نام جدید
        renamed_config = f"{base_config}#{new_name}"
        renamed_configs.append(renamed_config)
    return renamed_configs

def ensure_directories_exist():
    output_folder = os.path.abspath(os.path.join(os.getcwd(), ".."))
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    return output_folder

# ---> منطق اصلی به یک تابع منتقل شد <---
def run_scrape():
    print("Scraping and merging configs...")
    output_folder = ensure_directories_exist()
    protocols = ["vmess", "vless", "trojan", "ss", "ssr"]
    links = [
        "https://shadowmere.xyz/api/b64sub",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_BASE64.txt",
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity"
    ]
    base_url = "https://v2nodes.com"

    decoded_links = decode_urls(links)
    v2nodes_links = scrape_v2nodes_links(base_url)
    v2nodes_configs = decode_links(v2nodes_links)
    
    merged_configs = filter_for_protocols(decoded_links + v2nodes_configs, protocols)
    
    # ---> فراخوانی تابع تغییر نام <---
    renamed_merged_configs = rename_configs(merged_configs, "@proxyfig")

    output_filename = os.path.join(output_folder, "All_Configs_Sub.txt")
    base64_filename = os.path.join(output_folder, "All_Configs_Base64.txt")

    # پاک کردن فایل‌های قبلی
    if os.path.exists(output_filename):
        os.remove(output_filename)
    if os.path.exists(base64_filename):
        os.remove(base64_filename)

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(fixed_text)
        for config in renamed_merged_configs:
            f.write(config + "\n")

    with open(output_filename, "r", encoding="utf-8") as input_file:
        config_data = input_file.read()

    with open(base64_filename, "w", encoding="utf-8") as output_file:
        encoded_config = base64.b64encode(config_data.encode("utf-8")).decode("utf-8")
        output_file.write(encoded_config)
    print("Scraping finished and files created.")

if __name__ == "__main__":
    run_scrape()
