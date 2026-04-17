# Slipstream 🌊

**Slipstream** is a stateful, algorithmic portfolio rebalancing engine built for **Coinbase Advanced Trade**. It operates as a high-frequency "skimming" strategy, monitoring your crypto portfolio against mathematically defined target weights. It automatically trims profits from outperforming assets and reallocates capital into dipping assets, executing a disciplined "buy low, sell high" cycle autonomously.

---
### ⚠️ CRITICAL DISCLAIMERS & LIABILITY

### 1. Financial Liability & Beta Status
**By deploying Slipstream, you explicitly acknowledge that automated financial transactions will be executed on your behalf.** The creators, contributors, and maintainers of this software accept **ABSOLUTELY NO LIABILITY** for financial losses, unexpected trades, API timeouts, or liquidation events. 
* This software is provided "as-is" without any warranties. 
* **Extensive real-world stress testing has not yet been completed.** You are deploying beta software. 
* Past performance in mathematical models does not guarantee future results. **Use at your own discretion and risk.**

### 2. Staked Assets Are INCOMPATIBLE
Slipstream is **strictly incompatible** with staked or locked assets. Staked coins are omitted from the Coinbase API's `available_balance`, which causes the engine to perceive a massive "dip" and trigger panic-buys of the "missing" assets while liquidating your other holdings.

**To prevent catastrophic failure, you MUST choose one of the following:**
1. **Dedicated Sub-Portfolio (Recommended):** Use a Coinbase "Sub-Portfolio" strictly for liquid algorithmic trading. Leave staked assets in your Default portfolio.
2. **Manual Blacklisting:** Manually add every staked coin to the Telegram `/ignore` blacklist before starting the engine.

---

## 🚀 Overview

Slipstream is designed for the "ruthless" optimization of a crypto portfolio. Unlike passive "HODL" strategies, Slipstream treats volatility as an opportunity. By maintaining persistent state in a local SQLite database, it tracks High-Water Marks (HWM) and transaction history to ensure every trade is mathematically sound and aligned with your long-term rebalancing goals.

### Key Features:
- **Stateful Engine:** Tracks HWM and trades via SQLite.
- **Mission Control:** Full remote control via a secure Telegram bot.
- **Secure Boot Architecture:** Starts in a safe, paused state to prevent accidental execution.
- **Flexible Rebalancing:** Choose between Waterfall and Proportional math models.
- **Safety Switches:** Trailing stop-loss (Floor) and global panic button.

---

## 🛠 Installation & Setup

### 1. Clone & Environment
Ensure you have Python 3.10+ installed.

```bash
# Clone the repository
git clone https://github.com/Junroll/slipstream.git
cd slipstream

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# IMPORTANT: You must run this command anytime your terminal restarts
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the root directory and populate it with your credentials:

```env
TELEGRAM_BOT_TOKEN="your_bot_token" # From @BotFather
AUTHORIZED_CHAT_ID="your_chat_id"   # From @userinfobot (to restrict access)
COINBASE_API_KEY="your_api_key"
COINBASE_API_SECRET="your_api_secret"
```

*You may also take a look at `.env.example` for this format.*

---

### 3. Obtaining Your API Keys

To bring your `.env` file online, you will need to generate secure keys for both your exchange and your telemetry bot.

**Coinbase Advanced Trade Keys:**
1. Log into the Coinbase Developer Platform.
2. Navigate to **API Keys** and click **Create Key**.
3. **CRITICAL:** If you are using the recommended *Dedicated Sub-Portfolio* method to protect your staked assets, ensure you restrict this API key's access strictly to that specific portfolio.
4. Give the API key Read and Trade permissions (and optionally transfer permissions, though the program does not require it.)
5. Copy your `API Key` and `API Secret` into the `.env` file.

**Telegram Mission Control Keys:**
1. **Bot Token:** Open the Telegram app and search for the verified `@BotFather`. Send the `/newbot` command, follow the prompts to name your bot (e.g., `Slipstream_Engine_Bot`), and copy the provided HTTP API Token.
2. **Authorized Chat ID:** To ensure *only you* have the authority to command the engine, the bot needs your personal numerical ID. Search for `@userinfobot` (or `@getmyid_bot`) on Telegram, hit Start, and copy the numerical `Id` it returns to your `.env` file.

## 🏗 Deployment Sequence (Secure Boot)

Slipstream follows a **"Secure by Default"** architecture to prevent the engine from trading before you've configured your safety settings.

1. **Initialize Database:**
   Run the bot module first. This creates the `crypto_bot.db` file and initializes the system in a **permanently PAUSED** state.
   ```bash
   python3 -m src.bot
   ```

2. **Configure Blacklist:**
   Open your Telegram bot and add any assets you wish to ignore (fiat, staked assets, or long-term holds):
   - `/ignore ETH`
   - `/ignore USDC`
   - `/blacklist` (to verify)

3. **Unlock Engine:**
   Send the `/resume` command via Telegram to move the system from `PAUSED` to `ACTIVE`.

4. **Manual Test Run:**
   Launch the main engine once manually to ensure the database and API are connected.
   ```bash
   python3 -m src.main
   ```
5. **Automating the Engine:**
Slipstream does not contain a built-in scheduler. To run the engine automatically, you must configure a background task on your operating system. **The execution frequency is entirely customizable.**

> ***⚠️ Note:** The more aggressive the execution frequency (e.g., every 5 or 10 minutes), the more transactions the engine might trigger. While this captures micro-profits, it may also result in higher cumulative exchange fees or hit API rate limits in extreme market volatility. Monitor your fee-to-profit ratio closely when running at high frequencies.*

#### 🍏 For Mac & Linux (Cron)
Open your server's crontab:
```
crontab -e
``` 

   - Add one of the following lines depending on how aggressively you want the engine to skim. *(Note: You must replace the placeholder paths with the absolute path to both the virtual environment's Python executable and the Slipstream directory).*
```
    # Example 1: Run every hour at the top of the hour (Recommended Baseline)
