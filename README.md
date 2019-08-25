# NoGayNoRule

## TL;DR

```bash
CLENT_ID={API KEY} CLENT_SECRET={SECRET KEY} python main.py {IMAGE PATH}
```

## HTTP API

### Heath API

----
  探活接口

* **URL**

  /garbage

* **Method:**

  `GET`

* **URL Params**

  None

* **Data Params**

  None

* **Success Response:**

  * **Code:** 200 <br />
    **Content:** `Not wasted!`

* **Sample Call:**

  ```sh
    curl -X GET http://127.0.0.1:8010/garbage
  ```

### Image Recognization

----
  返回图片识别的结果(base64)

* **URL**

  /recognize/image/base64

* **Method:**

  `POST`

* **URL Params**

  None

* **Data Params**

   **Required:**

   `image_base64=[string]`

* **Success Response:**

  * **Code:** 200 <br />
    **Content:**

    ```json
    {
        "result": [
            {
                "keyword": "瓶子",
                "root": "商品-容器",
                "score": 0.562192
            },
            {
                "keyword": "电池",
                "root": "商品-电子原器件",
                "score": 0.429014
            },
            {
                "keyword": "化妆品",
                "root": "美妆-香水彩妆",
                "score": 0.250203
            },
            {
                "keyword": "药品",
                "root": "商品-药品",
                "score": 0.127708
            },
            {
                "keyword": "瓶装饮料",
                "root": "商品-瓶饮",
                "score": 0.004085
            }
        ],
        "total": 5
    }
    ```

* **Error Response:**

  * **Code:** 400 Bad Request <br />
    **Content:**

    ```json
    {
        "error": "image format error"
    }
    ```

* **Sample Call:**

  ```bash
    curl -X POST \
    http://0.0.0.0:8010/recognize/image/base64 \
    -F 'image_base64=[base64 string]'
  ```

----
  返回图片识别的结果
  
* **URL**

  /recognize/image

* **Method:**

  `POST`

* **URL Params**

  None

* **Data Params**

   **Required:**

   `image=[file]`

* **Success Response:**

  * **Code:** 200 <br />
    **Content:**

    ```json
    {
        "result": [
            {
                "keyword": "瓶子",
                "root": "商品-容器",
                "score": 0.562192
            },
            {
                "keyword": "电池",
                "root": "商品-电子原器件",
                "score": 0.429014
            },
            {
                "keyword": "化妆品",
                "root": "美妆-香水彩妆",
                "score": 0.250203
            },
            {
                "keyword": "药品",
                "root": "商品-药品",
                "score": 0.127708
            },
            {
                "keyword": "瓶装饮料",
                "root": "商品-瓶饮",
                "score": 0.004085
            }
        ],
        "total": 5
    }
    ```

* **Error Response:**

  * **Code:** 400 Bad Request <br />
    **Content:**

    ```json
    {
        "error": "image format error"
    }
    ```

* **Sample Call:**

  ```bash
    curl -X POST \
    http://0.0.0.0:8010/recognize/image \
    -F image=@/Path/To/Image.jpeg
  ```

### Download Cursor

----
  下载分类数据，一次最多返回 500 条数据

* **URL**

  /download/cursor

* **Method:**

  `GET`

* **URL Params**

  **Optional**

  `last_id=[int:0]`

* **Data Params**

  None

* **Success Response:**

  * **Code:** 200 <br />
    **Content:**

    ```json
    {
        "data": [
            {
                "classification": 1,
                "extra_detail": "",
                "id": 1,
                "item": "1号电池"
            },
            {
                "classification": 32,
                "extra_detail": "",
                "id": 2,
                "item": "用剩下1千克石膏"
            },
            {
                "classification": 32,
                "extra_detail": "",
                "id": 3,
                "item": "用剩下的1千克水泥"
            }
        ]
    }
    ```

* **Sample Call:**

  ```bash
    curl -X GET http://127.0.0.1:8010/download/classification?last_id=499
  ```

### Download Classification

----
  下载全量分类数据

* **URL**

  /download/classification

* **Method:**

  `GET`

* **URL Params**

* **Data Params**

  None

* **Success Response:**

  * **Code:** 200 <br />
    **Content:**
    file object

* **Sample Call:**

  ```bash
    curl -X GET http://127.0.0.1:8010/download/classification
  ```


### File Upload

----
  文件/图片上传接口

* **URL**

  /file-upload

* **Method:**

  `POST`

* **URL Params**

  **Required**

    `file=[fileobject]`

  **Optional**

* **Data Params**

  **Required**
  

  **Optional**

* **Success Response:**

  * **Code:** 200 <br />
    **Content:**

    ```text
    3ab0953778b8e3a615e58ab2c657cf4b
    ```

* **Sample Call:**

  ```bash
    curl -X POST http://127.0.0.1:8010/file-upload \
    -F extension=jpg \
    -F file=@image.jpeg
  ```

### Add Garbage

----
  上传新分类垃圾

* **URL**

  /classification/

* **Method:**

  `POST`

* **URL Params**

  **Required**

  **Optional**

* **Data Params**

  **Required**

    `item=[string]`

    `classification=[integer]`

  **Optional**

  `extra_detail=[string]`
  
  `image_hash=[string]`

* **Success Response:**

  * **Code:** 200 <br />
    **Content:**

    ```text
    OK
    ```

* **Sample Call:**

  ```bash
    curl -X POST \
    http://127.0.0.1:8010/classification/ \
    -F classification=4 \
    -F 'item=杰宝'
  ```

### Updade Classification Info

----
  更新垃圾信息

* **URL**

  /classification/:id

* **Method:**

  `PUT`

* **URL Params**

  **Required**

    `id=[integer]`

  **Optional**

* **Data Params**

  **Required**

  **Optional**

  `extra_detail=[string]`
  
  `classification=[integer]`

* **Success Response:**

  * **Code:** 200 <br />
    **Content:**

    ```text
    OK
    ```

* **Sample Call:**

  ```bash
    curl -X POST \
    http://127.0.0.1:8010/classification/4000 \
    -F classification=4
  ```
