// Function that returns function for filtering list of elements basesd on filter function
function filterFactory(elements, filterFunc, showFunc, hideFunc) {
	return () => {
		for (const element of elements) {
			// Hide element if it should be filtered, otherwise, show element
			if (filterFunc(element)) {
				hideFunc(element);
			}
			else {
				showFunc(element);
			}
		}
	}
}
