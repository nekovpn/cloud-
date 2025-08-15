# cloud/files/sort.py

import requests, os, base64

def run_sort():
    print("Sorting configs by protocol...")
    ptt = os.path.abspath(os.path.join(os.getcwd(), '.', 'Splitted-By-Protocol'))
    os.makedirs(ptt, exist_ok=True)

    files = {
        'vmess': os.path.join(ptt, 'vmess.txt'),
        'vless': os.path.join(ptt, 'vless.txt'),
        'trojan': os.path.join(ptt, 'trojan.txt'),
        'ss': os.path.join(ptt, 'ss.txt')
    }

    # Clear previous files
    for file in files.values():
        open(file, 'w').close()

    configs = {'vmess': [], 'vless': [], 'trojan': [], 'ss': []}

    try:
        # خواندن فایل از مسیر نسبی صحیح
        sub_file_path = os.path.abspath(os.path.join(os.getcwd(), '.', 'All_Configs_Sub.txt'))
        with open(sub_file_path, 'r', encoding='utf-8') as f:
            response_text = f.read()
            
        for config in response_text.splitlines():
            if config.strip() and not config.startswith('#'):
                for protocol in configs:
                    if config.startswith(f"{protocol}://"):
                        configs[protocol].append(config)
    except Exception as e:
        print(f"Error reading subscription file: {e}")
        return

    # برای شادوساکس، هر خط را جداگانه می‌نویسیم
    if configs['ss']:
        with open(files['ss'], 'w', encoding='utf-8') as f:
            f.write('\n'.join(configs['ss']))

    print("Sorting finished.")

if __name__ == "__main__":
    run_sort()
