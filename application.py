"""
@auther Hyunwoong
@since 7/1/2020
@see https://github.com/gusdnd852
"""
import logging
from flask import render_template
import telegram
import telegram.ext as telext
from kochat.app import KochatApi
from kochat.data import Dataset
from kochat.loss import CRFLoss, CosFace, CenterLoss, COCOLoss, CrossEntropyLoss
from kochat.model import intent, embed, entity
from kochat.proc import DistanceClassifier, GensimEmbedder, EntityRecognizer, SoftmaxClassifier
from scenario import dust, weather, travel, restaurant

token = "6077047821:AAGSOxUtmm5iemyfQHhB7kNmQRcXawGWT5s"
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def start(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

application = telext.ApplicationBuilder().token(token).build()
    
start_handler = telext.CommandHandler('start', start)
application.add_handler(start_handler)

application.run_polling()

# id_list = []


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


# if __name__ == '__main__':
#     kochat.app.template_folder = kochat.root_dir + 'templates'
#     kochat.app.static_folder = kochat.root_dir + 'static'
#     kochat.app.run(port=8080, host='0.0.0.0')
