"""Allows lichess-bot to send messages to the chat."""
from __future__ import annotations
import logging
import test_bot.lichess
from lib import model
from lib import lichess
from collections.abc import Sequence
from typing import Union
MULTIPROCESSING_LIST_TYPE = Sequence[model.Challenge]
LICHESS_TYPE = Union[lichess.Lichess, test_bot.lichess.Lichess]

logger = logging.getLogger(__name__)


class Conversation:
    """Enables the bot to communicate with its opponent and the spectators."""

    def __init__(self, game: model.Game, li: LICHESS_TYPE, version: str,
                 challenge_queue: MULTIPROCESSING_LIST_TYPE) -> None:
        """
        Communication between lichess-bot and the game chats.

        :param game: The game that the bot will send messages to.
        :param li: A class that is used for communication with lichess.
        :param version: The lichess-bot version.
        :param challenge_queue: The active challenges the bot has.
        """
        self.game = game
        self.li = li
        self.version = version
        self.challengers = challenge_queue

    def react(self, line: ChatLine) -> None:
        """
        React to a received message.

        :param line: Information about the message.
        """
        logger.info(f'*** {self.game.url()} [{line.room}] {line.username}: {line.text}')
        self.send_reply(line, "Focus on the game buddy, I'm not here to chat.")

    def send_reply(self, line: ChatLine, reply: str) -> None:
        """
        Send the reply to the chat.

        :param line: Information about the original message that we reply to.
        :param reply: The reply to send.
        """
        logger.info(f'*** {self.game.url()} [{line.room}] {self.game.username}: {reply}')
        self.li.chat(self.game.id, line.room, reply)

    def send_message(self, room: str, message: str) -> None:
        """Send the message to the chat."""
        if message:
            self.send_reply(ChatLine({"room": room, "username": "", "text": ""}), message)


class ChatLine:
    """Information about the message."""

    def __init__(self, message_info: dict[str, str]) -> None:
        """Information about the message."""
        self.room = message_info["room"]
        """Whether the message was sent in the chat room or in the spectator room."""
        self.username = message_info["username"]
        """The username of the account that sent the message."""
        self.text = message_info["text"]
        """The message sent."""
