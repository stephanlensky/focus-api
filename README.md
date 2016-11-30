# Focus Student Information System API

A simple RESTful Flask server to retrieve and parse pages from the Focus for Schools Student Information System (SIS). Although it was created for the [Academy for Science and Design](http://www.asdnh.org/), this service should work for any school running the Focus SIS. See [Supporting Additional Schools](#supportingadditionalschools) for details. to the equivalent ones for your school. The project is currently still in early development, so there are a bunch of bugs and the module does not yet have an installer.

**Complete**

- Basic changing semester/year (marking period)
- Courses
- Calendar
- Demographic
- Schedule

**In Progress**

- Authentication (doesn't account for session timing out)
- Portal (missing alerts)

**Planned**

- Descriptions for events from calendar
- Enhanced marking period support (choose redirect page)
- Address information
- Absences
- Referrals
- Final grades and GPA

**Unplanned**

- Attendance chart
- Preferences

## Running the server

### Dependencies

- [Flask](https://pypi.python.org/pypi/Flask)
- [beautifulsoup4](https://pypi.python.org/pypi/beautifulsoup4)
- [requests](https://pypi.python.org/pypi/requests)
- [python-dateutil](https://pypi.python.org/pypi/python-dateutil)

### Installation

Before doing anything else, make sure you have all of the dependencies installed:

```bash
pip3 install flask requests beautifulsoup4 python-dateutil
```

Next, clone the repository and run the `app.py` to start the server. In it's default configuration, it will host itself locally on your machine at http://127.0.0.1:5000/api/v1.

```bash
git clone https://github.com/dvshka/focus-api.git && cd focus-api
python3 focus/app.py
```

### Supporting Additional Schools

By default, this module will attempt to connect to ASDNH's Focus servers. In order to modify the program to work for other schools, a some constants may need be changed at the top of `app.py`.

```python
tld = 'https://focus.asdnh.org/'
urls = {
    'login': tld + 'focus/index.php',
    'portal': tld + 'focus/Modules.php?modname=misc/Portal.php',
    'course_pre': tld + 'focus/Modules.php?modname=Grades/StudentGBGrades.php?course_period_id=',
    'schedule': tld + 'focus/Modules.php?modname=Scheduling/Schedule.php',
    'calendar_pre': tld + 'focus/Modules.php?modname=School_Setup/Calendar.php&',
    'demographic': tld + 'focus/Modules.php?modname=Students/Student.php',
    'absences': tld + 'focus/Modules.php?modname=Attendance/StudentSummary.php',
}
```

As you can see, all URLs are build dynamically using from a top level domain. It may be enough to simply change the TLD, but if your implementation of Focus differs slightly, the URLs in `urls` may also need to be modified. If there are other bugs related to your specific school, please open an issue [here](https://github.com/dvshka/focus-api/issues) and I will look into it as soon as possible.

## Client Documentation

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

### /api/v1/login

**Accepts: POST**

Takes JSON formatted login information and attempts to log in to Focus. Returns your session ID if your login was successful and a 401 invalid credentials error if it was not. All other endpoints require a valid session ID cookie in order to work.

```javascript
{
  "username": "your.username"
  "password": "yourpassword"
}
```
```javascript
{
  "PHPSESSID": "yoursessid"
}
```

### /api/v1/marking_period

**Accepts: POST**

Takes a year and a marking period ID and changes the current marking period. Arguments are taken as a query string, with the year as `year` and the marking period ID as `mp`. Returns the portal for the new marking period. Information about available marking periods is appended to the JSON object returned by every other endpoint, not including login. However, only IDs for the selected year are available due to constraints set by the Focus web application. When changing to a new year, the marking period ID does not seem to be used, so any value will work.

```javascript
  "current_mp_year": 2015
  "current_mp_id": 315
  "available_mp_years": [2011, 2012, 2013, 2014, 2015, 2016, 2017]
  "available_mp_ids": [314, 315]
```

### /api/v1/portal

**Accepts: GET**

Returns a JSON object in the following format with information from the portal page:

```javascript
{
  "events": [
    {
      "description": "Spark Conference"
      "date": '2016-12-14'
    },
    ...
  ]
  "courses": [
    {
      "days": "MWH", 
      "id": 11136, 
      "letter_grade": "A+", 
      "name": "Learning Studios", 
      "percent_grade": 100, 
      "period": 1, 
      "teacher": "Douglass Adam Belley"
    }, 
    ...
    // marking period information
}
```

### /api/v1/course/<int:course_id>

**Accepts: GET**

Returns information about the course ID in the URL. Make sure that you are in the same marking period as the course ran, or this will not return any information about the course. Note that not all fields are applicable for all courses and assignments. For example, some courses do not use categories or have any assignments. Some assignments may not be graded, or may be a pass/fail grade. This example has both categories and assignments for your convenience.

```javascript
{
  "assignments": [
    {
      "assigned": "2016-10-20T00:00:00", 
      "category": "Project Work", 
      "due": "2016-12-19T00:00:00", 
      "max_grade": 50, 
      "name": "Lit Review Rough Draft", 
      "status": "ng"
    }, 
    {
      "assigned": "2016-11-30T00:00:00", 
      "category": "Project Work", 
      "due": "2016-11-30T00:00:00", 
      "name": "Outline and Annotated Bibliography Conference", 
      "status": "pass"
    },
    {
      "assigned": "2016-11-02T00:00:00", 
      "category": "Project Work", 
      "due": "2016-11-03T00:00:00", 
      "letter_overall_grade": "A+", 
      "max_grade": 3, 
      "name": "Status Check 3", 
      "percent_overall_grade": 100, 
      "status": "graded", 
      "student_grade": 3.0
    }, 
    ...
  ],
  "categories": [
    {
      "letter_grade": "A+", 
      "name": "Project Work", 
      "percent_grade": 100, 
      "percent_weight": 80
    }, 
    ...
  ],
  "letter_grade": "A+", 
  "name": "Learning Studios", 
  "percent_grade": 100, 
  "period": 1, 
  "teacher": "Douglass Adam Belley"
  // marking period information
}
```

### /api/v1/schedule

**Accepts: GET**

Returns a student's full year schedule, taken from Focus's "Class Registration/Schedule" page. The student who's schedule was used for this example has more courses than those listed, but they have ommitted so as to not take as much space. 

```javascript
{
  "courses": [
    {
      "days": "MWH", 
      "name": "Learning Studios", 
      "period": 1, 
      "room": "161", 
      "teacher": "Douglass Adam Belley", 
      "term": "year"
    },
    ...
    {
      "days": "MTWHF", 
      "name": "Blue Advisory", 
      "room": "161", 
      "teacher": "Patricia Ann Sockey", 
      "term": "year"
    },
    ...
    {
      "days": "MWH", 
      "name": "Economics", 
      "period": 7, 
      "room": "147", 
      "teacher": "Kimberly A Cashin", 
      "term": "s2"
    }, 
    ...
  ], 
  // marking period information
}
```

### /api/v1/calendar

**Accepts: GET**

Takes a year and month as arguments in the form of a query string(`year` and `month`) and returns the calendar for that month. Retrieving the detailed description for an event requires an additional API call which has not yet been implemented. The year and month that the calendar is from has been included for debugging purposes (calling this function with an invalid year and month combination has undefined behaviour).

```javascript
{
  "events": [
    {
      "date": "2016-11-02", 
      "id": "92121", 
      "name": "Spanish American War and March of the Flag Source ORQs", 
      "type": "assignment"
    }, 
    {
      "date": "2016-11-07", 
      "id": "697", 
      "name": "Progress Reports", 
      "type": "event"
    }, 
    ...
  ], 
  "month": 11, 
  "year": 2016
  // marking period information
}
```

### /api/v1/demographic

**Accepts: GET**

Returns basic information about the student account and the student's most recent recorded picture. The picture is encoded as a base64 jpg. Some information in the example has been redacted for privacy reasons.

```javascript
{
  "arrival_bus": [REDACTED], 
  "birthday": [REDACTED], 
  "cumulative_file": true, 
  "dismissal_bus": [REDACTED], 
  "email": [REDACTED], 
  "force_pass_change": false, 
  "gender": "male", 
  "grade": 11, 
  "id": [REDACTED], 
  "level": 6, 
  "locker": 437, 
  "medical_record_status": "need emergency form", 
  "name": "Stephan Lensky", 
  "pass_length": [REDACTED], 
  "photo_auth": true, 
  "picture": "/9j/4AAQSkZJRgA...7i0zUDmcD3qSH/VLQB//Z", 
  "username": "stephan.lensky"
  // marking period information
}
```
