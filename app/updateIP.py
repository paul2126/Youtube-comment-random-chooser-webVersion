import requests
import configparser

config = configparser.ConfigParser()
config.read("/etc/letsencrypt/cloudflare.ini")
# Configuration
CLOUDFLARE_API_TOKEN = config["CLOUDFLARE"]["CLOUDFLARE_API_TOKEN"]
ZONE_ID = config["CLOUDFLARE"]["ZONE_ID"]  # Find this in Cloudflare's dashboard under DNS
RECORD_ID = config["CLOUDFLARE"]["RECORD_ID"]  # Get this by listing DNS records via API
RECORD_NAME = config["CLOUDFLARE"]["RECORD_NAME"]  # The domain you want to update

# Fetch current public IP
def get_public_ip():
    response = requests.get("https://api.ipify.org?format=json")
    return response.json()["ip"]

# Update Cloudflare DNS record
def update_cloudflare_dns(ip):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{RECORD_ID}"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "type": "A",
        "name": RECORD_NAME,
        "content": ip,
        "ttl": 1,
        "proxied": True,
    }
    response = requests.put(url, headers=headers, json=data)
    return response.json()

# Main script
if __name__ == "__main__":
    public_ip = get_public_ip()
    result = update_cloudflare_dns(public_ip)
    print(result)
