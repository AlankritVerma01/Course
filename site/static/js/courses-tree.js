// Enable button tooltips
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
	return new bootstrap.Tooltip(tooltipTriggerEl)
})

// Courses Search Bar
const coursesSearchBar = document.querySelector("#form-courses-search-bar");
const coursesList = document.querySelectorAll(".form-courses-check");

// Run function when key is pressed
coursesSearchBar.addEventListener("keyup", filterFactory(coursesList,
	// Filtering function
	courseElement => {
		const text = coursesSearchBar.value.toUpperCase();
		// Show all elements if search bar is empty
		if (!text) {
			return false;
		}
		const label = courseElement.querySelector("label");
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

// Selected Clear Button
const coursesClearButton = document.querySelector("#form-courses-clear");
coursesClearButton.addEventListener("click", () => {
	// Show every element
	for (courseElement of coursesList) {
		courseElement.querySelector("input").checked = false;
	}
});
