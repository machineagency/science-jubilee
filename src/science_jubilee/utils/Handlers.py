import logging
from datetime import datetime

import requests


class SlackInputHandler:
    def __init__(self, webhook, machine_name="Jubilee", notify=None):
        """Sends 'crash detected' message to specified slack webhook, then waits for input from user to resume run

        :param webhook: URL for slack webhook to send message to
        :type webhook: str
        :param machine_name: name of machine to use in message. Default Jubilee
        :type machine_name: str
        :param notify: name of user or group to notify in slack message. ex @channel -> 'channel'
        :type notify: str

        """
        self.webhook = webhook
        self.machine_name = machine_name
        self.notify = notify

    def handle_crash(self):
        self.send_message()
        self.input_hold()
        return

    def send_message(self):
        if self.notify is not None:
            notification = f"<!{self.notify}>"
        else:
            notification = ""

        message = f'{notification} Crash Detected on {self.machine_name} at {datetime.now().strftime("%Y-%m-%d %H:%M")}. Intervention required to proceed with experiment.'
        r = requests.post(self.webhook, json={"text": message})

        print(r)

    def input_hold(self):
        response = input(
            'Is the crash resolved? Enter "All clear" to resume experiment'
        )
        if response == "All clear":
            return
        else:
            self.input_hold()
