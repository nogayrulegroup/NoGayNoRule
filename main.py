# coding: utf-8

import os
import base64
import hashlib
import logging

import requests
import werkzeug
from flask import Flask, request, abort, jsonify, send_file, redirect
from peewee import (
    Model,
    MySQLDatabase,
    BigAutoField,
    IntegerField,
    CharField,
    SmallIntegerField,
    BooleanField,
    DateTimeField,
    DoesNotExist
)
from celery import Celery
from celery.schedules import crontab


PAGE_LIMIT = 500

STATIC_DIR = 'static'
SNAPSHOT_FILE = os.path.join(STATIC_DIR, 'snapshot/classification.csv')
SNAPSHOT_FILE_NEW = SNAPSHOT_FILE + '.1'
USER_UPLOAD_DIR = os.path.join(STATIC_DIR, 'user-upload')


CLASSIFICATION_TYPES = {
    0: 'unready',
    1: 'hazardous',
    2: 'recyclable',
    4: 'residual',
    8: 'wet',
    16: 'large',
    32: 'decoration',
}


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


@db.atomic()
def fetchone_item_by_name(name):
    try:
        return (ClassificationModel
                .select()
                .where((ClassificationModel.is_deleted == False)
                       & (ClassificationModel.item == name))
                .order_by(ClassificationModel.id.desc())
                .get())
    except DoesNotExist:
        return None


@db.atomic()
def fetchone_item(item_id):
    try:
        return (ClassificationModel
                .select()
                .where((ClassificationModel.id == item_id)
                       & (ClassificationModel.is_deleted == False))
                .get())
    except DoesNotExist:
        return None


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


@app.route('/classification/', methods=['POST'])
def define_classification():
    item = request.values.get('item', type=str)
    classification = request.values.get('classification', type=int)
    extra_detail = request.values.get('extra_detail', type=str, default='')
    image_hash = request.values.get('image_hash', type=str, default='')

    if not all([item, classification]):
        abort(400)
    if classification not in CLASSIFICATION_TYPES:
        return 'Uncategorized classification', 400

    exist = fetchone_item_by_name(item)
    if exist:
        return '{} already exists'.format(item), 400

    new_item = ClassificationModel(
        item=item,
        classification=classification,
        extra_detail=extra_detail,
        image_hash=image_hash)
    new_item.save()

    return 'OK'


@app.route('/classification/<int:item_id>', methods=['PUT'])
def update_item_info(item_id):
    classification = request.values.get('classification', type=int)
    extra_detail = request.values.get('extra_detail', type=str)

    if not any([classification, extra_detail]):
        abort(400)
    if classification not in CLASSIFICATION_TYPES:
        abort(400, 'Uncategorized classification')

    item = fetchone_item(item_id)
    if not item:
        abort(404, 'Item {} not found'.format(item_id))

    if classification:
        item.classification = classification
    if extra_detail:
        item.extra_detail = extra_detail
    item.save()

    return 'OK'


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


@app.route('/download/user-upload/<string:mdhash>')
def download_user_upload(mdhash):
    name = mdhash[2:] + '.' + mdhash[-3:].lower()
    return redirect('/'.join(['/user-upload', mdhash[0], mdhash[1], name]))


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
    with open(os.path.join(path, h[2:] + ext.upper()) + '.' + ext, 'wb') as fd:
        fd.write(content)
        fd.flush()
    return h, 200


# Celery
celerybeat = Celery()
celerybeat.conf.beat_schedule = {
    'snapshot': {
        'task': 'main.setup_periodic_tasks',
        'schedule': crontab(minute=0, hour='*'),
    },
}


@celerybeat.task
def snapshot_classification():

    def write_header(fd):
        fd.write('id,item,city,classification,extra_detail,image_hash')
        fd.write('\n')
        fd.flush

    with open(SNAPSHOT_FILE_NEW, 'wt') as fd:

        write_header(fd)
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
