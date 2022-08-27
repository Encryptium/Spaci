const doneButtons = document.querySelectorAll("#tasks div img");
const tasks = document.querySelector("#tasks");

for (let i = 0; i < doneButtons.length; i++) {
	doneButtons[i].addEventListener('click', e => {
		fetch('/api/v1/complete-task?task_index=' + i.toString())
			.then(res => res.json())
			.then((data) => {
				if (data.success) {
					e.target.parentElement.remove();
				} else {
					location.reload();
				}
			});
	});
}

const newTaskFormElement = document.getElementById("new-task");

newTaskFormElement.addEventListener('submit', e => {
	e.preventDefault();
	
	var newTaskFormData = new FormData(newTaskFormElement);
	fetch('/api/v1/add-task', {
		method: 'POST',
		body: newTaskFormData
		}).then(function(response) {
			return response.json();
		}).then(function(data) {
			tasks.innerHTML += "<div><h2>" + document.querySelector("form#new-task input[name='title']").value + "</h2><p>" + document.querySelector("form#new-task input[name='description']").value + "</p><img style='cursor:not-allowed' src='/static/img/processing.svg' alt='Processing' title=\"While we are still processing this request, go grab a cup of coffee.\"></div>";
			newTaskFormElement.reset();
		});
});