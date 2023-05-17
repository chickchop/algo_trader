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

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# State definitions for top level conversation
SELECTING_ACTION, ANALYSIS, ADDING_SELF, DESCRIBING_SELF = map(chr, range(4))
# State definitions for descriptions conversation
SELECTING_CORP, TYPING = map(chr, range(4, 6))
# State definitions for second level conversation
SELECTING_LEVEL, SELECTING_FEATURE = map(chr, range(6, 8))
# Meta states
STOPPING, SHOWING = map(chr, range(8, 10))
# Shortcut for ConversationHandler.END
END = ConversationHandler.END

# Different constants for this example
(
    SCENARIO_LEVEL,
    START_OVER,
    SELF,
    CORP_NAME,
    CORP_CODE,
    CORP,
    CURRENT_CORP,
    LEVEL,
    TREND,
    CHART,
    VALUATION,
    MOMENTUM,
    OLHC,
    BOLLINDER
) = map(chr, range(10, 24))
            
with open('config/configs.json') as f:
    json_object = json.load(f)
token = json_object["telegram_token"]


# Top level conversation callbacks
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Select an action: 분석 선택 or show data."""
    text = (
        "분석을 진행하거나 분석 결과를 볼 수 있습니다. 대화를 종료하려면"
        "/stop 을 쳐주세요."
    )
    context.user_data[SCENARIO_LEVEL] = 1
    buttons = [
        [
            InlineKeyboardButton(text="분석 수행", callback_data=str(ANALYSIS)),
            InlineKeyboardButton(text="Add yourself", callback_data=str(ADDING_SELF)),
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
            "Hi, I'm kochatbot and I'm here to help you gather information."
        )
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_ACTION


async def adding_self(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Add information about yourself."""
    context.user_data[SCENARIO_LEVEL] = SELF
    text = "Okay, please tell me about yourself."
    button = InlineKeyboardButton(text="Add info", callback_data=str(LEVEL))
    keyboard = InlineKeyboardMarkup.from_button(button)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return DESCRIBING_SELF


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Pretty print gathered data."""

    # def pretty_print(data: Dict[str, Any], level: str) -> str:
    #     people = data.get(level)
    #     if not people:
    #         return "\nNo information yet."

    #     return_str = ""
    #     if level == SELF:
    #         for person in data[level]:
    #             return_str += f"\nName: {person.get(NAME, '-')}, Age: {person.get(AGE, '-')}"
    #     else:
    #         male, female = _name_switcher(level)

    #         for person in data[level]:
    #             gender = female if person[GENDER] == FEMALE else male
    #             return_str += (
    #                 f"\n{gender}: Name: {person.get(NAME, '-')}, Age: {person.get(AGE, '-')}"
    #             )
    #     return return_str

    # user_data = context.user_data
    # text = f"Yourself:{pretty_print(user_data, SELF)}"
    # text += f"\n\nParents:{pretty_print(user_data, PARENTS)}"
    # text += f"\n\nChildren:{pretty_print(user_data, CHILDREN)}"

    # buttons = [[InlineKeyboardButton(text="Back", callback_data=str(END))]]
    # keyboard = InlineKeyboardMarkup(buttons)

    # await update.callback_query.answer()
    # await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    # user_data[START_OVER] = True

    return SHOWING


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    await update.message.reply_text("Okay, bye.")

    return END


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End conversation from InlineKeyboardButton."""
    await update.callback_query.answer()

    text = "See you around!"
    await update.callback_query.edit_message_text(text=text)

    return END


