# UTSC Course Information Website

## Description
The website is a helper website which a student can use while he is doing his course planning by searching for courses and visualising their prerequisites and postrequisites. Currently, only the CMS courses can be visualised as we were able to just find data about them.

## IMPORTANT

### HOW TO RUN THE WEBSITE
1. Create virtual environment and activate it
python3 -m venv venv
Note: Activation depends on operating system (https://docs.python.org/3/library/venv.html#how-venvs-work)

2. Install site dependencies at the requirements.txt file in venv using pip
pip install -r requirements.txt

3. Run main.py file
python3 main.py


4. Open site in BROWSER
URL: http://localhost:8001

5. Click login button and log in with credentials
- Username: foo
- Password: bar

## Features
1. Requisite Tree
1. Find all the prerequisites of courses and display them in a graph. In case the user selects more than 1 course, the graph that is generated is connected - just 1 graph is made for both the courses.
   - Note - if there are no common prerequisite courses, then there is no way to merge the graphs, so they are displayed separately.
   - The main idea behind this is that if a student wants to take a course, they will be able to see all the courses which they need to take in order.
   - Also, if they plan to take more than 1 intended course, they will see all the courses they need to take in a graph.
   - For the creation of the graphs, we are using the D3.js library.
2. Find all courses which have a given course(s) as a partial prerequisite.
   - The term post-requisite means that all the courses which have the given course(s) as a prerequisite.
   - So for example, as the course CSCA08 is a prerequisite for a lot of courses, the graph shows all the courses which have CSCA08 as a prerequisite.
   - Also, to be clear, the graph that is shown is shown in order.
3. Find all courses which have a given course(s) as the complete prerequisite.
   - The courses that are listed here are the courses which the user can take after they have done the given selected courses.
4. For all the graphs that are made, the color red is used to highlight the head nodes, and proper arrows are shown to clear the depiction.
5. Another important feature is when a user clicks on any course (node) on the graph, they are redirected to a page which gives them the full information about the course.

2. Course reviews and comments
1. For each course in the database, we have implemented a course review page.
2. Here a user can come and add their reviews to the course and give it ratings.
3. Additionally, a user can also sort through all the courses based on the average rating or number of reviews that a course has.

3. Course Search
1. From all the database of the courses that we have, a user is able to search courses and sort them based on different parameters.
2. When a user clicks on a course, they are redirected to the course’s webpage which has all the information about the courses (also the ratings and the reviews).

## Other features of the website
1. We also have implemented a login page, where a user can log in, and we store their data. When a user logs in, we are able to store their data and courses they have already taken and then show them on our home page.

## Important Files
- `main.py` - Flask functions for creating the website (GET and POST decorators at bottom of file)
- `requisite_tree.py` - Functions for creating pre/postrequisite tree objects
- `sqlite_db.py` - Functions for directly handling sqlite3 database (ex. contains SQL table queries)
- `templates/template.html` - Template used by website
- `static/js/courses-tree-visual.js` - File containing requisite tree rendering code
