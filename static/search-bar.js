function searchBook() {
    let input, filter, buttons, i, txtValue
    input = document.getElementById("search_input")
    filter = input.value.toUpperCase()
    buttons = document.getElementsByTagName("button")
    for (i = 0; i < buttons.length; i++) {
        txtValue = buttons[i].textContent || buttons[i].innerText
        if (txtValue.toUpperCase().indexOf(filter) > -1) {
            buttons[i].style.display = ""
        } else {
            buttons[i].style.display = "none"
        }
    }
}