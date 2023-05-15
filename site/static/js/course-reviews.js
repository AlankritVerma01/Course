// Add event listener to update value of rating slider
const ratingElement = document.querySelector("#form-review-rating");
// Rating element might not be in document
if (ratingElement){
	ratingElement.addEventListener("input", ev => {
		// Update value based on slider value
		document.querySelector("#form-review-rating-value").innerText = `${ratingElement.value}/10`;
	});
}
