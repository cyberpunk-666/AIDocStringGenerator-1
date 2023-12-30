import time
import requests
import uuid
import websocket
import json
import threading

class BingChatBot:
    _brandId = "bingChat"
    _className = "BingChatBot"
    _model = "h3precise"
    _logoFilename = "bing-logo.svg"
    _loginUrl = "https://www.bing.com/chat"
    _userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.48"

    _optionsSets = None
    _tone = ""

    def __init__(self):
        self.conversation = None
        self.context = {}

    def send_prompt(self, prompt, on_update_response, callback_param):
        # If not logged in, handle the error
        # if not self.is_available():
        #     on_update_response(callback_param, {
        #         "content": f"Bot Bing not available",
        #         "done": True,
        #     })
        #     return

        try:
            self._execute_send_prompt(prompt, on_update_response, callback_param)
        except Exception as err:
            print(f"Error sending prompt to Bing: {err}")
            message = str(err)
            # Handle different types of errors if necessary
            on_update_response(callback_param, {
                "content": message,
                "done": True,
            })

    def _execute_send_prompt(self, prompt, on_update_response, callback_param):
        # Begin thinking...
        on_update_response(callback_param, {"content": "...", "done": False})
        self._send_prompt(prompt, on_update_response, callback_param)


    def create_chat_context(self):
        # headers = {
        #     "x-ms-client-request-id": str(uuid.uuid4()),
        #     "x-ms-useragent": "azsdk-js-api-client-factory/1.0.0-beta.1 core-rest-pipeline/1.10.3 OS/macOS",
        # }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/XX.X.XXXX.XX Safari/537.36'
        }        
        response = requests.get("https://www.bing.com/turing/conversation/create", headers=headers)
        if response.status_code == 200 and response.json().get('result', {}).get('value') == "Success":
            self.conversation = {
                "clientId": response.json()['clientId'],
                "conversationId": response.json()['conversationId'],
                "conversationSignature": response.json().get('conversationSignature', response.headers.get("x-sydney-conversationsignature")),
                "secAccessToken": response.headers.get("x-sydney-encryptedconversationsignature"),
                "invocationId": 0,
            }
            return self.conversation
        else:
            raise Exception("Error creating Bing Chat conversation: {}".format(response.json()))

    def make_prompt_request(self, prompt):
        if not self.conversation:
            raise Exception("No conversation context available")

        request_id = str(uuid.uuid4())
        return {
            "arguments": [
                {
                    # Other fields as per your requirement
                    "requestId": request_id,
                    "message": {
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "author": "user",
                        "inputMethod": "Keyboard",
                        "text": prompt,
                        "messageType": "Chat",
                        "requestId": request_id,
                        "messageId": request_id,
                    },
                    "conversationId": self.conversation["conversationId"],
                }
            ],
            "invocationId": str(self.conversation["invocationId"]),
            "target": "chat",
            "type": 4,
        }

    def is_available(self):
        available = False

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/XX.X.XXXX.XX Safari/537.36'
            }        
            response = requests.get("https://www.bing.com/turing/conversation/chats", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                available = data.get('result', {}).get('value') == "Success" and not self.is_anonymous(data.get('clientId'))
            else:
                print(f"Error checking Bing Chat login status: {response.status_code}")

        except requests.RequestException as error:
            print(f"Error checking Bing Chat login status: {error}")

        return available

    def is_anonymous(self, client_id):
        # Implement your logic to check if a client is anonymous
        return len(client_id) > 30 if client_id else False

    def _send_prompt(self, prompt, on_update_response, callback_param):
        context = self.create_chat_context()
        if not context:
            raise Exception("Failed to create chat context")


        def parse_response(event, on_update_response, callback_param, wsp):
            if event == {}:
                wsp.send(json.dumps({"type": 6}))
                wsp.send(json.dumps(self.make_prompt_request(prompt)))
                self.context["invocationId"] += 1
                self.set_chat_context(self.context)
            elif event['type'] == 6:
                wsp.send(json.dumps({"type": 6}))
            elif event['type'] == 3:
                on_update_response(callback_param, {"done": True})
                return
            elif event['type'] == 2:
                if event['item']['result']['value'] != "Success":
                    print(f"Error sending prompt to Bing Chat: {event}")
                    if event['item']['result']['value'] == "InvalidSession":
                        context = self.create_chat_context()
                        self.set_chat_context(context)
                        self.send_prompt(prompt, on_update_response, callback_param)
                        raise Exception("bot.creatingConversation")
                    elif event['item']['result']['value'] == "Throttled":
                        if self.is_anonymous(self.context['clientId']):
                            self.set_chat_context(None)
                            raise Exception(event['item']['result']['message'])
                        else:
                            raise Exception(event['item']['result']['message'])
                    elif event['item']['result']['value'] == "CaptchaChallenge":
                        url = "https://www.bing.com/turing/captcha/challenge"
                        on_update_response(callback_param, {
                            "content": f'bingChat.solveCaptcha, attributes=href="{url}" title="{url}" target="innerWindow"',
                            "format": "html",
                            "done": False,
                        })
                    else:
                        raise Exception(f"{event['item']['result']['message']} ({event['item']['result']['value']})")
                elif event['item']['throttling']['maxNumUserMessagesInConversation'] == event['item']['throttling']['numUserMessagesInConversation']:
                    context = self.create_chat_context()
                    self.set_chat_context(context)
                return
            elif event['type'] == 1:
                if len(event['arguments'][0]['messages']) > 0:
                    message = event['arguments'][0]['messages'][0]
                    beginning = ""
                    ending = ""
                    if message['messageType'] == "InternalSearchQuery":
                        beginning += "> " + message['text'] + "\n"
                    else:
                        body = message['adaptiveCards'][0]['body'][0]['text']
                        more_links = message['adaptiveCards'][0]['body'][1]['text']
                        if more_links is not None:
                            ending = f"> {more_links}"
                        on_update_response(callback_param, {
                            "content": f"{beginning}\n{body}\n{ending}",
                            "done": False,
                        })
            elif event['type'] == 7:
                raise Exception(event['error'])
            else:
                print(f"Unknown Bing Chat response: {event}")

        def on_message(ws, message):
            # Process incoming WebSocket messages
            try:
                print(f"Received message: {message}")
                messages = message.split(chr(30))  # Splitting by separator
                for msg in messages:
                    if msg:
                        event = json.loads(msg)
                        parse_response(event, on_update_response, callback_param, ws)
            except Exception as e:
                print(f"Error processing message: {e}")

        def on_error(ws, error):
            print(f"WebSocket error: {error}")

        def on_close(ws, close_status_code, close_msg):
            print(f"WebSocket closed with code: {close_status_code}, message: {close_msg}")

        def on_open(ws):
            print("WebSocket connection opened")
            ws.send(json.dumps({"protocol": "json", "version": 1}) + chr(30))

        websocket_url = f"wss://sydney.bing.com/sydney/ChatHub?sec_access_token={context['secAccessToken']}"
        ws = websocket.WebSocketApp(websocket_url,
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)

        def run(*args):
            ws.run_forever()

        ws_thread = threading.Thread(target=run)
        ws_thread.start()

        # Waiting for WebSocket connection to open
        time.sleep(1)

        # Send initial message to start conversation
        prompt_request = self.make_prompt_request(prompt)
        ws.send(json.dumps(prompt_request) + chr(30))





    def set_chat_context(self, context):
        self.context = context


# Instantiate and use the BingChatBot class
bing_bot = BingChatBot()
def on_update_response(callback_param, response):
    print(response)

response = bing_bot.send_prompt("What is the color of the sky", on_update_response, None)
print(response)