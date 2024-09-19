# Telegram Schedule and Quote Bot

## Overview

This project is a Telegram bot that automatically sends schedules and quotes to users. It supports multiple languages (Russian and Ukrainian) and allows users to subscribe to daily schedule notifications, find stickers, change their group, and subscribe to thematic quotes. The bot also includes admin features for sending messages to all users and uses a simple SQLite database for storing user subscriptions and settings.

## Features

- **Daily Schedule Notifications:** Users receive daily schedule messages based on their group and chosen language.
- **Quote Subscription:** Users can subscribe to receive daily quotes based on their preferences.
- **Language Support:** The bot supports both Russian and Ukrainian languages, which can be selected by users.
- **Sticker Search:** Users can search for stickers based on keywords.
- **Admin Functionality:** Admins can send messages to all users and manage the bot's operation.
- **Group and Settings Management:** Users can change their group, language, and quote preferences via a simple menu.
- **Automatic Retry Logic:** The bot will automatically retry if there are connection issues.

## Requirements

- Python 3.x
- Required Python libraries:
  - `python-telegram-bot`
  - `loguru`
  - `schedule`
  - `requests`
  - `sqlite3`
  - `python-dotenv`

To install all required dependencies, run:

```bash
pip install -r requirements.txt
```

## Setup

1. Clone the repository to your local machine:

```bash
pip install -r requirements.txt
```

2. Set up the environment variables by creating a `.env` file in the root directory:

```bash
TOKEN=your_telegram_bot_token
ADMINS=comma_separated_list_of_admin_user_ids
```

3. Modify the schedule:

Open the `rus_schedule.json` or `ukr_schedule.json` file (depending on the language) and update the schedule entries as needed. The schedule is structured by days of the week, and each entry contains class time, class name, links (if applicable), and teacher information. Make sure to follow the existing format in the JSON file to avoid errors.

4. Start the bot by running the following command:

```bash
python main.py
```

## Usage

- **Schedule Notifications**:

  - Users can view today's schedule by selecting the "Schedule" button in the chat.
  - They can also view the schedule for tomorrow by selecting the "Schedule for Tomorrow" button.
  - The schedule is customized based on the user's selected group and language.

- **Quote Subscription**:

  - Users can subscribe or unsubscribe from receiving daily motivational quotes.
  - The bot allows users to change the theme of the quotes (e.g., success, life, motivation) via the settings menu.

- **Sticker Search**:

  - Users can enter keywords to search for specific stickers in the bot's database.
  - After entering a keyword, the bot will display matching stickers that users can select and send in their chats.

- **Settings**:

  - Users can access the settings menu to change their preferred language (Russian or Ukrainian).
  - They can switch between different groups to receive the appropriate schedule for their group.
  - Users can also configure quote themes by selecting different tags for the types of quotes they want to receive.

- **Admin Commands**:
  - Admins have access to additional functionality, such as sending broadcast messages to all subscribed users.
  - Admins can also manage user subscriptions and update settings for all users.

## Logs

The bot uses `loguru` for logging. Logs are saved to a file named `logging.log` in the root directory. The logging configuration ensures:

- Log files have a maximum size of 10 MB. Once this size is reached, the log file is compressed into a `.zip` archive.
- Logs contain timestamps, log levels, and detailed error messages.
- Important events, such as sending messages to users and error handling, are recorded to help with debugging and monitoring.

You can find the log files in the same directory where the bot is running. These logs are useful for tracking the bot's performance and diagnosing any issues that arise.
