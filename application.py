"""
@auther Hyunwoong
@since 7/1/2020
@see https://github.com/gusdnd852
"""
import logging
import os
import sys
from typing import Dict
from io import BytesIO
from flask import render_template
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from algo.chart_analysis import analysis_bollinger_bands
# from kochat.app import KochatApi
# from kochat.data import Dataset
# from kochat.loss import CRFLoss, CosFace, CenterLoss, COCOLoss, CrossEntropyLoss
# from kochat.model import intent, embed, entity
# from kochat.proc import DistanceClassifier, GensimEmbedder, EntityRecognizer, SoftmaxClassifier
# from scenario import dust, weather, travel, restaurant

token = "6077047821:AAGSOxUtmm5iemyfQHhB7kNmQRcXawGWT5s"
basedir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(basedir)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [
    ["종목명","종목코드", "Something else..."],
    ["Done"],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])

def prepare_data_for_answer(category, text):
    # Write the plot Figure to a file-like bytes object:
    plot_file = BytesIO()
    fig, status_code, msg = analysis_bollinger_bands(category, text)
    if status_code == 200 :
        fig.savefig(plot_file, format='png')
        plot_file.seek(0)
        error_msg = ""
    else :
        error_msg = category + "입력 오류 입니다."
        plot_file = None

    prepared_data = {
        "status" : status_code,
        "msg" : msg ,
        "error_msg" : error_msg,
        "plot_file": plot_file,
    }

    return prepared_data

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""
    await update.message.reply_text(
        "Hi! My name is Ko chat. 몇 가지 물어볼게요",
        reply_markup=markup,
    )

    return CHOOSING


async def regular_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for info about the selected predefined choice."""
    text = update.message.text
    context.user_data["choice"] = text
    await update.message.reply_text(f"{text.lower()}을 선택하셨군요!")

    return TYPING_REPLY


async def custom_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for a description of a custom category."""
    await update.message.reply_text(
        'Alright, please send me the category first, for example "Most impressive skill"'
    )

    return TYPING_CHOICE


async def received_information(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store info provided by user and ask for the next category."""
    user_data = context.user_data
    text = update.message.text
    category = user_data["choice"]
    user_data[category] = text
    del user_data["choice"]
    return_data = prepare_data_for_answer(category, text)

    if return_data["status"] == 200 :
        await update.message.reply_photo(
            photo=return_data["plot_file"]
        )

        await update.message.reply_text(
            f"{facts_to_str(user_data)}에 관련된 분석 내용입니다. 추가로 궁금하시게 있으면 선택해 주세요.",
            reply_markup=markup,
        )
    else :
        await update.message.reply_text(
            return_data["error_msg"],
            reply_markup=markup,
        )

    return CHOOSING


async def bad_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Raise an error to trigger the error handler."""
    await context.bot.wrong_method_name()  # type: ignore[attr-defined]


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the gathered info and end the conversation."""
    user_data = context.user_data
    if "choice" in user_data:
        del user_data["choice"]

    await update.message.reply_text(
        f"I learned these facts about you: {facts_to_str(user_data)}Until next time!",
        reply_markup=ReplyKeyboardRemove(),
    )

    user_data.clear()
    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(
                    filters.Regex("^(종목명|종목코드)$"), regular_choice
                ),
                MessageHandler(filters.Regex("^Something else...$"), custom_choice),
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^Done$")), regular_choice
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^Done$")),
                    received_information,
                )
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("bad_command", bad_command))
    application.run_polling()


# dataset = Dataset(ood=True)
# emb = GensimEmbedder(model=embed.FastText())

# clf = DistanceClassifier(
#     model=intent.CNN(dataset.intent_dict),
#     loss=CenterLoss(dataset.intent_dict),
# )

# rcn = EntityRecognizer(
#     model=entity.LSTM(dataset.entity_dict),
#     loss=CRFLoss(dataset.entity_dict)
# )

# kochat = KochatApi(
#     dataset=dataset,
#     embed_processor=(emb, True),
#     intent_classifier=(clf, True),
#     entity_recognizer=(rcn, True),
#     scenarios=[
#         weather, dust, travel, restaurant
#     ]
# )


# @kochat.app.route('/')
# def index():
#     return render_template("index.html")


if __name__ == '__main__':
#     kochat.app.template_folder = kochat.root_dir + 'templates'
#     kochat.app.static_folder = kochat.root_dir + 'static'
#     kochat.app.run(port=8080, host='0.0.0.0')
    main()