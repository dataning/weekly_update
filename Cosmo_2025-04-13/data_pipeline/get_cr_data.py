import json
import os
import asyncio
import requests
import pandas as pd
from datetime import datetime, timedelta

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

CONFIG_FILE = "config.json"

def load_config():
    """
    Load configuration from config.json, creating a default
    file if it does not exist, and returning that configuration.
    """
    default_config = {
        "criticalmention": {
            "username": None,
            "password": None,
            "default_token": None,
            "alert_ids": "4360,89440,137678,4358",
            "days": 7,
            "output_dir": ".",
            "limit": 100,
            "headless": True,
            "cookie_expiry_days": 7,
            "token_history": [],
            "last_updated": None
        }
    }

    if not os.path.exists(CONFIG_FILE):
        # If config.json doesn't exist, create it with defaults
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=2)
        return default_config

    # If config.json does exist, load it
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error reading {CONFIG_FILE}: {e}")
        # Fall back to default config in case of error
        return default_config

    # Update any missing fields with defaults
    for key, value in default_config["criticalmention"].items():
        if key not in config["criticalmention"]:
            config["criticalmention"][key] = value

    return config

def save_config(config):
    """
    Save updated config back to config.json.
    """
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error writing {CONFIG_FILE}: {e}")
        return False

class CriticalMentionAPI:
    """Simple API client for Critical Mention using only config.json"""

    def __init__(self, auth_token=None):
        self.auth_token = auth_token
        self.base_url = "https://app.criticalmention.com"

    def get_headers_and_cookies(self):
        """
        Return the headers and cookies needed for the API request.
        We inject the auth token as a cookie named 'Authorization'.
        """
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive"
        }

        cookies = {
            "Authorization": self.auth_token
        }
        return headers, cookies

    def fetch_content(self, start_date=None, end_date=None, alert_ids=None, limit=100):
        """
        Fetch content from the API using the auth token from config.
        """
        if not self.auth_token:
            print("No authorization token provided.")
            return []

        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d 23:59:59")

        # If alert_ids is a string with commas, pass it through
        if isinstance(alert_ids, str):
            alert_ids = alert_ids.strip()

        params = {
            "limit": str(limit),
            "start": start_date,
            "end": end_date,
            "ascdesc": "desc",
            "page": "1",
            "timezone": "America/New_York",
            "data_source_ids": "2,1,7,5",
            "sort_order": "timestamp",
            "updatedMapping": "true",
        }

        if alert_ids:
            params["alert_ids"] = alert_ids

        print("\n=== API Request Parameters ===")
        for k, v in params.items():
            print(f"{k}: {v}")

        headers, cookies = self.get_headers_and_cookies()

        try:
            response = requests.get(
                f"{self.base_url}/allmedia/dashboard/content",
                params=params,
                headers=headers,
                cookies=cookies,
                timeout=30
            )
            print(f"Response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                clips = data.get("results", {}).get("clips", [])
                print(f"Found {len(clips)} clips")
                return clips
            elif response.status_code == 401:
                print("Authentication failed (401). Token might be expired.")
                return []
            else:
                print(f"Error response: {response.status_code}")
                print(f"Error details: {response.text[:500]}")
                return []
        except Exception as e:
            print(f"Error fetching content: {e}")
            return []

    def create_dataframe(self, clips):
        """Convert clips to a Pandas DataFrame with explicit datetime parsing."""
        if not clips:
            print("No clips data available.")
            return pd.DataFrame()

        df = pd.DataFrame(clips)

        # Attempt to convert time/timestamp columns
        # If your date strings always match '%Y-%m-%d %H:%M:%S EDT' format,
        # remove the trailing " EDT" and parse as '%Y-%m-%d %H:%M:%S'
        for col in ["time", "timestamp"]:
            if col in df.columns:
                try:
                    df[col] = (
                        df[col]
                        .astype(str)  # Ensure it's a string
                        .str.replace(" EDT", "", regex=False)
                        .pipe(
                            pd.to_datetime,
                            format="%Y-%m-%d %H:%M:%S",
                            errors="coerce"
                        )
                    )
                except Exception as e:
                    print(f"Could not convert {col}: {e}")

        return df

async def get_token_automatically(headless=True):
    """
    Use Playwright to log in to Critical Mention, capture token
    from cookies or network requests, and return it.
    """
    if not PLAYWRIGHT_AVAILABLE:
        print("Playwright not installed. Cannot automate token retrieval.")
        return None

    config = load_config()
    username = config["criticalmention"]["username"]
    password = config["criticalmention"]["password"]

    if not username or not password:
        print("No username/password found in config.json. Cannot auto-login.")
        return None

    print("\nAttempting to automatically retrieve token (Playwright).")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context()
            page = await context.new_page()

            # 1. Go to the Critical Mention site
            await page.goto("https://app.criticalmention.com/")
            await page.wait_for_load_state("domcontentloaded")

            # 2. If redirected to Onclusive Auth login, enter credentials
            if "auth.onclusive.com" in page.url or "onclusive.auth0.com" in page.url:
                print("Entering login credentials...")

                # Enter username
                await page.wait_for_selector('input[name="username"]', timeout=20000)
                await page.fill('input[name="username"]', username)
                await page.click('button[type="submit"]')

                # Enter password
                await page.wait_for_selector('input[name="password"]', timeout=20000)
                await page.fill('input[name="password"]', password)
                await page.click('button[type="submit"]')

                # Wait until we are back on criticalmention.com
                await page.wait_for_url("**/app.criticalmention.com/**", timeout=60000)

            # Wait for cookies to be set
            await asyncio.sleep(5)

            # Attempt to find 'Authorization' cookie
            cookies = await context.cookies()
            auth_token = None
            for cookie in cookies:
                if cookie["name"] == "Authorization":
                    auth_token = cookie["value"]
                    break

            # If not found, try network-based approach
            if not auth_token:
                # We'll intercept requests to see if there's an 'Authorization' header
                token_found = asyncio.Event()

                def handle_request(request):
                    nonlocal auth_token
                    headers = request.headers
                    if "authorization" in headers and headers["authorization"].startswith("eyJ"):
                        auth_token = headers["authorization"]
                        token_found.set()

                page.on("request", handle_request)

                # Force a page that triggers an API call
                await page.goto("https://app.criticalmention.com/allmedia/dashboard")
                try:
                    await asyncio.wait_for(token_found.wait(), timeout=10)
                except asyncio.TimeoutError:
                    pass

            # Close browser
            await browser.close()

            # Return whatever we found
            if auth_token:
                print("Token retrieved successfully (Playwright).")
                return auth_token
            else:
                print("Could not retrieve token automatically.")
                return None
    except Exception as e:
        print(f"Playwright error: {e}")
        return None

async def update_token():
    """
    Update token by:
    1. Trying auto-retrieval (Playwright).
    2. If that fails, ask user to paste in a token manually.
    3. Save new token to config.json.
    """
    config = load_config()

    # 1. Attempt automatic retrieval (if Playwright is available)
    if PLAYWRIGHT_AVAILABLE:
        new_token = await get_token_automatically(headless=config["criticalmention"]["headless"])
        if new_token and new_token.startswith("eyJ"):
            # Save old token to token history
            old_token = config["criticalmention"]["default_token"]
            if old_token:
                config["criticalmention"]["token_history"].append({
                    "token": old_token,
                    "replaced_at": str(datetime.now())
                })
            # Update config
            config["criticalmention"]["default_token"] = new_token
            config["criticalmention"]["last_updated"] = str(datetime.now())
            save_config(config)
            return new_token

    # 2. Manual token input
    print("\nAutomatic token retrieval failed or is unavailable.")
    print("Please open your browser dev tools after logging in to app.criticalmention.com.")
    print("Locate a request with an 'Authorization' cookie/header that starts with 'eyJ'.")
    new_token = input("Paste your new token here: ").strip()

    if not new_token.startswith("eyJ"):
        print("That doesn't look like a valid JWT (must start with eyJ).")
        return None

    # Save old token to history
    old_token = config["criticalmention"]["default_token"]
    if old_token:
        config["criticalmention"]["token_history"].append({
            "token": old_token,
            "replaced_at": str(datetime.now())
        })

    # Update config
    config["criticalmention"]["default_token"] = new_token
    config["criticalmention"]["last_updated"] = str(datetime.now())
    save_config(config)

    print("New token saved.")
    return new_token

async def fetch_data_from_criticalmention():
    """
    Main async function to:
    - Load config (username, password, token, etc.)
    - Attempt to fetch data from the Critical Mention API
    - If token is expired, prompt update
    - Return Pandas DataFrame
    """
    config = load_config()

    # Grab everything from config
    alert_ids = config["criticalmention"]["alert_ids"]
    days = config["criticalmention"]["days"]
    limit = config["criticalmention"]["limit"]
    default_token = config["criticalmention"]["default_token"]

    if not default_token:
        print("No token in config.json. Attempting to retrieve a new one...")
        default_token = await update_token()
        if not default_token:
            print("Unable to proceed without a valid token.")
            return None

    # Prepare API
    api = CriticalMentionAPI(auth_token=default_token)

    # Calculate date range
    end_date = datetime.now().strftime("%Y-%m-%d 23:59:59")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d 00:00:00")

    # Fetch
    clips = api.fetch_content(
        start_date=start_date,
        end_date=end_date,
        alert_ids=alert_ids,
        limit=limit
    )

    # If empty, try updating token
    if not clips:
        print("No clips returned. Possibly the token is expired.")
        user_input = input("Would you like to update the token and retry? (y/n): ").lower()
        if user_input == "y":
            new_token = await update_token()
            if new_token:
                api = CriticalMentionAPI(auth_token=new_token)
                clips = api.fetch_content(
                    start_date=start_date,
                    end_date=end_date,
                    alert_ids=alert_ids,
                    limit=limit
                )

    if not clips:
        print("No clips found or request failed.")
        return None

    # Convert to DataFrame
    df = api.create_dataframe(clips)
    if df.empty:
        print("Received data but no valid clips to display.")
        return None

    # Optionally save to Parquet
    timestamp = datetime.now().strftime("%Y-%m-%d_%H")
    output_filename = f"CR_daily_{timestamp}.parquet"
    df.to_parquet(output_filename, index=False)
    print(f"Saved to {output_filename}. Retrieved {len(df)} records.")

    return df

def get_critical_mention_data():
    """
    User-friendly, synchronous function to fetch data. 
    Call this in your script or notebook.
    """
    try:
        return asyncio.run(fetch_data_from_criticalmention())
    except Exception as e:
        print(f"Error: {e}")
        return None

def save_user_credentials(email, password):
    """
    Updates username/password in config.json for Playwright auto-login.
    """
    config = load_config()
    config["criticalmention"]["username"] = email
    config["criticalmention"]["password"] = password
    saved = save_config(config)
    if saved:
        print("Username and password updated in config.json.")
    else:
        print("Failed to update config.json.")
    return saved

def update_auth_token():
    """
    User-friendly, synchronous function to update token (Playwright or manual).
    """
    try:
        new_token = asyncio.run(update_token())
        if new_token:
            print("Token updated successfully.")
        return new_token is not None
    except Exception as e:
        print(f"Error updating token: {e}")
        return False

if __name__ == "__main__":
    print("=== Critical Mention Single-Config Script ===")
    print("1. Call save_user_credentials(email, password) to store your login.")
    print("2. Call update_auth_token() to auto/manual retrieve a new token.")
    print("3. Call get_critical_mention_data() to fetch data as a DataFrame.")
    print("---")
    df = get_critical_mention_data()
    print(df)