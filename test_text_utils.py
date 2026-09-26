import pytest
from aiogram.exceptions import TelegramBadRequest

from src.utils.text_utils import send_markdown_safe

pytestmark = pytest.mark.asyncio


class FakeMessage:
    pass


class FakeBot:
    def __init__(self, fail_with: TelegramBadRequest = None):
        self.calls = []
        self.fail_with = fail_with

    async def send_message(self, chat_id, text, **kwargs):
        self.calls.append((chat_id, text, kwargs))
        if self.fail_with and len(self.calls) == 1:
            raise self.fail_with
        return FakeMessage()


async def test_send_with_markdown():
    bot = FakeBot()
    await send_markdown_safe(bot, 123, 'text **bold**')
    assert len(bot.calls) == 1
    chat_id, text, kwargs = bot.calls[0]
    assert chat_id == 123
    assert text == 'text **bold**'
    assert kwargs['parse_mode'] == 'Markdown'


async def test_falls_back_to_plain_on_unparseable_entities():
    err = TelegramBadRequest(
        method='sendMessage',
        message="bad request: can't parse entities: can't find end of the entity"
    )
    bot = FakeBot(fail_with=err)
    await send_markdown_safe(bot, 1, 'угол менее 90* текст')
    assert len(bot.calls) == 2
    assert bot.calls[0][2]['parse_mode'] == 'Markdown'
    assert 'parse_mode' not in bot.calls[1][2]


async def test_reraises_other_telegram_errors():
    err = TelegramBadRequest(method='sendMessage', message='bad request: message text is empty')
    bot = FakeBot(fail_with=err)
    with pytest.raises(TelegramBadRequest):
        await send_markdown_safe(bot, 1, 'x')
    assert len(bot.calls) == 1