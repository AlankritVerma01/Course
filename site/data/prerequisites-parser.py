# Parses prerequisites from course information file into json file

import pyparsing as pp
import json

# pp.ParserElement.enablePackrat()

INPUT_FILENAME = 'courses.json'
OUTPUT_FILENAME = 'prerequisites.json'

def get_courses(input_filename):
    with open(input_filename, 'r') as file:
        courses = json.load(file)
    return courses

def parse_prerequisites(prereq_str):
    # Parses prereq_str and returns prerequistes in dictionary or as string. Returns original string if unsuccessfully parsed
    """
    Prerequisite Expression Schemas:
    COURSE CODE,
    {
        'op': "and"/"or",
        'args': [
            PREREQUISITE_EXPRESSIONS
        ]
    }
    """
    ### Preprocessing
    # Replace useless text
    prereq_str = prereq_str.replace("14.0 credits and enrolment in a Computer Science Subject POSt. Restricted to students in the Specialist/Specialist Co-op programs in Computer Science or in the Specialist/Specialist Co-op programs in Management and Information Technology", '')
    prereq_str = prereq_str.replace("A minimum of 2.5 credits at the B-level or higher in CSC courses", '')
    prereq_str = prereq_str.replace("Normally intended for students who have completed at least 8 credits.", '')
    prereq_str = prereq_str.replace("Students must obtain consent from the Supervisor of Studies before registering for this course.", '')
    prereq_str = prereq_str.replace("Enrolment procedures: Project supervisor's note of agreement must be presented to the Supervisor of Studies, who must issue permission for registration.", '')
    prereq_str = prereq_str.replace("10.0 credits, including 2.0 credits in MAT courses [excluding MATA02H3], of which 0.5 credit must be at the B-level", '')
    prereq_str = prereq_str.replace("Permission of the instructor is required. Typically this will require that the student has completed courses such as ", '')
    prereq_str = prereq_str.replace("but the instructor may specify alternative course requirements", '')
    prereq_str = prereq_str.replace("with a grade of B+ or higher", '')
    prereq_str = prereq_str.replace("with grade of at least B+", '')
    prereq_str = prereq_str.replace("Students enrolled in the Minor program in Applied Statistics should take STAC53H3", '')
    # Replace slashes with or because pyparsing
    prereq_str = prereq_str.replace('/', ' or ')
    # Replace double spaces
    prereq_str = prereq_str.replace('  ', ' ')
    # Strip leading periods
    prereq_str = prereq_str.strip('. ')

    # Empty string edgecase
    if prereq_str == '':
        return None

    ### Expression Keywords
    # Operators
    AND = pp.Keyword('and')
    OR = pp.Keyword('or')

    # UTSC Course Code
    COURSE_CODE = pp.Regex("\\(?[A-Z]{4}[0-9]{2}H3\.?\\)?")
    # Other campus course codes
    COURSE_CODE_EXTERN = pp.Regex("\\(?[A-Z]{3}[0-9]{3}(?:(?:H[13]?)|Y)\.?\\)?")
    # Grade 12 Courses
    COURSE_GRADE_12 = pp.Literal("Grade 12 Calculus and Vectors") | pp.Literal("one other Grade 12 mathematics course") | pp.Literal("Grade 12 Advanced Functions and Introductory Calculus and Geometry and Discrete Mathematics")
    # Program requirements
    OTHER_REQ = pp.Literal("proficiency in C") | pp.Literal("Some experience with programming in an imperative language such as Python, Java or C") | pp.Literal("Three C-level CSC courses") | pp.Literal("at least one other B-level course in Mathematics or Computer Science") | pp.Literal("1.5 credits at the C-level in MAT courses")
    CREDITS_REQ = pp.Regex("[0-9]+.[0-9]+ [Cc]redits?")
    CGPA_REQ = pp.Regex("(?:a )?CGPA (?:of (?:at least )?)?[0-9].[0-9],?")
    SUBJECT_ENROLLMENT_REQ = pp.Regex("enrolment in a (?:(?:CSC)|(?:Computer Science)|(?:Mathematics)) [Ss]ubject POSt,?")
    NON_SUBJECT_ENROLLMENT_REQ = pp.Regex("enrolment in a non-CSC Subject PO[Ss]t for which this specific course is a program requirement,?")
    PROGRAM_REQ = OTHER_REQ | CREDITS_REQ | CGPA_REQ | SUBJECT_ENROLLMENT_REQ | NON_SUBJECT_ENROLLMENT_REQ
    # Everything before a list of prerequisites
    PREAMBLE = pp.Regex(".*:") | pp.Regex("including,?")
    # Permission to take course
    PERMISSION = pp.Literal("Students must obtain consent from the Supervisor of Studies before registering for this course.") | pp.Literal("Permission of the instructor") | pp.Literal("permission of the Supervisor of Studies")

    ### Actions to create prerequisite dictionary and replace unneeded prerequisites with empty strings
    COURSE_CODE.set_parse_action(lambda m: m[0].strip('(). '))
    COURSE_CODE_EXTERN.set_parse_action(lambda _: '')
    COURSE_GRADE_12.set_parse_action(lambda _: '')
    PROGRAM_REQ.set_parse_action(lambda _: '')
    PREAMBLE.set_parse_action(lambda _: '')
    PERMISSION.set_parse_action(lambda _: '')

    operand = COURSE_CODE | COURSE_CODE_EXTERN | COURSE_GRADE_12 | PROGRAM_REQ | PERMISSION
    #operand.set_parse_action(code).set_name("operand")
    expression = pp.infix_notation(
        operand,
        [
            (AND, 2, pp.opAssoc.LEFT, lambda m: {'op': 'and', 'args': m[0][0::2]}),
            (OR, 2, pp.opAssoc.LEFT, lambda m: {'op': 'or', 'args': m[0][0::2]}),
            (PREAMBLE, 1, pp.opAssoc.RIGHT, lambda m: m[0][1])
        ],
        lpar='[',
        rpar=']'
    ).set_name("boolean expression")
    return reduce_prerequisite_dict(expression.parse_string(prereq_str, parse_all=True)[0])

