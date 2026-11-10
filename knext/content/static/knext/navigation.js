"use strict";
const appMenu = document.querySelector(".knext-menu");
if (appMenu) {
    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && appMenu.open) {
            appMenu.open = false;
            appMenu.querySelector("summary").focus();
        }
    });
    document.addEventListener("click", event => {
        if (!appMenu.contains(event.target)) appMenu.open = false;
    });
}
