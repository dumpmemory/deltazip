import requests
from multiprocessing import Pool

endpoint = 'http://localhost:8000'

response_time = []
task = {
    'prompt': "Once upon a time, ",
    'model': '.cache/compressed_models/p2.8b_gsd_133'
}

def test(i):
    print(f"issuing {i}th request")
    res = requests.post(endpoint + '/inference', json=task)
    return res.json()

with Pool(4) as p:
    results = p.map(test, range(4))
    print(results)