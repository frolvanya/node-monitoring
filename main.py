import os
import time

import requests


def send_message(api, chat_id, message):
    api_url = f"https://api.telegram.org/bot{api}/sendMessage"

    try:
        response = requests.post(api_url, json={"chat_id": chat_id, "text": message})
        print(response.text)
    except Exception as err:
        print(f"Unable to send telegram message due to: {err}")


def main():
    near_validator_account_id = os.getenv("NEAR_VALIDATOR_ACCOUNT_ID")
    telegram_bot_api_key = os.getenv("TELEGRAM_BOT_API_KEY")
    telegram_notifications_chat_id = os.getenv("TELEGRAM_NOTIFICATIONS_CHAT_ID")
    near_rpc_url = os.getenv("NEAR_RPC_URL", "https://rpc.mainnet.near.org")

    near_validators_info = None
    for _retry_attempts_left in range(10):
        try:
            near_validators_info = requests.post(
                near_rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": "dontcare",
                    "method": "validators",
                    "params": "latest",
                }
            ).json()
        except Exception as err:
            print(f"Unable to send POST request due to: {err}")
            time.sleep(5)
        break
    if not near_validators_info:
        exit(1)

    monitored_validator_account_stats = next(
        (account for account in near_validators_info["result"]["current_validators"]
            if account["account_id"] == near_validator_account_id),
        None
    )

    with open("logs.txt", "r") as logs_file:
        try:
            prev_delta = int(logs_file.read().strip())
        except:
            prev_delta = None

    if monitored_validator_account_stats is None:
        if prev_delta is not None:
            send_message(
                telegram_bot_api_key,
                telegram_notifications_chat_id,
                f"Validator {near_validator_account_id} is not validating current epoch \n\nhttps://nearscope.net/validator/{near_validator_account_id}",
            )

            with open("logs.txt", "w") as logs_file:
                pass
        return

    curr_delta = (
        monitored_validator_account_stats["num_expected_blocks"] - monitored_validator_account_stats["num_produced_blocks"]
        +
        monitored_validator_account_stats["num_expected_chunks"] - monitored_validator_account_stats["num_produced_chunks"]
    )

    if prev_delta != curr_delta:
        if curr_delta >= 10:
            send_message(
                telegram_bot_api_key,
                telegram_notifications_chat_id,
                f"Not enough blocks or chunks were produced\nBlocks: {monitored_validator_account_stats['num_produced_blocks']} produced / {monitored_validator_account_stats['num_expected_blocks']} expected\nChunks: {monitored_validator_account_stats['num_produced_chunks']} produced / {monitored_validator_account_stats['num_expected_chunks']} expected\n\nhttps://nearscope.net/validator/{near_validator_account_id}",
            )

        with open("logs.txt", "w") as logs_file:
            logs_file.write(str(curr_delta))


if __name__ == "__main__":
    main()
