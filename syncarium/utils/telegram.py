#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# telegram.py

**Project**: Syncarium - Intelligent Timing Platform Toolkit  
**Description**: Telegram Bot utilities.  
**Author**: PhD Student Alberto Ortega Ruiz, University of Granada  
**Created**: 2025-10-08  
**Version**: 1.1.0  
**License**: GPLv3
"""

# ─────────────────────────────────────────────────────────────────────────────
# Standard Library Imports
# (None used directly in this file)


# ─────────────────────────────────────────────────────────────────────────────
# Third-Party Imports
import requests

# ─────────────────────────────────────────────────────────────────────────────
# Local Application Imports
import syncarium.options.telegram_vars as telegram_vars


# ─────────────────────────────────────────────────────────────
# 📱 TelegramBot Class
# ─────────────────────────────────────────────────────────────
class TelegramBot:
    """
    Utility class for sending, receiveing or managing program messages to a Telegram Bot.

    ### Attributes
    - **telegram_bot_token** (`str`): Telegram bot token used for sending notifications.
    - **telegram_chat_id** (`str`): Telegram chat ID used for sending notifications.
    """

# ─────────────────────────────────────────────────────────────────────────────
# 🚧 Function: constructor
# ─────────────────────────────────────────────────────────────────────────────
    def __init__(self) -> None:
        
        self.telegram_bot_token: str = telegram_vars.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id: str = telegram_vars.TELEGRAM_CHAT_ID

# ─────────────────────────────────────────────────────────────────────────────
# 📌 Function: send_message
# ─────────────────────────────────────────────────────────────────────────────
    def send_message(self, message: str) -> None:
        """
        Sends a message to the configured Telegram bot.

        Constructs and sends a POST request to the Telegram Bot API using the stored
        bot token and chat ID. If the request fails, an error message is shown in the console.

        ### Args:
        - **message** (`str`): Text message to send via Telegram.
        """

        if self.telegram_bot_token:
            url: str = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data: dict[str, str] = {
                "chat_id": self.telegram_chat_id,
                "text": message
            }

            requests.post(url, data=data)