# Second level conversation callbacks
async def select_corp_input_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = "기업을 찾기 위한 방법으로 종목 명이나 종목 코드를 선택해주세요."
    context.user_data[SCENARIO_LEVEL] = 2
    buttons = [
        [
            InlineKeyboardButton(text="종목명", callback_data=str(CORP_NAME)),
            InlineKeyboardButton(text="종목코드", callback_data=str(CORP_CODE)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    
    return SELECTING_CORP


async def ask_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    context.user_data[CORP] = update.callback_query.data
    text = "Okay, tell me."
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text)

    return TYPING


async def save_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Save input for feature and return to feature selection."""
    user_data = context.user_data
    user_data[CURRENT_CORP] = update.message.text

    user_data[START_OVER] = True

    return await select_level(update, context)


async def end_describing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End gathering of features and return to parent conversation."""
    user_data = context.user_data
    level = user_data[SCENARIO_LEVEL]
    if not user_data.get(level):
        user_data[level] = []
    user_data[level].append(user_data[CURRENT_CORP])

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



async def end_second_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to top level conversation."""
    context.user_data[START_OVER] = True
    await start(update, context)

    return END


# Third level callbacks
async def select_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    context.user_data[SCENARIO_LEVEL] = 3
    buttons = [
        [
            InlineKeyboardButton(text="시황분석", callback_data=str(TREND)),
            InlineKeyboardButton(text="기술적분석(차트)", callback_data=str(CHART)),
            InlineKeyboardButton(text="기본분석(벨류에이션)", callback_data=str(VALUATION)),
            InlineKeyboardButton(text="모멘텀(호재, 악재)", callback_data=str(MOMENTUM)),
            InlineKeyboardButton(text="Done", callback_data=str(END)),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we collect level for analysis, clear the cache and save the level
    if not context.user_data.get(START_OVER):
        context.user_data[LEVEL] = {LEVEL: update.callback_query.data}
        text = "Please select a level to update."

        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    # But after we do that, we need to send a new message
    else:
        text = "Got it! Please select a level to update."
        await update.message.reply_text(text=text, reply_markup=keyboard)
    
    context.user_data[START_OVER] = False
    return SELECTING_FEATURE

async def select_feature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    level = update.callback_query.data

    text = "Please choose, whom to add."

    if level == TREND :
        buttons = [
        [
            InlineKeyboardButton(text="이평선 분석", callback_data=str(OLHC)),
            InlineKeyboardButton(text="볼린저밴드 분석", callback_data=str(BOLLINDER)),
        ],
        [
            InlineKeyboardButton(text="Show data", callback_data=str(SHOWING)),
            InlineKeyboardButton(text="Back", callback_data=str(END)),
        ],
    ]
        keyboard = InlineKeyboardMarkup(buttons)

    elif level == CHART :
        buttons = [
        [
            InlineKeyboardButton(text="이평선 분석", callback_data=str(OLHC)),
            InlineKeyboardButton(text="볼린저밴드 분석", callback_data=str(BOLLINDER)),
        ],
        ]
        keyboard = InlineKeyboardMarkup(buttons)
    elif level == VALUATION :
        buttons = [
        [
            InlineKeyboardButton(text="이평선 분석", callback_data=str(OLHC)),
            InlineKeyboardButton(text="볼린저밴드 분석", callback_data=str(BOLLINDER)),
        ],
        ]
        keyboard = InlineKeyboardMarkup(buttons)
    elif level == MOMENTUM :
        buttons = [
        [
            InlineKeyboardButton(text="이평선 분석", callback_data=str(OLHC)),
            InlineKeyboardButton(text="볼린저밴드 분석", callback_data=str(BOLLINDER)),
        ],
        ]
        keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return await show_data(update, context)



def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    # Set up third level ConversationHandler (collecting features)
    description_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                ask_for_input, pattern="^" + str(CORP_NAME) + "$|^" + str(CORP_CODE) + "$"
            )
        ],
        states={
            TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_input)],
        },
        fallbacks=[
            CallbackQueryHandler(end_describing, pattern="^" + str(END) + "$"),
            CommandHandler("stop", stop_nested),
        ],
        map_to_parent={
            # Return to second level menu
            END: ANALYSIS,
            # End conversation altogether
            STOPPING: STOPPING,
        },
    )

    # Set up second level ConversationHandler (분석 수행)
    analysis_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_corp_input_type, pattern="^" + str(ANALYSIS) + "$")],
        states={
            SELECTING_CORP: [description_conv],
            SELECTING_LEVEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND,select_level)
            ],
            SELECTING_FEATURE: [
                CallbackQueryHandler(select_feature, pattern=f"^{TREND}$|^{CHART}$|^{VALUATION}$|^{MOMENTUM}$")
            ],
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
        analysis_conv,
        CallbackQueryHandler(show_data, pattern="^" + str(SHOWING) + "$"),
        CallbackQueryHandler(adding_self, pattern="^" + str(ADDING_SELF) + "$"),
        CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
    ]
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SHOWING: [CallbackQueryHandler(start, pattern="^" + str(END) + "$")],
            SELECTING_ACTION: selection_handlers,
            ANALYSIS: selection_handlers,
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