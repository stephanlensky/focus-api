# Focus API

A simple RESTful Flask server to retrieve and parse pages from the Focus for Schools Student Information System. Although it was created for the [Academy for Science and Design](http://www.asdnh.org/), this service should work for any school running the Focus SIS. Simply change all of the URLs `focus/app.py` to the equivalent ones for your school. The project is currently still in early development, so there may be a few bugs and the module does not yet have an installer.

### Dependencies

- [Flask](https://pypi.python.org/pypi/Flask)
- [beautifulsoup4](https://pypi.python.org/pypi/beautifulsoup4)
- [requests](https://pypi.python.org/pypi/requests)
- [python-dateutil](https://pypi.python.org/pypi/python-dateutil)

### Running the server

Before doing anything else, make sure you have all of the dependencies installed:

```bash
pip3 install flask requests beautifulsoup4 python-dateutil
```

Next, clone the repository and run the `app.py` to start the server. In it's default configuration, it will host itself locally on your machine at http://127.0.0.1:5000/api/v1.

```bash
git clone https://github.com/dvshka/focus-api.git && cd focus-api
python3 focus/app.py
```

### Client Documentation

The API does its best to follow RESTful guidelines while still connecting as an unprivileged user to Focus servers. As such, using the API should be fairly self explanatory.

```python
# Python example using requests

# log in and retrieve session cookie
d = {'username':'your.username', 'password':'yourpassword'}
r = requests.post('http://127.0.0.1:5000/api/v1/login', json=d)
sess_id = r.json()

# change the marking period to semester two of 2015
params = {
  'year': 2015,
  'mp': 315
}
r = requests.post('http://127.0.0.1:5000/api/v1/marking_period', params=params, cookies=sess_id

# retrieve and print the student's courses
r = requests.get('http://127.0.0.1:5000/api/v1/portal', cookies=sess_id)
print(r.json()['courses'])

```

_to do_
