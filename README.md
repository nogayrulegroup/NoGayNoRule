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
  返回图片识别的结果

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
