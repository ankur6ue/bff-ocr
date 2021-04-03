import pytest
import requests
import time

url = 'http://127.0.0.1:5001' # The root url of the flask app

def test_post():
    image_name = 'dog.jpg'
    r = requests.post(url + '/upload_image', {'file_name': image_name, 'content_size_min': 2000,
                                              'content_size_max': 200000})
    assert r.status_code == 200


# wrong endpoint name
def test_post_bad_ep():
    image_name = 'dog.jpg'
    r = requests.post(url + '/upload_image_', {'file_name': image_name})
    # Not Found
    assert r.status_code == 404


def test_post_bad_param1():
    image_name = 'dog.jpg'
    r = requests.post(url + '/upload_image', {'file_name_': image_name})
    assert r.status_code == 422


def test_post_bad_param2():
    # unsupported image type
    image_name = 'dog.bmp'
    r = requests.post(url + '/upload_image', {'file_name': image_name})
    # Bad Request
    assert r.status_code == 422


def test_post_bad_param3():
    # content_size_min too low
    image_name = 'dog.jpg'
    r = requests.post(url + '/upload_image', {'file_name': image_name, 'content_size_min': 20,
                                              'content_size_max': 200000})
    # Bad Request
    assert r.status_code == 422


def test_post_url():
    # This should succeed
    image_name = 'dog.jpg'
    r = requests.post(url + '/upload_image', {'file_name': image_name, 'content_size_min': 2000,
                                              'content_size_max': 80000})
    assert r.status_code == 200
    r = r.json()
    post_url = r['post_url']
    data = r['data']
    image_path = 'dog.jpg'
    with open(image_path, 'rb') as f:
        files = {'file': (image_name, f)}
        r = requests.post(post_url, data=data, files=files)
        assert r.status_code == 204


def test_post_url_oor():
    # out-of-range test: set content_size_max < image size
    image_name = 'dog.jpg'
    r = requests.post(url + '/upload_image', {'file_name': image_name, 'content_size_min': 2000,
                                              'content_size_max': 40000})
    assert r.status_code == 200
    r = r.json()
    post_url = r['post_url']
    data = r['data']
    image_path = 'dog.jpg'
    with open(image_path, 'rb') as f:
        files = {'file': (image_name, f)}
        r = requests.post(post_url, data=data, files=files)
        # Your proposed upload exceeds the maximum allowed
        assert r.status_code == 400

def test_post_url_expired():
    # expired url test: set expired to 't' seconds and then sleep for longer than that
    image_name = 'dog.jpg'
    r = requests.post(url + '/upload_image', {'file_name': image_name, 'content_size_min': 2000,
                                              'content_size_max': 80000, 'expiration': 10})
    assert r.status_code == 200
    time.sleep(12)
    r = r.json()
    post_url = r['post_url']
    data = r['data']
    image_path = 'dog.jpg'
    with open(image_path, 'rb') as f:
        files = {'file': (image_name, f)}
        r = requests.post(post_url, data=data, files=files)
        # Invalid according to Policy: Policy expired.
        assert r.status_code == 403

test_post_url_oor()
# test_post_url_expired()