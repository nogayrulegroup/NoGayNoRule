# coding: utf-8

import os
import base64
import hashlib
import logging

import requests
import werkzeug
from flask import Flask, request, abort, jsonify, send_file
from peewee import (
    Model,
    MySQLDatabase,
    BigAutoField,
    IntegerField,
    CharField,
    SmallIntegerField,
    BooleanField,
    DateTimeField
)
from celery import Celery
from celery.schedules import crontab


PAGE_LIMIT = 500

STATIC_DIR = 'static'
SNAPSHOT_FILE = os.path.join(STATIC_DIR, 'snapshot/classification.csv')
SNAPSHOT_FILE_NEW = SNAPSHOT_FILE + '.1'
USER_UPLOAD_DIR = os.path.join(STATIC_DIR, 'user-upload')


logger = logging.getLogger()


db = MySQLDatabase(
    'wasted',
    host=os.environ['DB_HOST'],
    port=int(os.environ['DB_PORT']),
    user=os.environ['DB_USER'],
    passwd=os.environ['DB_PASSWD'],
    autoconnect=False,
    charset='utf8mb4')


class ClassificationModel(Model):
    id = BigAutoField()
    item = CharField()
    city = CharField()
    classification = IntegerField()
    frequency = SmallIntegerField()
    extra_detail = CharField()
    image_hash = CharField()
    is_deleted = BooleanField()
    created_at = DateTimeField()
    updated_at = DateTimeField()

    class Meta:
        database = db
        table_name = 'tb_classification'


@db.atomic()
def query_with_last_id(last_id, limit=PAGE_LIMIT):
    return (ClassificationModel
            .select()
            .where((ClassificationModel.id > last_id)
                   & (ClassificationModel.is_deleted == False))
            .limit(limit))


@db.atomic()
def dump_classification():
    return (ClassificationModel
            .select(ClassificationModel.id,
                    ClassificationModel.item,
                    ClassificationModel.city,
                    ClassificationModel.classification,
                    ClassificationModel.extra_detail,
                    ClassificationModel.image_hash)
            .where(ClassificationModel.is_deleted == False)
            .tuples()
            .iterator())


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


@app.route('/recognize/image/base64', methods=['POST'])
def recognize_image_base64():
    image = request.values.get('image_base64')
    if not image:
        abort(400)
    resp = recognize(image)
    if resp.get('error_msg'):
        return jsonify({
            'error': resp.get('error_msg'),
        }), 400
    return jsonify({
        'result': resp['result'],
        'total': resp['result_num'],
    })


@app.route('/classification/', methods=['PUT'])
def define_classification():
    pass


@app.route('/recognize/image', methods=['POST'])
def recognize_image():
    image = request.files.get('image')
    if not image:
        abort(400)
    resp = recognize(encode_image(image.read()))
    if resp.get('error_msg'):
        return jsonify({
            'error': resp.get('error_msg'),
        }), 400
    return jsonify({
        'result': resp['result'],
        'total': resp['result_num'],
    })


@app.route('/download/cursor')
def download_cursor():
    last_id = request.values.get('last_id', type=int, default=0)
    return jsonify({
        'data': [{
            'id': rd.id,
            'item': rd.item,
            'classification': rd.classification,
            'extra_detail': rd.extra_detail,
        } for rd in query_with_last_id(last_id)]
    })


@app.route('/download/classification')
def download_classification():
    return send_file(SNAPSHOT_FILE)


@app.route('/file-upload', methods=['POST'])
def upload_file():
    fp = request.files.get('file')
    ext = request.values.get('extension')
    content = fp.read()

    m = hashlib.md5()
    m.update(content)
    h = m.hexdigest()

    path = os.path.join(USER_UPLOAD_DIR, h[0], h[1])
    if not os.path.isdir(path):
        os.makedirs(path, 0o755)
    with open(os.path.join(path, h[2:]) + '.' + ext, 'wb') as fd:
        fd.write(content)
        fd.flush()
    return h, 200


# Celery
celerybeat = Celery()
celerybeat.conf.beat_schedule = {
    'snapshot': {
        'task': 'main.setup_periodic_tasks',
        'schedule': crontab(hour=1),
    },
}


@celerybeat.task
def snapshot_classification():
    with open(SNAPSHOT_FILE_NEW, 'wt') as fd:
        for r in dump_classification():
            fd.write(','.join(map(str, r)))
            fd.write('\n')
        fd.flush()

    os.rename(SNAPSHOT_FILE_NEW, SNAPSHOT_FILE)


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
