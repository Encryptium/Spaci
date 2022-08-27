const sideNav = document.getElementById("sidenav");
const sideNavLinks = document.querySelectorAll("#sidenav a");

// Remove sidebar when link is clicked
for (let i = 0; i < sideNavLinks.length; i++) {
	sideNavLinks[i].addEventListener('click', e => {
		e.preventDefault();
		sideNav.style.animation = 'clear-sidenav 0.3s ease';
		
		setTimeout(() => {
            window.location.href = sideNavLinks[i].href;
		}, 300);
	});
}

const workspaceSelector = document.getElementById("workspace-selector");
const workspaceList = document.getElementById("workspace-list");
const workspaceSelectorClose = document.getElementById("back-btn");

// Hide and show the workspaces selector
workspaceSelector.addEventListener('click', e => {
	workspaceList.style.display = 'block';
});

workspaceSelectorClose.addEventListener('click', e => {
	workspaceList.style.display = 'none';
});

// Change background color of a link in side nav
// based on which page is on
const changeLinkColor = () => {
    const url = location.href;
    
    // Get last part of url
    const page = url.substr(url.lastIndexOf("/") + 1);

    // Adds .active to the link
    document.querySelector(`a[href=${page}]`).classList.add("active");
};

changeLinkColor();


