const inviteField = document.querySelector('#invite form input');
const inviteButton = document.querySelector('#invite form input[type=\'submit\']');
const collaborators = document.querySelector('#collaborators');

inviteButton.addEventListener('click', function(e) {
    e.preventDefault();
    var invite = new FormData(document.querySelector('#invite form'));
    inviteField.value = inviteField.value.replace(/\s/g, '');
    if (inviteField.value.length > 0) {
        inviteButton.disabled = true;
        inviteButton.value = 'Inviting...';
        inviteField.disabled = true;
        fetch('/api/v1/invite', {
        method: 'POST',
        body: invite
        }).then(function(response) {
            return response.json();
        }).then(function(data) {
            inviteButton.disabled = false;
            inviteButton.value = 'Invite';
            inviteField.disabled = false;
            if (data.success) {
                collaborators.innerHTML += `<div><p>${inviteField.value}</p><img src="/static/img/close.svg" alt="Remove this collaborator"></div>`;
            }
            inviteField.value = '';
        });
    }
});

const removeCollaboratorBtn = document.querySelectorAll('#collaborators div img');

for (var i = 0; i < removeCollaboratorBtn.length; i++) {
    removeCollaboratorBtn[i].addEventListener('click', function(e) {
        e.preventDefault();
        const collaborator = this.parentNode;
        const collaboratorId = collaborator.querySelector('p').innerHTML;
        fetch('/api/v1/remove-collaborator', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                collaboratorId: collaboratorId
            })
        }).then(function(response) {
            return response.json();
        }).then(function(data) {
            if (data.success) {
                collaborator.remove();
            }
        });
    } );
}