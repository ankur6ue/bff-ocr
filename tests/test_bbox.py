import requests
import time

url = 'http://127.0.0.1:5001' # The root url of the flask app

def test_get_bboxes():
    image_name = 'trading-issue.jpg'
    r = requests.get(url + '/bboxes', {'file_name': image_name})
    assert r.status_code == 200
    rec_results = json.loads(r.content)
    print(r)




# test_get_bboxes()
# test_post_url_expired()