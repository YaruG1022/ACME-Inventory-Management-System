function generateNavbar(navbar_entries) {
    const currentPath = window.location.pathname.split('/').pop();
    
    return `
      <div class="topnav">
          ${navbar_entries.map(item => `
            <a href="${item.path}" class="${currentPath === item.path ? 'active' : ''}" ${item.style ? `style="${item.style}"` : ''} ${item.title ? `title="${item.title}"` : ''} ${item.id ? `id="${item.id}"` : ''}>
                ${item.icon ? `<i class="${item.icon}"></i>` : ''} ${item.img ? `<div class="topnav-pfp"><img src="${item.img}"></div>` : '' }  ${item.name}
            </a>
          `).join('')}
          <div class="search-container" style="float: left;">
              <form action="/action_page.php">
                  <input type="text" placeholder="Search.." name="search">
                  <button type="submit"><i class="fa fa-search"></i></button>
              </form>
          </div>
      </div>

      
    `;
}

function checkGET(param = '') {
  if (new URLSearchParams(window.location.search).get(param) != null)
      return true
  return false
}

/* function that opens a modal based on id */
function openModal(modal_id)
{
    var modal_elm = document.getElementById(modal_id);
    modal_elm.style.display = "block";
}

/* function that closes a modal based on id */
function closeModal(modal_id)
{
    var modal_elm = document.getElementById(modal_id);
    modal_elm.style.display = "none";
}


document.addEventListener('DOMContentLoaded', (event) => {
    //document.getElementById('navbar').innerHTML = generateNavbar();

    // Get the modals
    var loginModal = document.getElementById("loginModal");
    var signupModal = document.getElementById("signupModal");

    // Get the buttons that open the modals
    var loginBtn = document.getElementById("loginBtn");

    // Get the <span> elements that close the modals
    var closeButtons = document.getElementsByClassName("close");

    // Get the sign up link
    var signupLink = document.getElementById("signupLink");

    // When the user clicks the login button, open the login modal
    if(loginBtn) {
      loginBtn.onclick = function() {
        loginModal.style.display = "block";
      }
    }
    

    // When the user clicks on <span> (x), close the modal
    for (var i = 0; i < closeButtons.length; i++) {
        closeButtons[i].onclick = function() {
            loginModal.style.display = "none";
            signupModal.style.display = "none";
        }
    }

    // When the user clicks on the sign-up link, open the sign-up modal and close the login modal
    signupLink.onclick = function(event) {
      event.preventDefault();
      loginModal.style.display = "none";
      signupModal.style.display = "block";
    }

    // When the user clicks anywhere outside of the modals, close them
    window.onclick = function(event) {
      if (event.target == loginModal) {
        loginModal.style.display = "none";
        loginModal.getElementsByClassName("warning")[0].innerHTML = "";
        signupModal.getElementsByClassName("warning")[0].innerHTML = "";
      } else if (event.target == signupModal) {
        signupModal.style.display = "none";
        loginModal.getElementsByClassName("warning")[0].innerHTML = "";
        signupModal.getElementsByClassName("warning")[0].innerHTML = "";
      }
    }

    if(checkGET('next')) {
      redir_location = new URLSearchParams(window.location.search).get("next");
      redirs = document.getElementsByClassName("redir")
      for(i = 0; i < redirs.length; i++){
          redirs[i].setAttribute("value", redir_location);
      }
    }

    if(checkGET('login'))
    {
        openModal("loginModal");
    }
    if(checkGET('signup'))
    {
        openModal("signupModal");
    }
});
