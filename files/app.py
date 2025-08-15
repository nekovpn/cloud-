# cloud--main/files/app.py

import pybase64, base64, binascii, requests, os, concurrent.futures
from bs4 import BeautifulSoup

fixed_text = """#profile-title: base64:VjJSYXkgQ29uZmlncw==
#profile-update-interval: 1
#subscription-userinfo: upload=29; download=12; total=10737418240000000; expire=2546249531
#support-url: https://github.com/nekovpn/cloud
#profile-web-page-url: https://github.com/nekovpn/cloud
"""

def decode_base64(encoded):
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
    try:
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, "html.parser")
        pagination = soup.find("ul", class_="pagination justify-content-center")
        if pagination:
            page_links = pagination.find_all("a", class_="page-link")
            page_numbers = [int(link.get("href").split("=")[-1]) for link in page_links if link.get("href", "").startswith("?page=")]
            return max(page_numbers) if page_numbers else 1
        return 1
    except requests.RequestException:
        return 1

def fetch_url_config(url):
    try:
        response = requests.get(url, timeout=10)
        return decode_base64(response.content) if response.content else ""
    except requests.RequestException:
        return ""

def fetch_server_config(server_url):
    try:
        response = requests.get(server_url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        config_div = soup.find("textarea", {"id": "config"})
        return config_div.get("data-config") if config_div and config_div.get("data-config") else None
    except requests.RequestException:
        return None

def scrape_v2nodes_links(base_url):
    max_pages = get_max_pages(base_url)
    links = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_page = {executor.submit(requests.get, f"{base_url}?page={page}", timeout=10): page for page in range(1, max_pages + 1)}
        for future in concurrent.futures.as_completed(future_to_page):
            try:
                response = future.result()
                soup = BeautifulSoup(response.text, "html.parser")
                servers = soup.find_all("div", class_="col-md-12 servers")
                links.extend([f"{base_url}/servers/{server.get('data-id')}/" for server in servers if server.get("data-id")])
            except requests.RequestException:
                pass
    return links

def decode_data(fetch_function, items):
    decoded_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        future_to_item = {executor.submit(fetch_function, item): item for item in items}
        for future in concurrent.futures.as_completed(future_to_item):
            config = future.result()
            if config:
                decoded_data.append(config)
    return decoded_data

def filter_and_rename_configs(data, protocols, new_name):
    filtered_configs = []
    for line in data:
        for config_line in (line.splitlines() if "\n" in line else [line]):
            if any(config_line.startswith(p) for p in protocols):
                base_config = config_line.split('#')[0]
                renamed_config = f"{base_config}#{new_name}"
                filtered_configs.append(renamed_config)
    return filtered_configs

def run_scrape():
    print("Scraping and merging configs...")
    output_folder = os.path.abspath(os.path.join(os.getcwd(), ".")) # فایل‌ها در ریشه پروژه ساخته می‌شوند
    protocols = ["vmess", "vless", "trojan", "ss"]
    links = [
        "https://shadowmere.xyz/api/b64sub",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_BASE64.txt",
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity"
    ]
    base_url = "https://v2nodes.com"

    decoded_links = decode_data(fetch_url_config, links)
    v2nodes_links = scrape_v2nodes_links(base_url)
    v2nodes_configs = decode_data(fetch_server_config, v2nodes_links)
    
    merged_configs = decoded_links + v2nodes_configs
    renamed_configs = filter_and_rename_configs(merged_configs, protocols, "@proxyfig")

    output_filename = os.path.join(output_folder, "All_Configs_Sub.txt")
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(fixed_text)
        f.write("\n".join(renamed_configs) + "\n")
    
    with open(output_filename, "r", encoding="utf-8") as input_file:
        config_data = input_file.read()
    
    base64_filename = os.path.join(output_folder, "All_Configs_Base64.txt")
    with open(base64_filename, "w", encoding="utf-8") as output_file:
        encoded_config = base64.b64encode(config_data.encode("utf-8")).decode("utf-8")
        output_file.write(encoded_config)
        
    print("Scraping finished and files created.")

if __name__ == "__main__":
    run_scrape()
