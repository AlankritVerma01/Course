"""
Direct handling of sqlite3 database (manages tables, executes queries)
"""

import sqlite3
import json
from datetime import datetime

# Files containing data
COURSES_FILE = 'data/courses.json'
PREREQUISITES_FILE = 'data/prerequisites.json'

### Database Schema
USER_SCHEMA = """
    User (username      TEXT PRIMARY KEY NOT NULL,
          password      TEXT NOT NULL)
"""
COURSE_SCHEMA = """
    Course (id          CHAR(8) PRIMARY KEY NOT NULL,
            name        TEXT NOT NULL,
            description TEXT,
            link        TEXT)
"""
COURSE_FIELDS_SCHEMA = """
    CourseFields (course_id      CHAR(8) NOT NULL,
                  field_name     TEXT NOT NULL,
                  field_value    TEXT,
                  PRIMARY KEY (course_id, field_name),
                  FOREIGN KEY(course_id) REFERENCES Course(id))
"""
COURSE_PREREQS_SCHEMA = """
    CoursePrereqs (course_id     CHAR(8) PRIMARY KEY NOT NULL,
                   prereqs_json  TEXT,
                   FOREIGN KEY(course_id) REFERENCES Course(id))
"""
# Table containing prerequisite-postrequisite relation between two courses
COURSE_PRE_POST_REQ_SCHEMA = """
    CoursePrePostReq (postreq_id CHAR(8) NOT NULL,
                      prereq_id  CHAR(8) NOT NULL,
                      PRIMARY KEY (postreq_id, prereq_id),
                      FOREIGN KEY(postreq_id) REFERENCES Course(id),
                      FOREIGN KEY(prereq_id) REFERENCES Course(id))
"""
REVIEW_SCHEMA = """
    Review (id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp            DATETIME NOT NULL,
            course_id            CHAR(8) NOT NULL,
            username             TEXT NOT NULL,
            rating               INT NOT NULL CHECK(0 <= rating AND rating <= 10),
            content              TEXT,
            UNIQUE (course_id, username),
            FOREIGN KEY(course_id) REFERENCES Course(id),
            FOREIGN KEY(username) REFERENCES User(username))
"""

### Complex SQL Queries
GET_COURSE_ORDER_BY_REVIEWS = """
    SELECT Course.id, COUNT(Review.id) FROM Course LEFT JOIN Review ON Course.id=Review.course_id
    GROUP BY Course.id ORDER BY COUNT(Review.id)
    DESC LIMIT ?
"""
GET_COURSE_AVERAGE_RATING = """
    SELECT CAST(SUM(rating) AS REAL) / COUNT(id) FROM Review WHERE course_id=?
"""
GET_COURSE_ORDER_BY_AVERAGE_RATING = """
    SELECT Course.id, CAST(SUM(Review.rating) AS REAL) / COUNT(Review.id) FROM Course LEFT JOIN Review ON Course.id=Review.course_id
    GROUP BY Course.id ORDER BY CAST(SUM(Review.rating) AS REAL) / COUNT(Review.id)
    DESC LIMIT ?
"""

### SQL Queries
INSERT_USER_QUERY =                       "INSERT INTO User VALUES (?, ?)"
INSERT_COURSE_QUERY =                     "INSERT INTO Course VALUES (?, ?, ?, ?)"
INSERT_COURSE_FIELDS_QUERY =              "INSERT INTO CourseFields VALUES(?, ?, ?)"
INSERT_COURSE_PREREQS_QUERY =             "INSERT INTO CoursePrereqs VALUES (?, ?)"
INSERT_COURSE_PRE_POST_REQ_SCHEMA_QUERY = "INSERT INTO CoursePrePostReq VALUES (?, ?)"
INSERT_REVIEW_QUERY =                     "INSERT INTO Review(timestamp, course_id, username, rating, content) VALUES (strftime('%s'), ?, ?, ?, ?)"
INSERT_REVIEW_CUSTOM_DATE =               "INSERT INTO Review(timestamp, course_id, username, rating, content) VALUES (?, ?, ?, ?, ?)"
UPDATE_REVIEW_QUERY =                     "UPDATE Review SET rating=?, content=?, timestamp=strftime('%s') WHERE course_id=? AND username=?"
DELETE_REVIEW_QUERY =                     "DELETE FROM Review WHERE course_id=? AND username=?"

