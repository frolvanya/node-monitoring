import json
import requests

import os
import time


def send_message(api, chat_id, message):
    api_url = f"https://api.telegram.org/bot{api}/sendMessage"

    try:
        response = requests.post(api_url, json={"chat_id": chat_id, "text": message})
        print(response.text)
    except Exception as err:
        print(f"Unable to send telegram message due to: {err}")


def main():
    api = os.getenv("GRAFANA_BOT_API")
    chat_id = "-1001216990785"

    network = "https://rpc.mainnet.near.org"
    headers = {"Content-type": "application/json", "Accept": "application/json"}
    try:
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "dontcare",
                "method": "validators",
                "params": "latest",
            }
        )
    except Exception as err:
        print(f"Unable to dump data due to: {err}")
        exit(1)

    logs = open("logs.txt", "r+")
    try:
        prev_delta = int(logs.read().splitlines()[-1].strip())
    except:
        prev_delta = None

    try:
        response = requests.post(network, data=data, headers=headers)
    except Exception as err:
        print(f"Unable to send POST request due to: {err}")
        time.sleep(5)
        exit(1)

    try:
        response_json = json.loads(response.text)
    except Exception as err:
        print(f"Unable to load response due to: {err}")
        time.sleep(5)
        exit(1)

    for account in response_json["result"]["current_validators"]:
        if account["account_id"] == "qbit.poolv1.near":
            curr_delta = account["num_expected_blocks"] - account["num_produced_blocks"]
            curr_delta += (
                account["num_expected_chunks"] - account["num_produced_chunks"]
            )

            if (
                prev_delta != curr_delta
                and curr_delta >= 10
                and account["num_produced_blocks"] < account["num_expected_blocks"]
            ):
                send_message(
                    api,
                    chat_id,
                    f"Not enough blocks were produced ({account['num_produced_blocks']} produced / {account['num_expected_blocks']} expected)\n\nhttps://nearscope.net/validator/qbit.poolv1.near",
                )

            if (
                prev_delta != curr_delta
                and curr_delta >= 10
                and account["num_produced_chunks"] < account["num_expected_chunks"]
            ):
                send_message(
                    api,
                    chat_id,
                    f"Not enough chunks were produced ({account['num_produced_chunks']} produced / {account['num_expected_chunks']} expected)\n\nhttps://nearscope.net/validator/qbit.poolv1.near",
                )

            if prev_delta != curr_delta:
                logs.write(str(curr_delta) + "\n")

            break


if __name__ == "__main__":
    main()
