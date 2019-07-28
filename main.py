# coding: utf-8

import os
import base64

import requests


BAIDU = (
    'https://aip.baidubce.com/rest/2.0/image-classify/v2/'
    'advanced_general?access_token='
)
ACCESS_KEY = os.environ['ACCESS_KEY']


def encode_image(image):
    return base64.b64encode(image)


def load_image(path):
    with open(path, 'rb') as fd:
        image = fd.read()
    return encode_image(image)


def recognize(image_path):
    result = requests.post(
        BAIDU + ACCESS_KEY,
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
