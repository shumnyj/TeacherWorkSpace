function popup_show() {
  var popup = document.getElementById("NotifCont");
  popup.classList.toggle("show");
  }

function rm_notification(x) {
    y = x.parentElement.parentElement.parentElement;
    x = x.parentElement.parentElement
    // x.style.display = "none";
    y.removeChild(x)
    if (y.children.length == 0) {
        y.parentElement.style.display = "none"
    }
}

function delete_confirm(text, link) {
    res = confirm("Are you sure you want to delete this " + text + "?")
    if (res == true)
        window.location.href = link;
}