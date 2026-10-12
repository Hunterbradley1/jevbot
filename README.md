# jevbot

A Discord bot that answers yes/no questions with a probability chart.

@mention the bot with a question and it replies with a poll-style chart showing how confident the model is in **yes** versus **no**, plus a one-line summary like `Yes 98% · No 2%`.

```
@jevbot Is the Earth round?
```

Answers come from the [TypeSafe](https://typesafe.ai) API. The question is sent as a choice between `yes` and `no`, and the API returns a probability for each.

## Requirements

- Python 3.10+
- A [TypeSafe](https://typesafe.ai) API key
- A Discord bot token

## Setup

### 1. Install dependencies

```
pip install discord.py python-dotenv pillow typesafe-sdk
```

### 2. Create the Discord bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and create an application.
2. On the **Bot** page:
   - Click **Reset Token** and copy the token. It's only shown once.
   - Turn on **Message Content Intent**.
   - Make sure **Requires OAuth2 Code Grant** is off.

> The bot token is not the **Public Key** on the General Information page.

### 3. Add your keys

Copy `.env.example` to `.env` and fill in both values:

```
TYPESAFE_API_KEY=your-typesafe-api-key
DISCORD_BOT_TOKEN=your-discord-bot-token
```

`.env` is in `.gitignore`. Never commit it.

### 4. Invite the bot to your server

In the Developer Portal, open **OAuth2 → URL Generator**:

- **Scopes:** `bot`
- **Bot Permissions:** View Channels, Send Messages, Send Messages in Threads, Attach Files, Read Message History

Open the generated URL and pick your server. Or use this link with your **Application ID** (from General Information):

```
https://discord.com/oauth2/authorize?client_id=YOUR_APP_ID&scope=bot&permissions=274878008320
```

If Discord says the application doesn't have a bot in the server, the link was missing the `bot` scope. Remove the app under Server Settings → Integrations and invite it again.

### 5. Run it

```
python jev_bot.py
```

The bot shows as online once it's running.

## Usage

- @mention the bot followed by a yes/no question.
- User, role and channel mentions inside the question are converted to names, so `Is @Sam online?` is asked as written rather than as a raw user ID.
- Each question is answered on its own. The bot doesn't remember earlier questions, so follow-ups like "what about @someone?" need to be asked in full.

## Testing without Discord

`jev_test.py` asks a single question from the command line and prints both probabilities:

```
python jev_test.py
```

```
Question: Is the Earth round?
Yes: 98.0%
No:  2.0%
```

Edit `QUESTION` at the top of the file to try other questions.

## Files

| File | Purpose |
|---|---|
| `jev_bot.py` | The Discord bot and chart rendering |
| `jev_test.py` | Command-line test of the TypeSafe yes/no call |
| `.env.example` | Template for your `.env` |

## Notes

The percentages are the model's confidence, not verified facts. Treat answers to opinion, prediction or personal questions as entertainment.
