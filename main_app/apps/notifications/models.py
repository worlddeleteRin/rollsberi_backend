from pydantic import BaseModel
import httpx

class TelegramBot(BaseModel):
    api_url: str = "https://api.telegram.org/bot"
    username: str
    access_token: str

    def send_msg(self, chat_id: str, msg: str):
        req_url = self.api_url + self.access_token + "/sendMessage"
        print('request url is', req_url)
        data = {
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "MarkdownV2",
        }
        resp = httpx.post(req_url, data = data)
        print('resp is', resp.json())
