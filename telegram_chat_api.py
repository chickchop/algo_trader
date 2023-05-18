from io import BytesIO
import logging
import json
from typing import Any, Dict, Tuple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from algo.chart_analysis import get_chart_result
from algo.fundamental_analysis import get_analysis_result

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# State definitions for top level conversation
SELECTING_ACTION, INFORMATION, DO_ANALYSIS, DESCRIBING_SELF = map(chr, range(4))
# State definitions for second level conversation
SELECTING_LEVEL, SELECTING_TYPE = map(chr, range(4, 6))
# State definitions for descriptions conversation
SELECTING_FEATURE, TYPING = map(chr, range(6, 8))
# Meta states
STOPPING, SHOWING = map(chr, range(8, 10))
# Shortcut for ConversationHandler.END
END = ConversationHandler.END

# Different constants for this example
(
    CHART,#\x0f
    VALUATION,#\x0c
    SELF,
    ANALYSIS_TYPE, #\r
    OHLC,
    BOLLINDGER, 
    KPI,
    MODEL,
    CODE, #\x12
    NAME, #\x13
    START_OVER, #\x14
    FEATURES, #\x15
    CURRENT_FEATURE, #\x16
    CURRENT_LEVEL, #\x17
) = map(chr, range(10, 24))


# Top level conversation callbacks
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Select an action: Adding parent/child or show data."""
    text = (
        "분석을 수행하기 위해서 분석을 수행하세요. 입력한 정보를 확인하려면 show data 로 확인하세요. Done 을 누르시면 종료입니다."
        "간단하게 대화를 종료하려면 /stop."
    )

    buttons = [
        [
            InlineKeyboardButton(text="정보 입력", callback_data=str(INFORMATION)),
            InlineKeyboardButton(text="분석 실행", callback_data=str(DO_ANALYSIS)),
        ],
        [
            InlineKeyboardButton(text="Show data", callback_data=str(SHOWING)),
            InlineKeyboardButton(text="Done", callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we're starting over we don't need to send a new message
    if context.user_data.get(START_OVER):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        await update.message.reply_text(
            "Hi, Kochat 입니다. 기업 분석을 원하시는 내용을 선택해주셔야 합니다."
        )
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_ACTION


async def do_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Add information about yourself."""
    
    text = "분석을 수행중입니다."

    user_data = context.user_data
    def prepare_data_for_answer(user_data):
        print(user_data)
        if user_data[CURRENT_FEATURE] == NAME :
            category = "종목명"
            corp = user_data[FEATURES][NAME]
        else :
            category = "종목코드"
            corp = user_data[FEATURES][CODE]
        level = user_data[CURRENT_LEVEL]
        
        if level == CHART :
            # Write the plot Figure to a file-like bytes object:
            if user_data[FEATURES][ANALYSIS_TYPE] == OHLC :
                analysis_type = 1
            else :
                analysis_type = 2
            plot_file = BytesIO()
            fig, status_code, msg, comment = get_chart_result(category, corp, analysis_type=analysis_type)
        elif level == VALUATION :
            if user_data[FEATURES][ANALYSIS_TYPE] == KPI :
                analysis_type = 1
            else :
                analysis_type = 2
            plot_file = BytesIO()
            fig, status_code, msg, comment = get_analysis_result(category, corp, analysis_type=analysis_type)
            
        if status_code == 200 :
            if fig is None :
                plot_file = None
            else :
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

    return_data = prepare_data_for_answer(user_data)

    if return_data["status"] == 200 :
        if return_data["plot_file"] is None :
            pass
        else :
            await update.callback_query.message.reply_photo(
                photo=return_data["plot_file"]
            )

        await update.callback_query.message.reply_text(
            return_data["comment"],
        )
    else :
        await update.message.reply_text(
            return_data["error_msg"],
        )
    # await update.callback_query.answer()
    # await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return END


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    def pretty_print(data: Dict[str, Any], level: str) -> str:
        corp = data.get(level)
        if not corp:
            return "\nNo information yet."

        return_str = ""
        if level == SELF:
            for corp in data[level]:
                return_str += f"\nName: {corp.get(NAME, '-')}, Code: {corp.get(CODE, '-')}"
        else:
            for corp in data[level]:
                if corp[ANALYSIS_TYPE] == CHART :
                    analysis_type_nm = "기술적 분석"
                elif corp[ANALYSIS_TYPE] == VALUATION :
                    analysis_type_nm = "기본적 분석"
                else :
                    analysis_type_nm = ""
                return_str += (
                    f"\n{analysis_type_nm}: Name: {corp.get(NAME, '-')}, Code: {corp.get(CODE, '-')}"
                )
        return return_str

    user_data = context.user_data
    text = f"Yourself:{pretty_print(user_data, SELF)}"
    text += f"\n\n기술적 분석 선택:{pretty_print(user_data, CHART)}"
    text += f"\n\n기본적 분석 선택:{pretty_print(user_data, VALUATION)}"

    buttons = [[InlineKeyboardButton(text="Back", callback_data=str(END))]]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    user_data[START_OVER] = True

    return SHOWING


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    for i in context.user_data.keys() :
        del context.user_data[i]
    await update.message.reply_text("Okay, bye.")

    return END


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End conversation from InlineKeyboardButton."""
    await update.callback_query.answer()

    text = "See you around!"
    await update.callback_query.edit_message_text(text=text)

    return END


# Second level conversation callbacks
async def select_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Choose to add a parent or a child."""
    text = "기업 분석 방법을 선택해주세요. 마찬가지로 show data 로 입력을 확인하거나 뒤로 돌아갈 수 있습니다."
    buttons = [
        [
            InlineKeyboardButton(text="기술적 분석(차트 분석)", callback_data=str(CHART)),
            InlineKeyboardButton(text="기본적 분석(벨류에이션)", callback_data=str(VALUATION)),
        ],
        [
            InlineKeyboardButton(text="Show data", callback_data=str(SHOWING)),
            InlineKeyboardButton(text="Back", callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SELECTING_LEVEL


async def select_analysis_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Choose to add mother or father."""
    level = update.callback_query.data
    context.user_data[CURRENT_LEVEL] = level

    text = " 구체적으로 어떤 분석 방법을 하실건가요?"

    if level == CHART :
        buttons = [
            [
                InlineKeyboardButton(text="캔들차트, 이평선", callback_data=str(OHLC)),
                InlineKeyboardButton(text="볼린저밴드", callback_data=str(BOLLINDGER)),
            ],
            [
                InlineKeyboardButton(text="Show data", callback_data=str(SHOWING)),
                InlineKeyboardButton(text="Back", callback_data=str(END)),
            ],
        ]
    elif level == VALUATION :
        buttons = [
            [
                InlineKeyboardButton(text="지표", callback_data=str(KPI)),
                InlineKeyboardButton(text="파마프렌치 기반 평가", callback_data=str(MODEL)),
            ],
            [
                InlineKeyboardButton(text="Show data", callback_data=str(SHOWING)),
                InlineKeyboardButton(text="Back", callback_data=str(END)),
            ],
        ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SELECTING_TYPE


async def end_second_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to top level conversation."""
    context.user_data[START_OVER] = True
    await start(update, context)

    return END


# Third level callbacks
async def select_feature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Select a feature to update for the person."""
    print(context.user_data)
    buttons = [
        [
            InlineKeyboardButton(text="종목명", callback_data=str(NAME)),
            InlineKeyboardButton(text="종목코드", callback_data=str(CODE)),
            InlineKeyboardButton(text="Done", callback_data=str(END)),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we collect features for a new person, clear the cache and save the gender
    if not context.user_data.get(START_OVER):
        context.user_data[FEATURES] = {ANALYSIS_TYPE: update.callback_query.data}
        text = "Please select a feature to update."

        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    # But after we do that, we need to send a new message
    else:
        text = "Got it! 이제 Done 을 누르세요."
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_FEATURE


async def ask_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for selected feature."""
    context.user_data[CURRENT_FEATURE] = update.callback_query.data
    text = "Okay, tell me."

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text)

    return TYPING


async def save_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Save input for feature and return to feature selection."""
    user_data = context.user_data
    user_data[FEATURES][user_data[CURRENT_FEATURE]] = update.message.text

    user_data[START_OVER] = True

    return await select_feature(update, context)


async def end_describing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End gathering of features and return to parent conversation."""
    user_data = context.user_data
    level = user_data[CURRENT_LEVEL]
    if not user_data.get(level):
        user_data[level] = []
    user_data[level].append(user_data[FEATURES])

    # Print upper level menu
    if level == SELF:
        user_data[START_OVER] = True
        await start(update, context)
    else:
        await select_level(update, context)

    return END


async def stop_nested(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Completely end conversation from within nested conversation."""
    await update.message.reply_text("Okay, bye.")

    return STOPPING


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    with open('config/configs.json') as f:
        json_object = json.load(f)
    token = json_object["telegram_token"]
    application = Application.builder().token(token).build()

    # Set up third level ConversationHandler (collecting features)
    description_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                select_feature, pattern="^" + str(OHLC) + "$|^" + str(BOLLINDGER) + "$|^" + str(KPI) + "$|^" + str(MODEL)
            )
        ],
        states={
            SELECTING_FEATURE: [
                CallbackQueryHandler(ask_for_input, pattern="^(?!" + str(END) + ").*$")
            ],
            TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_input)],
        },
        fallbacks=[
            CallbackQueryHandler(end_describing, pattern="^" + str(END) + "$"),
            CommandHandler("stop", stop_nested),
        ],
        map_to_parent={
            # Return to second level menu
            END: SELECTING_LEVEL,
            # End conversation altogether
            STOPPING: STOPPING,
        },
    )

    # Set up second level ConversationHandler (adding a person)
    analysis_cov = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_level, pattern="^" + str(INFORMATION) + "$")],
        states={
            SELECTING_LEVEL: [
                CallbackQueryHandler(select_analysis_type, pattern=f"^{CHART}$|^{VALUATION}$")
            ],
            SELECTING_TYPE: [description_conv],
        },
        fallbacks=[
            CallbackQueryHandler(show_data, pattern="^" + str(SHOWING) + "$"),
            CallbackQueryHandler(end_second_level, pattern="^" + str(END) + "$"),
            CommandHandler("stop", stop_nested),
        ],
        map_to_parent={
            # After showing data return to top level menu
            SHOWING: SHOWING,
            # Return to top level menu
            END: SELECTING_ACTION,
            # End conversation altogether
            STOPPING: END,
        },
    )

    # Set up top level ConversationHandler (selecting action)
    # Because the states of the third level conversation map to the ones of the second level
    # conversation, we need to make sure the top level conversation can also handle them
    selection_handlers = [
        analysis_cov,
        CallbackQueryHandler(show_data, pattern="^" + str(SHOWING) + "$"),
        CallbackQueryHandler(do_analysis, pattern="^" + str(DO_ANALYSIS) + "$"),
        CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
    ]
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SHOWING: [CallbackQueryHandler(start, pattern="^" + str(END) + "$")],
            SELECTING_ACTION: selection_handlers,
            SELECTING_LEVEL: selection_handlers,
            DESCRIBING_SELF: [description_conv],
            STOPPING: [CommandHandler("start", start)],
        },
        fallbacks=[CommandHandler("stop", stop)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()