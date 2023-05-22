import logging
from io import BytesIO
from typing import Dict
import os
import sys
import json
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


if __name__ == '__main__':
#     kochat.app.template_folder = kochat.root_dir + 'templates'
#     kochat.app.static_folder = kochat.root_dir + 'static'
#     kochat.app.run(port=8080, host='0.0.0.0')
    application.run(host='0.0.0.0', port=5000, threaded=True)