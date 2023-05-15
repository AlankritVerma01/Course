"""
Functions for creating pre/postrequisite tree objects
"""

### Prerequisite Tree
def create_course_prereq_tree(db, course):
    """Returns adjacency tree containing partial prerequisites originating from course

    Return Schema:
    [
        {
            course id: [list of connected courses]
        }
    ]
    """
    tree = dict()

    # Traverse tree with queue and storing visited courses in tree
    queue = {course}
    while queue:
        curr = queue.pop()
        tree[curr] = db.get_prereq_courses(curr)
        queue.update([prereq for prereq in tree[curr] if prereq not in tree.keys()])
    return tree

def create_prereq_tree(db, courses):
    """Returns adjacency tree containing partial prerequisites originating from courses

    Return Schema:
    [
        {
            course id: [list of connected courses]
        }
    ]
    """
    tree = dict()

    # Take union of prerequisite trees of courses
    for course in courses:
        # If course is already added, then its prerequisite tree is also already in the tree
        if course not in tree.keys():
            tree.update(create_course_prereq_tree(db, course))
    return tree

### Postrequisite Tree
def create_course_postreq_tree(db, course):
    """Returns adjacency tree containing partial postrequisites originating from course

    Return Schema:
    [
        {
            course id: [list of connected courses]
        }
    ]
    """
    tree = dict()

    # Traverse tree with queue and storing visited courses in tree
    queue = {course}
    while queue:
        curr = queue.pop()
        tree[curr] = db.get_postreq_courses(curr)
        queue.update([postreq for postreq in tree[curr] if postreq not in tree.keys()])
    return tree

def create_partial_postreq_tree(db, courses):
    """Returns adjacency tree containing partial postrequisites originating from courses

    Return Schema:
    [
        {
            course id: [list of connected courses]
        }
    ]
    """
    tree = dict()

    # Take union of postrequisite trees of courses
    for course in courses:
        # If course is already added, then its postrequisite tree is also already in the tree
        if course not in tree.keys():
            tree.update(create_course_postreq_tree(db, course))
    return tree

def check_prereqs_satisfied(course_list, prereqs):
    """Returns whether prerequisites are satisfied given list of courses"""
    if prereqs is None:
        return True
    if type(prereqs) == str:
        return prereqs in course_list
    # Otherwise, prereqs is dict
    if prereqs['op'] == 'or':
        return any(check_prereqs_satisfied(course_list, prereq) for prereq in prereqs['args'])
    elif prereqs['op'] == 'and':
        return all(check_prereqs_satisfied(course_list, prereq) for prereq in prereqs['args'])

def create_complete_postreq_tree(db, primary, secondary):
    """Returns adjacency tree containing complete postrequisites of primary courses satisfied from secondary courses

    Return Schema:
    [
        {
            course id: [list of connected courses]
        }
    ]
    """
    # Get all possible courses that could appear in complete prerequisite tree
    course_pool = create_partial_postreq_tree(db, primary)
    # Begin tree with parameter courses already added
    tree = {course: course_pool[course] for course in primary}
    tree.update({course: db.get_postreq_courses(course) for course in secondary})

    # Repeatedly iterate over course_list until tree doesn't change for entire loop
    changed = True
    while changed:
        changed = False
        for course, prereq_courses in course_pool.items():
            if course not in tree.keys():
                # Check if prerequisites of course satisfied with courses in tree
                prereqs = db.get_course_prereqs(course)
                if check_prereqs_satisfied(tree.keys(), prereqs):
                    tree[course] = prereq_courses
                    changed = True
    return tree
