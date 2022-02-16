import requests
import time

def change_proxy(api_key='TLFbLjVMCcEdZLMdvI4mpjyWl3vUJjKEzhNIBX'):
    try:
        response = requests.get(f'http://proxy.tinsoftsv.com/api/changeProxy.php?key={api_key}').json()
        print(response)
        if not response['success']:
            if response['description'] == 'wrong key!':
                return None
            time.sleep(response['next_change'] + 6)
            return change_proxy(api_key)
        return['proxy']
    except:
        time.sleep(6)
        return change_proxy(api_key)

if __name__ == '__main__':
    print(change_proxy())