GET_USER_BY_USERNAME =                    "SELECT username, password FROM User WHERE username=?"
GET_COURSE_IDS =                          "SELECT id FROM Course LIMIT ?"
GET_COURSE_BY_ID =                        "SELECT * FROM Course WHERE id=?"
GET_COURSE_FIELDS_BY_ID =                 "SELECT field_name, field_value FROM CourseFields WHERE course_id=?"
GET_REVIEW_BY_COURSE_ID =                 "SELECT * FROM Review WHERE course_id=? ORDER BY timestamp DESC LIMIT ?"
GET_REVIEW_BY_USERNAME =                  "SELECT * FROM Review WHERE username=? ORDER BY timestamp DESC LIMIT ?"
GET_REVIEW_BY_COURSE_ID_AND_USERNAME =    "SELECT * FROM Review WHERE course_id=? AND username=?"
GET_COURSE_PREREQS_BY_ID =                "SELECT prereqs_json FROM CoursePrereqs WHERE course_id=?"
GET_PREREQ_COURSES_BY_COURSE_ID =         "SELECT * FROM CoursePrePostReq WHERE postreq_id=?"
GET_POSTREQ_COURSES_BY_COURSE_ID =        "SELECT * FROM CoursePrePostReq WHERE prereq_id=?"


class SqlDb:
    def __init__(self, db_file):
        self._db_file = db_file # File that contains database
        self._con = sqlite3.connect(db_file) # Connection object to database

        self._con.execute("PRAGMA foreign_keys = 1") # Turn on foreign keys


    ### Database Management
    def _commit(self):
        """Saves all changes to database"""
        self._con.commit()

    def _rollback(self):
        """Rolls back changes made to database"""
        self._con.rollback()

    def close(self):
        """Close database connection"""
        self._con.close()

    def print_user_db(self):
        """Prints all user-related tables in database"""
        print(self._con.execute("SELECT * FROM User").fetchall())
        print(self._con.execute("SELECT * FROM Review").fetchall())

    def print_course_db(self):
        """Prints all course-related tables in database"""
        print(self._con.execute("SELECT * FROM Course").fetchall())
        print(self._con.execute("SELECT * FROM CourseFields").fetchall())
        print(self._con.execute("SELECT * FROM CoursePrereqs").fetchall())
        print(self._con.execute("SELECT * FROm CoursePrePostReq").fetchall())

    def reset_user_db(self):
        """Deletes all user-related data in database and reinitialises it"""
        if (input(f"You are about to reset all user data in {self._db_file}. Confirm? (y/n) ").lower() == "y"):
            self._drop_user_tables()
            self._create_user_tables()
            self._commit()

    def reset_course_db(self):
        """Deletes all course-related data in database and reinitialises it"""
        if (input(f"You are about to reset all course data in {self._db_file}. Confirm? (y/n) ").lower() == "y"):
            self._drop_course_tables()
            self._create_course_tables()
            self._commit()

    def add_test_user_data(self):
        """Note: Reset database before creating test data"""
        self.add_user("user", "user")
        self.add_user("admin", "admin")
        self.add_review("CSCB20H3", "user", 10, "This course is great, it is the best", int(datetime(2023, 4, 1, 12, 24, 31).timestamp()))
        self.add_review("CSCB20H3", "admin", 6, "I've never taken this course", int(datetime(2023, 3, 1, 14, 23, 41).timestamp()))


    ### Modify data
    def add_user(self, username, password):
        """Returns True if user successfully added"""
        return self._execute_query(INSERT_USER_QUERY, (username, password), verbose=False) is not None

    def insert_course_data(self, courses_file, prerequisites_file):
        """Insert all course and prerequisite data into database"""
        # Add data to Course and CourseFields tables
        with open(courses_file, 'r', encoding='utf-8') as f:
            course_data = json.load(f)
            for data in course_data:
                self.add_course(data['code'], data['name'], data['description'], data['link'], {field: value for field, value in data['fields'].items()})
        # Add data to CoursePrereqs and CoursePrePostReq tables
        with open(prerequisites_file, 'r') as f:
            prerequisites_data = json.load(f)
            for data in prerequisites_data:
                if data['prereqs'] is not None:
                    self.add_prerequisites(data['code'], data['prereqs'])

    def add_course(self, id, name, description='', link='', fields=dict()):
        """Returns True if course successfully added"""
        queries_and_params = [(INSERT_COURSE_QUERY, (id, name, description, link))]
        for field, value in fields.items():
            queries_and_params.append((INSERT_COURSE_FIELDS_QUERY, (id, field, value)))
        return self._execute_queries(queries_and_params) is not None

    def generate_prereq_courses(prerequisites):
        """Generator object for recursively returning courses in a prerequisite tree"""
        if type(prerequisites) == str:
            yield prerequisites
        elif type(prerequisites) == dict:
            for course in prerequisites['args']:
                yield from SqlDb.generate_prereq_courses(course)

    def add_prerequisites(self, course_id, prerequisites):
        """Returns True if prerequisites successfully added"""
        if self._execute_query(INSERT_COURSE_PREREQS_QUERY, (course_id, json.dumps(prerequisites))) is None:
            return False
        for prereq_id in SqlDb.generate_prereq_courses(prerequisites):
            # Silence warnings, since some prerequisite courses may not exist anymore
            self._execute_query(INSERT_COURSE_PRE_POST_REQ_SCHEMA_QUERY, (course_id, prereq_id), verbose=False)
        return True

    def add_review(self, course_id, username, rating, content, timestamp=None):
        """Returns True if review successfully added"""
        if timestamp is None:
            return self._execute_query(INSERT_REVIEW_QUERY, (course_id, username, rating, content)) is not None
        return self._execute_query(INSERT_REVIEW_CUSTOM_DATE, (timestamp, course_id, username, rating, content)) is not None

    def edit_review(self, course_id, username, rating, content):
        """Returns True if review successfully edited"""
        return self._execute_query(UPDATE_REVIEW_QUERY, (rating, content, course_id, username)) is not None

    def delete_review(self, course_id, username):
        """Returns True if review successfully deleted"""
        return self._execute_query(DELETE_REVIEW_QUERY, (course_id, username)) is not None

    ### Get user data
    def get_password(self, username):
        """Returns password associated with username, or None if username not in database"""
        query = self._execute_query(GET_USER_BY_USERNAME, (username,))
        if query is not None and (result := query.fetchone()) is not None:
            return result[1]

    def get_user_reviews(self, username, limit=-1):
        """
        Returns list of reviews posted by a user

        Return Schema:
        [
            {
                "review_id": Unique id of Review,
                "timestamp": Timestamp of Review in Unix Epoch,
                "course_id": Username of Review Creator,
                "rating": Rating of Review, on a scale of 0-10 (inclusive)
                "content": Additional comments of review
            }
        ]
        """
        query = self._execute_query(GET_REVIEW_BY_USERNAME, (username, limit))
        if query is not None:
            return [{"review_id": row[0],
                     "timestamp": row[1],
                     "course_id": row[2],
                     "rating": row[4],
                     "content": row[5]} for row in query]


    ### Get course data
    def get_courses(self, limit=-1):
        """Returns list of ids of all courses in database"""
        query=self._execute_query(GET_COURSE_IDS, (limit,))
        if query is not None:
            return [row[0] for row in query]

    def get_courses_order_by_reviews(self, limit=-1):
        """Returns courses ordered by number of users who have taken them

        Return Schema:
        [
            (Course Id, Number of Users)
        ]
        """
        query = self._execute_query(GET_COURSE_ORDER_BY_REVIEWS, (limit,))
        if query is not None:
            return [(row[0], row[1]) for row in query]

    def get_courses_order_by_average_rating(self, limit=-1):
        """Returns courses ordered by average rating

        Return Schema:
        [
            (Course Id, Average Rating)
        ]
        """
        query = self._execute_query(GET_COURSE_ORDER_BY_AVERAGE_RATING, (limit,))
        if query is not None:
            return [(row[0], row[1]) for row in query]


    ### Get Data for Single Course
    def get_course_basic_info(self, course):
        """Returns basic course information in format

        Return Schema:
        {
            "name": Course Name,
            "description": Course Description,
            "link": Course Link
        }
        """
        course_query = self._execute_query(GET_COURSE_BY_ID, (course,))
        if course_query is not None and (course_results := course_query.fetchone()) is not None:
            return {"name": course_results[1],
                    "description": course_results[2],
                    "link": course_results[3]
                   }

    def get_course_full_info(self, course):
        """Returns full course information in format

        Return Schema:
        {
            "name": Course Name,
            "description": Course Description,
            "link": Course Link,
            "fields": [
                "name": Field Name,
                "value": Field Value
            ]
        }
        """
        info = self.get_course_basic_info(course)
        if info is not None:
            course_field_query = self._execute_query(GET_COURSE_FIELDS_BY_ID, (course,))
            course_field_results = course_field_query.fetchall() if course_field_query is not None else []
            info["fields"] = [{"name": row[0],
                               "value": row[1]
                              } for row in course_field_results]
            return info

    def get_course_reviews(self, course, limit=-1):
        """Returns list of reviews about course in format

        Return Schema:
        [
            {
                "review_id": Unique id of Review,
                "timestamp": Timestamp of Review in Unix Epoch,
                "username": Username of Review Creator,
                "rating": Rating of Review, on a scale of 0-10 (inclusive)
                "content": Additional comments of review
            }
        ]
        """
        query = self._execute_query(GET_REVIEW_BY_COURSE_ID, (course, limit))
        if query is not None:
            return [{"review_id": row[0],
                     "timestamp": row[1],
                     "username": row[3],
                     "rating": row[4],
                     "content": row[5]} for row in query]

    def get_course_review(self, course, user):
        """
        Returns review by user on course in format, or None if no such review

        Return Schema:
        {
            "review_id": Unique id of Review,
            "timestamp": Timestamp of Review in Unix Epoch,
            "username": Username of Review Creator,
            "rating": Rating of Review, on a scale of 0-10 (inclusive)
            "content": Additional comments of review
        }
        """
        query = self._execute_query(GET_REVIEW_BY_COURSE_ID_AND_USERNAME, (course, user))
        if query is not None and (result := query.fetchone()) is not None:
            return {"review_id": result[0],
                    "timestamp": result[1],
                    "username": result[3],
                    "rating": result[4],
                    "content": result[5]}

    def get_course_average_rating(self, course):
        """Returns average rating of reviews of course, or None if no reviews"""
        query = self._execute_query(GET_COURSE_AVERAGE_RATING, (course,))
        if query is not None and (result := query.fetchone()) is not None:
            return result[0]

    def get_course_prereqs(self, course):
        """Returns dictionary representing course prerequisites structure

        Return Schema:
        {
            'op': "and"/"or",
            'args': [
                list of courses/prerequisite expressions
            ]
        }
        """
        query = self._execute_query(GET_COURSE_PREREQS_BY_ID, (course,))
        if query is not None and (result := query.fetchone()) is not None:
            return json.loads(result[0])

    def get_prereq_courses(self, course):
        """Returns list of prerequisite courses of course"""
        query = self._execute_query(GET_PREREQ_COURSES_BY_COURSE_ID, (course,))
        if query is not None:
            return [row[1] for row in query]

    def get_postreq_courses(self, course):
        """Returns list of postrequisite courses of course"""
        query = self._execute_query(GET_POSTREQ_COURSES_BY_COURSE_ID, (course,))
        if query is not None:
            return [row[0] for row in query]


    ### Database Manipulation
    def _create_user_tables(self):
        """Creates user-related tables in database"""
        self._con.execute(f"CREATE TABLE IF NOT EXISTS {USER_SCHEMA}")
        self._con.execute(f"CREATE TABLE IF NOT EXISTS {REVIEW_SCHEMA}")
        self._commit()

    def _create_course_tables(self):
        """Creates course-related tables in database"""
        self._con.execute(f"CREATE TABLE IF NOT EXISTS {COURSE_SCHEMA}")
        self._con.execute(f"CREATE TABLE IF NOT EXISTS {COURSE_FIELDS_SCHEMA}")
        self._con.execute(f"CREATE TABLE IF NOT EXISTS {COURSE_PREREQS_SCHEMA}")
        self._con.execute(f"CREATE TABLE IF NOT EXISTS {COURSE_PRE_POST_REQ_SCHEMA}")
        self._commit()

    def _drop_user_tables(self):
        """Drops all user-related tables in database"""
        self._con.execute("DROP TABLE IF EXISTS Review")
        self._con.execute("DROP TABLE IF EXISTS User")
        self._commit()

    def _drop_course_tables(self):
        """Drops course-related tables in database"""
        self._con.execute("DROP TABLE IF EXISTS CoursePrePostReq")
        self._con.execute("DROP TABLE IF EXISTS CoursePrereqs")
        self._con.execute("DROP TABLE IF EXISTS CourseFields")
        self._con.execute("DROP TABLE IF EXISTS Course")
        self._commit()

    def _execute_query(self, query, params=[], verbose=True):
        """Attempts to execute query, returning cursor if successful and None if unsuccessful"""
        try:
            cur = self._con.execute(query, params)
            self._commit()
            return cur
        except sqlite3.IntegrityError as e:
            if verbose:
                print(e)
                print(f"Could not execute \"{query}\" with parameters {params}")
            return None

    def _execute_queries(self, queries_and_params):
        """Attempts to execute queries, returning array of cursors if successful and None if unsuccessful"""
        curs = []
        for query, params in queries_and_params:
            try:
                curs.append(self._con.execute(query, params))
            except sqlite3.IntegrityError as e:
                print(e)
                print(f"Could not execute \"{query}\" from list of queries with parameters {params}")
                self._rollback()
                return None
        self._commit()
        return curs


