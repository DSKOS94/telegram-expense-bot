
import asyncio
import os
import gspread
import nest_asyncio
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

nest_asyncio.apply()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS_FILE = "credentials.json"

def get_google_creds():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
    return creds

creds = get_google_creds()
client = gspread.authorize(creds)

SHEET_ID = "1xXkIZW3p_2ExARyR8KSkXvGCcZ73gEaXPBAMOtPccBk"
SHEET_NAME = "Внесениие"
REFERENCE_SHEET = "Справочник"

spreadsheet = client.open_by_key(SHEET_ID)
available_sheets = [sheet.title for sheet in spreadsheet.worksheets()]
print(f"✅ Доступные листы: {available_sheets}")
if SHEET_NAME not in available_sheets or REFERENCE_SHEET not in available_sheets:
    raise ValueError("❌ Ошибка: Не найдены нужные листы.")

sheet = spreadsheet.worksheet(SHEET_NAME)

async def add_expense(update: Update, context: CallbackContext):
    try:
        msg = update.message.text.split(maxsplit=8)
        if len(msg) < 8:
            await update.message.reply_text("❌ Формат: /add_expense месяц дата сумма объект контрагент назначение статья_ддс")
            return

        _, month, date, amount, *rest = msg
        object_ = "-"
        contractor = "-"
        purpose = "-"
        dds = "-"

        if len(rest) == 2:
            purpose, dds = rest
        elif len(rest) == 3:
            contractor, purpose, dds = rest
        elif len(rest) == 4:
            object_, contractor, purpose, dds = rest

        accrual_date = date
        wallet = "AJMAN BANK"

        row = [month, date, accrual_date, amount, wallet, object_, contractor, purpose, dds]
        sheet.append_row(row)
        print(f"✅ Добавлено: {row}")
        await update.message.reply_text(f"✅ Добавлено: {amount} AED, {purpose}.")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        await update.message.reply_text(f"❌ Ошибка при добавлении! {str(e)}")

async def start_bot():
    TOKEN = "7329695886:AAFXz9Q6jp4KfFDCvuBT_btKZk1zFO5k1LE"
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("add_expense", add_expense))

    print("⏳ Бот запускается...")
    await app.initialize()
    await app.start()
    print("✅ Бот запущен! Ожидаю команды...")
    await app.updater.start_polling()
    await asyncio.Event().wait()

# Гибкий запуск без ошибки закрытия event loop
def run():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен вручную")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")

if __name__ == "__main__":
    run()
