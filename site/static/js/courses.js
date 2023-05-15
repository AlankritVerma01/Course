// Click listener for table rows
const coursesList = document.querySelectorAll("#courses-list .courses-list-row");
for (const course of coursesList) {
	course.addEventListener("click", () => window.location = course.dataset.courseLink);
}

// Courses Search Bar
const coursesSearchBar = document.querySelector("#search-bar-courses");

// Run function when key is pressed
coursesSearchBar.addEventListener("keyup", filterFactory(coursesList,
	// Filtering function
	courseElement => {
		const text = coursesSearchBar.value.toUpperCase();
		// Show all elements if search bar is empty
		if (!text) {
			return false;
		}
		const label = courseElement.querySelector(".courses-row-id");
		const courseCode = label.textContent || label.innerText;
		// Show element if search bar text appears anywhere in course code
		return courseCode.toUpperCase().indexOf(text) <= -1;
	},
	// Show element function
	courseElement => {
		courseElement.style.display = "";
	},
	// Hide element function
	courseElement => {
		courseElement.style.display = "none";
	}
));