# Callable functions for maintenance and testing purposes
def get_db():
    return SqlDb("database.db")

def reset_users():
    db = get_db()
    db.reset_user_db()

def reset_courses():
    # Note: Also resets user data due to foreign key dependencies
    db = get_db()
    db.reset_user_db()
    db.reset_course_db()
    db.insert_course_data(COURSES_FILE, PREREQUISITES_FILE)

def reset_db():
    reset_courses()
    reset_users()

def test_queries():
    db = get_db()
    # Assume that add_test_user_data has been called
    tests = [
        (" - Password of 'user': ", db.get_password('user')),
        (" - Reviews Posted by 'user': ", db.get_user_reviews('user')),
        (" - 10 Courses: ", db.get_courses(10)),
        (" - Basic Course Info of CSCB20H3: ", db.get_course_basic_info('CSCB20H3')),
        (" - Full Course Info of CSCB20H3: ", db.get_course_full_info('CSCB20H3')),
        (" - Prerequisite Structure of MATC82H3: ", db.get_course_prereqs('MATC82H3')),
        (" - Prerequisites of CSCA48H3: ", db.get_prereq_courses('CSCA48H3')),
        (" - Prerequisites of MATA31H3: ", db.get_prereq_courses('MATA31H3')),
        (" - Postrequisites of CSCA48H3: ", db.get_postreq_courses('CSCA48H3')),
        (" - Reviews of CSCB20H3: ", db.get_course_reviews('CSCB20H3')),
        (" - Review of CSCB20H3 by user 'admin': ", db.get_course_review('CSCB20H3', 'admin')),
        (" - Average Rating of CSCB20H3: ", db.get_course_average_rating('CSCB20H3')),
        (" - Average Rating of MATA31H3: ", db.get_course_average_rating('MATA31H3')),
        (" - Top 10 Courses by Reviews: ", db.get_courses_order_by_reviews(10)),
        (" - Top 10 Courses by Rating: ", db.get_courses_order_by_average_rating(10))
    ]
    for test, result in tests:
        print(test + str(result))


if __name__ == "__main__":
    test_queries()
