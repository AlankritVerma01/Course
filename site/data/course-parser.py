from bs4 import BeautifulSoup as Soup
import json

INPUT_FILENAME = "course-list.html"
OUTPUT_FILENAME = "courses.json"

def get_courses():
    # Returns list of elements containing course information
    with open(INPUT_FILENAME, 'r', encoding='utf-8') as f:
        document = Soup(f, 'html.parser')
    # Get element whose children contain information about each course
    courses = document.find(attrs={'class': 'view-content'})
    # Create list containing course elements
    return courses.find_all('div', recursive=False)

def get_course_info(element):
    """
    Retrieves course information from HTML element in a dictionary format

    Element Schema:
    <div class="no-break views-row">
        <div class="views-field views-field-field-course-title">
            <div class="field-content"><br />
                <h3>[COURSE CODE]: [COURSE NAME]</h3>
            </div>
        </div>
        <div class="views-field views-field-body">
            <div class="field-content">
                <p>[COURSE DESCRIPTION]</p>
            </div>
        </div>
        <span class="views-field views-field-field-[FIELD NAME]">
            <strong class="views-label views-label-field-[FIELD NAME]">[FIELD NAME]: </strong>
            <span class="field-content">[FIELD CONTENT]</span>
        </span>
        <br>
        [MORE SPAN ELEMENTS]
        <div class="views-field views-field-field-timetable-link">
            <div class="field-content">
                <div><a href="[LINK TO COURSE PAGE]">Link to UTSC Timetable</a></div>
            </div>
        </div>
    </div>

    Return Schema:
    {
        'code': Course code,
        'name': Name of course,
        'description': Short description of course,
        'link': Link to course on uoft website,
        'fields': {
            'field': Additional information about course listed with course information
                     Possible fields are: 'Enrolment Limits', 'Recommended Preparation', 'Exclusion', 'Corequisite', 'Course Experience', 'Prerequisite', 'Breadth Requirements', 'Note'
        }
    }
    """
    info = dict()

    # Add information stored in div elements
    divs = element.find_all('div', recursive=False)
    info['code'] = divs[0].div.h3.string[:8]
    info['name'] = divs[0].div.h3.string
    info['description'] = ''.join(divs[1].strings)
    info['link'] = divs[2].div.a['href']

    # Add fields stored in span elements
    info['fields'] = dict()
    for span in element.find_all('span', recursive=False):
        field_name = span.strong.string[:-2]
        info['fields'][field_name] = ''.join(span.span.strings)

    return info

def main():
    courses = get_courses()
    courses_info = [get_course_info(course) for course in courses]
    with open(OUTPUT_FILENAME, 'w') as file:
        json.dump(courses_info, file)

if __name__ == "__main__":
    main()