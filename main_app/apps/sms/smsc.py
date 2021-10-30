import requests

def smsc_send_call_code(
    smsc_login: str,
    smsc_password: str,
    phone: str,
):
    base_url = "https://smsc.ru/sys/send.php"   
    params = {
        "login": smsc_login,
        "psw": smsc_password,
        "phones": phone,
        "mes": "code",
        "call": "1",
        "fmt": 3,
    }
    response = requests.get(base_url, params = params).json()
    if 'error' in response:
        return False, None
    code = response['code']
    # get only 4 last digets of 6 digets code
    code_final = code[2:]
    return True, code_final
