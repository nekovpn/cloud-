# cloud--main/files/sort.py

import os, base64

def run_sort():
    print("Sorting configs by protocol and encoding to Base64...")
    project_root = os.path.abspath(os.path.join(os.getcwd(), "."))
    ptt = os.path.join(project_root, 'Splitted-By-Protocol')
    os.makedirs(ptt, exist_ok=True)

    files = {
        'vmess': os.path.join(ptt, 'vmess.txt'),
        'vless': os.path.join(ptt, 'vless.txt'),
        'trojan': os.path.join(ptt, 'trojan.txt'),
        'ss': os.path.join(ptt, 'ss.txt')
    }

    for file_path in files.values():
        open(file_path, 'w').close()

    configs = {'vmess': [], 'vless': [], 'trojan': [], 'ss': []}

    try:
        sub_file_path = os.path.join(project_root, 'All_Configs_Sub.txt')
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

    # Encode the content of each file to Base64
    for protocol, data_list in configs.items():
        if data_list:
            # Join all configs into a single string separated by newlines
            content_str = '\n'.join(data_list)
            # Encode the entire string to Base64
            encoded_content = base64.b64encode(content_str.encode('utf-8'))
            # Write the Base64 encoded bytes to the file
            with open(files[protocol], 'wb') as f:
                f.write(encoded_content)

    print("Sorting and encoding finished.")

if __name__ == "__main__":
    run_sort()
