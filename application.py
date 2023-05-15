import logging
from io import BytesIO
from typing import Dict
import os
import sys
from flask import Flask, request, jsonify, render_template, abort
from flask_restful import Api
from flask_cors import CORS
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from chatbot_template import KakaoTemplate
from algo.chart_analysis import get_chart_result

# from kochat.app import KochatApi
# from kochat.data import Dataset
# from kochat.loss import CRFLoss, CosFace, CenterLoss, COCOLoss, CrossEntropyLoss
# from kochat.model import intent, embed, entity
# from kochat.proc import DistanceClassifier, GensimEmbedder, EntityRecognizer, SoftmaxClassifier
# from scenario import dust, weather, travel, restaurant

basedir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(basedir)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

application = Flask(__name__)

CORS(application)
api = Api(application)

BOT_TYPE = "kakao"
BOT_TYPE = "telegram"


def prepare_data_for_answer(category, corp):
    # Write the plot Figure to a file-like bytes object:
    plot_file = BytesIO()
    fig, status_code, msg, comment = get_chart_result(category, corp, analysis_type=2)
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
        "comment" : comment
    }

    return prepared_data


@application.route("/", methods=['POST'])
def get_answer():
    payloads = request.get_json()

    try : 
        if BOT_TYPE == "kakao" :
            utterance = payloads['userRequest']['utterance']
            category = utterance[0]
            corp = utterance[0]
            ret = prepare_data_for_answer(category, corp)

            skillTemplate = KakaoTemplate()
            return skillTemplate.send_response(ret)
        else :
            abort(404)

    except Exception as e :
        abort(500)


def main() :
    if BOT_TYPE == "telegram" :
        token = "6077047821:AAGSOxUtmm5iemyfQHhB7kNmQRcXawGWT5s"
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
                    return_data["comment"] + "\n" +
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
    else :
        application.run(host='0.0.0.0', port=5000, threaded=True)


if __name__ == '__main__':
#     kochat.app.template_folder = kochat.root_dir + 'templates'
#     kochat.app.static_folder = kochat.root_dir + 'static'
#     kochat.app.run(port=8080, host='0.0.0.0')
    main()