import requests
import time

#important variables
API_KEY = "465f7078-6d47-47c4-8b20-e24b35447d56"  # Your Helius API key
YOUR_WALLET_ADDRESS = 'B1ADY4MfWfeQtoT71jXQT8MvE1Z86s4Ug7ysHdjup4aM'
SENDER_WALLET_ADDRESS = 'ChGA1Wbh9WN8MDiQ4ggA5PzBspS2Z6QheyaxdVo3XdW6'
IMG_WALLET = 'imgXJgVM2oFdVyLXuZSwdsPEB5e9PBZcst51tF3T7nR'



# Helius RPC for signature fetching
RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={API_KEY}"
# Helius /v0/transactions endpoint for decoding
DECODE_URL = f"https://api.helius.xyz/v0/transactions?api-key={API_KEY}"

# State
seen_signatures = set()

def get_latest_signatures(address, limit=5):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [address, {"limit": limit}]
    }
    response = requests.post(RPC_URL, json=payload)
    if response.status_code != 200:
        print("Signature fetch error:", response.text)
        return []

    return [sig["signature"] for sig in response.json().get("result", [])]

def decode_transactions(signatures):
    if not signatures:
        return []

    payload = { "transactions": signatures }
    response = requests.post(DECODE_URL, json=payload)
    if response.status_code != 200:
        print("Decode error:", response.text)
        return []

    return response.json()

BOT_TOKEN = "8165577128:AAFRkc1fyHfUfSQJD9Da6GqUPQT0KO6w1yw"
CHAT_ID = "6606128113"


def process_transactions(transactions):
    for txn in transactions:
        sig = txn.get("signature")
        swap_events = txn.get("swapEvents", [])
        for swap in swap_events:
             if swap.get("user") == IMG_WALLET:
                token_in = swap["tokenIn"]
                token_out = swap["tokenOut"]

                message = (
                    f"🚨 *IMG Wallet Sell Detected!*\n\n"
                    f"*Tx:* [View on Solscan](https://solscan.io/tx/{sig})\n"
                    f"*Sold:* {token_in['amount']} of `{token_in['mint']}`\n"
                    f"*Received:* {token_out['amount']} of `{token_out['mint']}`"
                    )

                print(message)
                send_telegram_alert(BOT_TOKEN, CHAT_ID, message)
                
def send_telegram_alert(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"  # Allows links & formatting
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print("❌ Telegram error:", response.text)


send_telegram_alert(BOT_TOKEN, CHAT_ID, "✅ Test message from your bot!")
# Polling Loop
print("⏳ Listening for sell events from IMG wallet...")
while True:
    try:
        latest_signatures = get_latest_signatures(IMG_WALLET, limit=5)
        new_signatures = [sig for sig in latest_signatures if sig not in seen_signatures]
        seen_signatures.update(new_signatures)

        if new_signatures:
            transactions = decode_transactions(new_signatures)
            process_transactions(transactions)

    except Exception as e:
        print("❌ Error:", e)

    time.sleep(15)  # Check every 15 seconds