const deleteButton = document.getElementById("delete-button");
const deleteInstructions = document.getElementById("delete-instructions");
const deleteCode = document.querySelector("#description > p:nth-child(1) > code:nth-child(1)").innerHTML;
const deleteInput = document.getElementById("delete-input");

deleteButton.addEventListener('click', e => {
	e.preventDefault();
	console.log("i");
	deleteInstructions.style.display = 'block';
});

deleteInstructions.addEventListener('submit', e => {
	e.preventDefault();
	if (deleteInput.value == deleteCode) {
		window.location.href = "/delete-workspace?workspace_id=" + workspaceID;
	} else {
		console.log("failed");
	}
});