def reduce_prerequisite_dict(prereqs):
    # Recursively remove empty strings and redundant operators from prerequisite dictionary
    if type(prereqs) == str:
        return prereqs if prereqs != '' else None
    # Apply function to list
    prereqs['args'] = [reduce_prerequisite_dict(arg) for arg in prereqs['args']]

    # Reduce list
    prereqs['args'] = [arg for arg in prereqs['args'] if arg is not None]
    if len(prereqs['args']) == 0:
        return None
    elif len(prereqs['args']) == 1:
        return prereqs['args'][0]
    return prereqs

def parse_prereqs(courses):
    # Returns dictionary of prerequisites for each course in courses
    # Schema: { 'code': COURSE CODE, 'prereqs': PREREQUISITE EXPRESSION }
    prereqs = []
    for course in courses:
        prereq_str = course['fields'].get('Prerequisite', '')
        prereqs.append({'code': course['code'], 'prereqs': parse_prerequisites(prereq_str)})
    return prereqs

def main():
    # Only parse CMS courses because otherwise this will take one month to finish
    courses = [course for course in get_courses(INPUT_FILENAME) if course['code'][:3] in ['MAT', 'CSC', 'STA']]
    prereqs = parse_prereqs(courses)
    with open(OUTPUT_FILENAME, 'w') as file:
        json.dump(prereqs, file)

    ### TESTING
    #print(parse_prerequisites("MATA22H3/MATA31H3"))
    """
    courses = [course for course in get_courses(INPUT_FILENAME) if course['code'][:3] in ['MAT', 'CSC', 'STA']]
    #courses = get_courses(INPUT_FILENAME)
    count = 0
    for course in courses:
        try:
            prereq_str = course['fields'].get('Prerequisite')
            if prereq_str is not None:
               prereqs = parse_prerequisites(prereq_str)
               print(f"{course['code']} - {prereqs}")
        except pp.ParseException as e:
            #if ':' in prereq_str:
            count += 1
            print(f"Could not parse {course['code']} - Prerequisites: {prereq_str}")
            print(e)
    print(f"Total unparsed: {count}/{len(courses)}")
    """

if __name__ == '__main__':
    main()
