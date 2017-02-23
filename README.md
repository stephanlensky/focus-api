# Focus Student Information System API

A simple RESTful Flask server to retrieve and parse pages from the Focus for Schools Student Information System (SIS). Although it was created for the [Academy for Science and Design](http://www.asdnh.org/), this service should work for any school running the Focus SIS (see [supporting additional schools](#supporting-additional-schools) for details).

**Complete**

- Authentication
- Setting semester/year
- Portal
- Courses
- Calendar (monthly)
- Detailed information about events from calendar
- Demographic
- Schedule
- Referrals
- Absences
- Address information
- Term exam grades
- Overall term grades

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

Next, clone the repository and run the `app.py` to start the server. In it's default configuration, it will host itself locally on your machine at http://127.0.0.1:5000/api/v2.

```bash
git clone https://github.com/kidcontact/focus-api.git && cd focus-api
python3 focus/app.py
```

### Supporting Additional Schools

By default, this module will attempt to connect to ASDNH's Focus servers. In order to modify the program to work for other schools, constants need be changed at the top of `app.py`.

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

As you can see, all URLs are build dynamically from a given top level domain. It may be enough to simply change the TLD, but if your implementation of Focus differs slightly, the URLs in `urls` may also need to be modified. Additionally, the session timeout in `focus/auth.py` may need to be changed to match your school's settings. If there are other bugs related to your specific school, please open an issue [here](https://github.com/dvshka/focus-api/issues) and I will look into it as soon as possible.

## Client Documentation

The API does its best to follow RESTful guidelines while still connecting as an unprivileged user to Focus servers. As such, using the API should be fairly self explanatory. All payloads are passed and returned using JSON unless otherwise specified.

```python
# Python example using requests

# log in and retrieve session cookie
d = {'username':'your.username', 'password':'yourpassword'}
r = requests.post('http://127.0.0.1:5000/api/v1/session', json=d)
sess_id = r.cookies

# change the marking period to semester two of 2015
d = {'year': 2015, 'mp_id': 315}
r = requests.put('http://127.0.0.1:5000/api/v1/session', json=d, cookies=sess_id

# retrieve and print the student's courses
r = requests.get('http://127.0.0.1:5000/api/v1/portal', cookies=sess_id)
print(r.json()['courses'])

```

### session

**Accepts: GET, POST, PUT**

###### GET

Returns the username and timeout (in seconds, UTC) associated with the session id cookie provided. 403s when there is no session associated with the cookie.

```javascript
{
  "timeout": 1481819260.7088594, 
  "username": "stephan.lensky"
}
```

###### POST

Takes JSON formatted login information and attempts to log in to Focus. Returns some information about the login and a session cookie if your login was successful. 401s if it was not. All other endpoints require a valid session ID cookie in order to work.

Sent:
```javascript
{
  "username": "your.username"
  "password": "yourpassword"
}
```
Returned:
```javascript
// JSON
{
  "timeout": 1481819260.7088594, 
  "username": "your.username"
}
// Cookie
{
    PHPSESSID: "your_session_id"
}
```

###### PUT

Updates the marking period given a year and marking period id. An additional `redirect` parameter may be given to specify the page returned after changing the marking period. Valid redirect values follow the same format as API urls. So for example, to retrieve the new portal, send `portal`. To retrieve course 15206, send `course/15206`. Redirection to a url under `calendar` is not supported. When no redirect is specified, the portal of the new marking period will be provided.

```javascript
{
  "year": 2015
  "mp_id": 315
  "redirect": "course/15206" // optional
}
```

The JSON returned will be equivalent to sending a GET request to `course/15206`. However, doing both the marking period change and redirection in one step takes less time.

### portal

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
  ],
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
  ],
  "upcoming": [
    {
      "assignments": [
        {
          "due": "2017-02-14T00:00:00", 
          "name": "Calorie Worksheet"
        },
        ...
       ],
       "course_id": 11131
    },
    ...
  ],
  "alert": "You have been absent 9 periods" // may not be present
  // marking period information
}
```

### courses

**Accepts: GET**

Returns information about all courses that the student has. This endpoint scrapes information from every course page individually, which means that it has to load up to eight full pages in order to retrieve everything. As a result calling this method will take quite some time. Use it at your own risk.

```javascript
{
  courses: [
    {
      // see below for course format
    },
    ...
  ]
  // marking period information
}
```

### courses/<int:id>

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

### schedule

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

### calendar/<int:year>/<int:month>/<int:day>

**Accepts: GET**

Returns a calendar for the specificity provided. The day may be omitted to give a full month, and the month may be omitted to get a full year. Focus provides calendars only by month, so retrieving a full year's calendar is very slow. To retrieve additional information about events, use `calendar/assignments/<int:id>` and `calendar/occasions/<int:id>`, depending on the type of the event.

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
      "type": "occasion"
    }, 
    ...
  ], 
  
  // if you request a calendar only for one day, that day will be listed here as well
  // for a full year, only the year will be listed
  "month": 11, 
  "year": 2016
  // marking period information
}
```

### calendar/occasion/<int:id>

**Accepts: GET**

Retrieves detailed information about a calendar event of type `occasion`. If the event does not exist, a status code of 400 is returned. Please note that this is not the method for calendar events of type `assignment`. Additionally, this endpoint does not return any information about current or available marking periods.

```javascript
{
  "date": "2016-12-14", 
  "school": "Academy for Science and Design", 
  "title": "SPARK Conference ", 
  "type": "event"
}
```

### calendar/assignment/<int:id>

**Accepts: GET**

Retrieves detailed information about a calendar event of type `assignment`. If the assignment does not exist, a status code of 400 is returned. Please note that this is not the method for calendar events of type `occasion`. Additionally, this endpoint does not return any information about current or available marking periods.

