import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ContentType, ParseMode
from aiogram.filters import CommandStart
from aiogram.filters import Filter
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery,
)
from app.db_async import DatabaseMiddleware, insert_payment, init_db_pool
from config.constants import PAYMENT_PROVIDER_TOKEN, TOKEN

dp = Dispatcher()

# Define courses with their prices
courses = {
    "Course 1": 200,
}


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with the `/start` command.
    """
    await message.answer(
        f"Вас вітає CultProject, {html.bold(message.from_user.full_name)}! Виберіть курс:"
    )
    await show_course_menu(message, message.chat.id)


async def show_course_menu(message: Message, user_id: int) -> None:
    """
    Show the course selection menu as an inline keyboard.
    """
    # Initialize an empty list for buttons
    buttons = [
        [
            InlineKeyboardButton(
                text="Безпечний салон", callback_data=f"course_{course_name}"
            )
        ]
        for course_name in courses.keys()
    ]

    # Create the InlineKeyboardMarkup with the buttons
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer("Доступні курси:", reply_markup=markup)


@dp.callback_query(lambda call: call.data.startswith("course_"))
async def handle_course_selection(call: CallbackQuery) -> None:
    """
    Handle the selection of a course from the inline keyboard.
    """
    course_name = call.data.split("_", 1)[1]
    price = courses[course_name]

    # Define the price for Telegram Payment (LabeledPrice)
    labeled_price = [LabeledPrice(label=course_name, amount=price)]
    title = f"{course_name} Course"
    description = f"Payment for {course_name} course."
    payload = f"course_{course_name}"  # You can encode additional data if needed
    provider_token = PAYMENT_PROVIDER_TOKEN
    currency = "PLN"
    prices = [
        LabeledPrice(label=course_name, amount=price * 100)
    ]  # amount in the smallest currency unit (cents)

    try:
        # Sending the invoice to the user
        await call.message.answer_invoice(
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=prices,
            start_parameter="course_purchase",
            is_flexible=False,
        )
    except Exception as e:
        print(f"Error sending invoice: {e}")
        await call.message.answer(
            "Sorry, there was an error while processing your payment."
        )

    await call.answer(f"You selected {course_name}!")


@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """
    Handle the pre-checkout process (Telegram automatically verifies the payment).
    """
    await pre_checkout_query.bot.answer_pre_checkout_query(
        pre_checkout_query.id, ok=True
    )


class SuccessfulPaymentFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        """
        Custom filter that checks if the message is of type 'successful_payment'.
        """
        return message.content_type == ContentType.SUCCESSFUL_PAYMENT


# Register handler for successful payment using the custom filter
@dp.message(SuccessfulPaymentFilter())
async def successful_payment_handler(message: Message):
    """
    Handle successful payments and send the course video.
    """
    print("successful_payment_handler")
    receipt = message.successful_payment
    print(receipt)

    pool = message.bot.pool  # Assuming pool is attached to the bot instance

    if not pool:
        print("No database pool available!")
        await message.answer(
            "There was an issue processing your payment. Please try again later."
        )
        return

    payload = message.successful_payment.invoice_payload  # e.g., "course_Course 1"
    course_name = payload.split("_", 1)[1]
    payment_data = {
        "telegram_id": message.from_user.id,
        "user_name": message.from_user.full_name,
        "course_name": course_name,
        "amount": message.successful_payment.total_amount,
        "status": "paid",
    }

    try:
        await insert_payment(pool, payment_data)
        video_url = "https://t.me/ssternenko/36997"  # Replace with your video URL
        await message.answer_video(
            video_url, caption=f"Here is your video for {course_name}!"
        )
    except Exception as e:
        print(f"Error inserting payment: {e}")
        await message.answer(
            "There was an issue processing your payment. Please try again later."
        )


# Handler for failed payment (if any)
@dp.message(SuccessfulPaymentFilter())
async def failed_payment_handler(message: Message):
    """
    Handle failed payments and prompt the user to try again.
    """
    if message.content_type == ContentType.SUCCESSFUL_PAYMENT:
        # If payment was not successful
        await message.answer(
            "Unfortunately, there was an issue with your payment. Please try again."
        )
        # Optionally, you could ask the user to re-initiate the payment process
        await message.answer("To retry, please select a course again.")


async def main() -> None:
    """
    Main entry point of the bot.
    """
    # Initialize the connection pool
    pool = await init_db_pool()

    # Initialize bot
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    bot.pool = pool

    # Add middleware to inject the pool
    dp.update.middleware(DatabaseMiddleware(pool))

    try:
        logging.info("Starting bot...")
        # Start polling
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        logging.info("Closing database pool...")
        await pool.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
