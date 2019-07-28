# coding: utf-8

import os
import base64

import requests

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


def get_access_token():
    result = requests.post(KEY_BASE_URL.format(CLIENT_ID, CLIENT_SECRET))
    return result.json()['access_token']


def encode_image(image):
    return base64.b64encode(image)


def load_image(path):
    with open(path, 'rb') as fd:
        image = fd.read()
    return encode_image(image)


def recognize(image_path):
    result = requests.post(
        BAIDU.format(get_access_token()),
        data={'image': load_image(image_path)})
    print(result.text)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('image')

    args = parser.parse_args()
    if not args.image:
        print('Unexcept image path: {}', args.image)
    recognize(args.image)


if __name__ == '__main__':
    main()