0 * * * * cd /absolute/path/to/slipstream && /absolute/path/to/slipstream/venv/bin/python -m src.main

    # Example 2: Run every 30 minutes (Moderate Skimming)
*/30 * * * * cd /absolute/path/to/slipstream && /absolute/path/to/slipstream/venv/bin/python -m src.main

    # Example 3: Run every 10 minutes (Aggressive Skimming)
*/10 * * * * cd /absolute/path/to/slipstream && /absolute/path/to/slipstream/venv/bin/python -m src.main

    # Example 4: Run every 5 minutes (Hyper-Aggressive Skimming)
*/5 * * * * cd /absolute/path/to/slipstream && /absolute/path/to/slipstream/venv/bin/python -m src.main

    # Example 5: Run once a day at Noon (Passive / Low Fee Strategy)
0 12 * * * cd /absolute/path/to/slipstream && /absolute/path/to/slipstream/venv/bin/python -m src.main
```

### 🪟 For Windows (Task Scheduler)
Windows does not use cron. Instead, open your Command Prompt as Administrator and use the schtasks tool.

Run one of the following commands. *(Note: Replace the C:\path\to\slipstream placeholder with your actual folder path. Notice that Windows uses \Scripts\python.exe for the virtual environment).*

```
    :: Example 1: Run every 60 minutes (Recommended Baseline)
schtasks /create /tn "SlipstreamEngine" /tr "cmd.exe /c cd C:\path\to\slipstream && venv\Scripts\python.exe -m src.main" /sc minute /mo 60

    :: Example 2: Run every 30 minutes (Moderate Skimming)
schtasks /create /tn "SlipstreamEngine" /tr "cmd.exe /c cd C:\path\to\slipstream && venv\Scripts\python.exe -m src.main" /sc minute /mo 30

    :: Example 3: Run every 10 minutes (Aggressive Skimming)
schtasks /create /tn "SlipstreamEngine" /tr "cmd.exe /c cd C:\path\to\slipstream && venv\Scripts\python.exe -m src.main" /sc minute /mo 10
```
*Note that :: is used to denote a comment in the Windows Task Scheduler command line.*

---

## 🎮 Telegram Mission Control

The entire engine is controlled remotely. Below are the available commands:

| Command | Action |
| :--- | :--- |
| `/info` | Explains the active Slipstream rebalancing logic. |
| `/status` | View current settings, active alerts, and the High-Water Mark. |
| `/history [n]` | View the last `n` executed trades (defaults to 10). |
| `/pause` | **Emergency Stop:** Halts all trading activity immediately. |
| `/resume` | Reactivates the trading loop. |
| `/mute` / `/unmute` | Toggle push notifications for trade alerts. |
| `/mode` | Swap between **Waterfall** and **Proportional** rebalancing math. |
| `/floor [-pct]` | Update the trailing stop-loss (e.g., `/floor -20`). |
| `/blacklist` | View all currently ignored coins. |
| `/ignore [COIN]` | Add a coin to the blacklist. |
| `/allow [COIN]` | Remove a coin from the blacklist. |
| `/panic` | **Nuclear Option:** Market-sells all non-blacklisted assets into fiat and halts the engine. Requires text confirmation. |

---

## 📦 Technology Stack
- **Language:** Python
- **Database:** SQLite3
- **Primary APIs:** Coinbase Advanced Trade, Telegram Bot API
- **Architecture:** Local state persistence with remote control interface