```javascript
{
  "course": {
    "days": "TWF", 
    "name": "Advanced Computer Science", 
    "period": 4, 
    "teacher": "Madge  Smith"
  }, 
  "date": "2015-12-11", 
  "notes": "Binary Calculator", 
  "school": "Academy for Science and Design", 
  "title": "Assignment 7", 
  "type": "assignment"
}
```

### demographic

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

### address

**Accepts: GET**

Retrieves information from the address page in Focus. This includes address/contact information for the student and any contacts (usually parents) associated with the student. As with the demographic section, some information has been redacted.

```javascript
{
  "address": [REDACTED],
  "city": "Nashua",
  // some fields may not be present for all contacts, make sure to check
  "contacts": [
    {
      "address": [REDACATED],
      "cell_phone": [REDACTED],
      "city": "Nashua",
      "email": [REDACTED],
      "home_phone": [REDACTED],
      "name": [REDACTED],
      "private_email": [REDACTED],
      "relationship": "mother",
      "state": "NH",
      "zip": "03063"
    },
    ...
  ],
  "phone": [REDACTED],
  "state": "NH",
  "zip": "03063"
  // marking period information
}
```

### referrals

**Accepts: GET**

Returns a list of referrals that the student has receieved during the current school year. If the student has no referrals, the `referrals` array is empty and only the marking period information is returned.

```javascript
{
  "referrals": [
    {
      // see below for referrals format
    },
    ...
  ]
  // marking period information
}
```

### referrals/<int:id>

**Accepts: GET**

Returns information about a single referral (that was given during the selected year). If there is no referral with the id given, a status code of 404 will be returned.

```javascript
{
  "creation_date": "2016-10-13", 
  "display": true, 
  "entry_date": "2016-10-13", 
  "grade": 11,
  "id": 3168, 
  "last_updated": "2016-10-13", 
  "name": "Stephan Lensky",
  "notification_sent": 0, 
  "processed": true, 
  "school": "Academy for Science and Design", 
  "school_year": 2016, 
  "teacher": "Douglass Belley", 
  "violation": "Eating in classroom"
  // marking period information
}
```

### absences

**Accepts: GET**

Returns information from the table in the "Absences" section of Focus.

```javascript
{
  "absences": [
    {
      "date": "2017-02-22T00:00:00", 
      "periods": [
        {
          "days": "MWH", 
          "last_updated": "2017-02-22T08:19:21", 
          "last_updated_by": "Douglass Adam Belley", 
          "name": "Learning Studios", 
          "period": 1, 
          "status": "absent", 
          "teacher": "Douglass Adam Belley"
        }, 
        {
          "period": 2, 
          "status": "unset"
        }, 
        {
          "days": "MWH", 
          "last_updated": "2017-02-22T10:17:34", 
          "last_updated_by": "Patricia Ann Sockey", 
          "name": "Humanities III (LA)", 
          "period": 3, 
          "status": "absent", 
          "teacher": "Patricia Ann Sockey"
        }, 
        {
          "period": 4, 
          "status": "unset"
        }, 
        {
          "period": "advisory", 
          "status": "absent"
        }, 
        {
          "period": 5, 
          "status": "unset"
        }, 
        ...
      ], 
      "status": "present"
    }, 
    ...
  ],
  "days_possible": 106,
  // marking period information
}
```

### exams

**Accepts: GET**

Retrieves a list of all term exams that the student has taken. If a field is blank in Focus, it may not be present in the return for this endpoint. Additionally, this endpoint does not include marking period information.

```javascript
{
  "exams": [
    {
      // see below for exam format
    },
    ...
  ]
}
```

### exams/<int:id>

**Accepts: GET**

Retrieves information about a single exam. As with the above, different fields may be present for different exams and marking period information will not be included.

```javascript
{
  "affects_gpa": true, 
  "course_id": 10788, 
  "course_num": "MA3300", 
  "credits": 1.0, 
  "credits_earned": 1.0, 
  "gpa_points": 3.0, 
  "grade_level": 10, 
  "id": 207044, 
  "last_updated": "2016-06-20", 
  "last_updated_by": "Rosy Gandhi", 
  "letter_grade": "B", 
  "location": "Academy for Science and Design", 
  "mp_id": 315,
  "mp_name": "Semester 2",
  "name": "Precalculus Honors", 
  "percent_grade": 85, 
  "scale": "Honors & AP", 
  "subject": "Math", 
  "syear": 2015, 
  "teacher": "Rosy Gandhi", 
  "weighted_gpa_points": 3.5
}
```

### final_grades, final_grades/<int:id>, semester_grades, semester_grades/<int:id>, quarter_grades, quarter_grades/<int:id>

**Accepts: GET**

Gets information about overall grades for the duration of the class, by semester, and by quarter respectively. Information about specific grades can be retrieved by ID. These endpoints are all lumped together due to their very similar nature.

```javascript
{
  "affects_gpa": true, 
  "comment": "Good programmer! Likes to explore.", 
  "course_id": 10853, 
  "course_num": "CS4500", 
  "credits": 1.0, 
  "credits_earned": 1.0, 
  "gpa_points": 3.7, 
  "grade_level": 10, 
  "id": 205253, 
  "last_updated": "2016-06-20", 
  "last_updated_by": "Madge Smith", 
  "letter_grade": "A-", 
  "location": "Academy for Science and Design", 
  "mp_id": 313, 
  "mp_name": "Semester 2", 
  "name": "Advanced Computer Science", 
  "percent_grade": 90, 
  "scale": "Honors & AP", 
  "subject": "Areas of Specialization & Inspiration", 
  "syear": 2015, 
  "teacher": "Madge Smith", 
  "weighted_gpa_points": 4.2
}
```
