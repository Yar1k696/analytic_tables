from aiogram import Bot, Dispatcher
from handlers.start import router as start_router
from config import BOT_TOKEN
import logging
import asyncio


bot = Bot(token=BOT_TOKEN)

dp = Dispatcher()

dp.include_router(start_router)

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
