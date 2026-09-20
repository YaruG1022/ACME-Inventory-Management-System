function openMenu(menuId) {
    // Hide all content
    var contents = document.getElementsByClassName('menu-content');
    for (var i = 0; i < contents.length; i++) {
        contents[i].style.display = 'none';
    }

    // Show the selected content
    document.getElementById(menuId).style.display = 'block';
}

window.onload = function() {
    openMenu('whatsNew');
}
