# coding: utf-8

import os
import base64

import requests
import werkzeug
from flask import Flask, request, abort, jsonify


KEY_BASE_URL = (
    'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials'
    '&client_id={}&client_secret={}'
)
BAIDU = (
    'https://aip.baidubce.com/rest/2.0/image-classify/v2/'
    'advanced_general?access_token={}'
)

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']


app = Flask('NoWasted')
app.config['MAX_CONTENT_LENGTH'] = 128 * 1024  # 128KB


@app.errorhandler(werkzeug.exceptions.BadRequest)
def handle_bad_request(e):
    return 'bad request!', 400


app.register_error_handler(400, handle_bad_request)


def get_access_token():
    result = requests.post(KEY_BASE_URL.format(CLIENT_ID, CLIENT_SECRET))
    return result.json()['access_token']


def encode_image(image):
    return base64.b64encode(image)


def load_image(path):
    with open(path, 'rb') as fd:
        image = fd.read()
    return encode_image(image)


def recognize(image):
    result = requests.post(
        BAIDU.format(get_access_token()),
        data={'image': image})
    return result.json()


def load_and_recognize(path):
    return recognize(load_image(path))


@app.route('/garbage')
def index():
    return 'Not wasted!'


@app.route('/recognize/text')
def recoginze_text():
    text = request.values.get('text')
    if not text:
        abort(400)
    return text


@app.route('/recognize/image/base64', methods=['POST'])
def recognize_image_base64():
    image = request.values.get('image_base64')
    if not image:
        abort(400)
    resp = recognize(image)
    if resp.get('error_msg'):
        return resp.get('error_msg')
    return jsonify({
        'result': resp['result'],
        'total': resp['result_num'],
    })


@app.route('/recognize/image', methods=['POST'])
def recognize_image():
    image = request.files.get('image')
    if not image:
        abort(400)
    resp = recognize(encode_image(image.read()))
    if resp.get('error_msg'):
        return resp.get('error_msg')
    return jsonify({
        'result': resp['result'],
        'total': resp['result_num'],
    })


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('image')

    args = parser.parse_args()
    if not args.image:
        print('Unexcept image path: {}', args.image)
    print(load_and_recognize(args.image))


if __name__ == '__main__':
    main()
