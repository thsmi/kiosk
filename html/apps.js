const SEVEN_SECONDS = 7*1000;

class ScheduleDialog {

    /**
     * Shows the schedule dialog an waits until the user either accepts or dismisses it.
     * @returns {boolean}
     *   true in case the dialog was accepted otherwise false if the user canceled it.
     */
    async show() {
        return new Promise((resolve) => {

            const elm = document.getElementById('kiosk-schedule-dialog');
            const modal = new bootstrap.Modal(elm);
    
            function onSaveClick() {
                document
                    .getElementById('kiosk-schedule-update')
                    .removeEventListener('click', onSaveClick);
                document
                    .getElementById('kiosk-schedule-dialog')
                    .removeEventListener('hidden.bs.modal', onModalClose);
    
                modal.hide();
    
                resolve(true);
            }
    
    
            function onModalClose() {
                document
                    .getElementById('kiosk-schedule-update')
                    .removeEventListener('click', onSaveClick);
                document
                    .getElementById('kiosk-schedule-dialog')
                    .removeEventListener('hidden.bs.modal', onModalClose);
    
                resolve(false);
            }
    
            // Attach event listeners
            document
                .getElementById('kiosk-schedule-update')        
                .addEventListener('click', onSaveClick);
            document
                .getElementById('kiosk-schedule-dialog')
                .addEventListener('hidden.bs.modal', onModalClose);
    
            // Show the modal
            modal.show();
        });
            
    
    }

    setWeekday(weekday) {
        document.getElementById("kiosk-schedule-weekday-monday").checked = false;
        document.getElementById("kiosk-schedule-weekday-tuesday").checked = false;
        document.getElementById("kiosk-schedule-weekday-wednesday").checked = false;
        document.getElementById("kiosk-schedule-weekday-thursday").checked = false;
        document.getElementById("kiosk-schedule-weekday-friday").checked = false;
        document.getElementById("kiosk-schedule-weekday-saturday").checked = false;
        document.getElementById("kiosk-schedule-weekday-sunday").checked = false;
    
        for (const item of weekday.split(",")) {
            if (item === "1")
                document.getElementById("kiosk-schedule-weekday-monday").checked = true;
            if (item === "2")
                document.getElementById("kiosk-schedule-weekday-tuesday").checked = true;
            if (item === "3")
                document.getElementById("kiosk-schedule-weekday-wednesday").checked = true;
            if (item === "4")
                document.getElementById("kiosk-schedule-weekday-thursday").checked = true;
            if (item === "5")
                document.getElementById("kiosk-schedule-weekday-friday").checked = true;
            if (item === "6")
                document.getElementById("kiosk-schedule-weekday-saturday").checked = true;
            if (item === "0")
                document.getElementById("kiosk-schedule-weekday-sunday").checked = true;
    
            if (item === "*") {
                document.getElementById("kiosk-schedule-weekday-monday").checked = true;
                document.getElementById("kiosk-schedule-weekday-tuesday").checked = true;
                document.getElementById("kiosk-schedule-weekday-wednesday").checked = true;
                document.getElementById("kiosk-schedule-weekday-thursday").checked = true;
                document.getElementById("kiosk-schedule-weekday-friday").checked = true;
                document.getElementById("kiosk-schedule-weekday-saturday").checked = true;
                document.getElementById("kiosk-schedule-weekday-sunday").checked = true;            
            }
    
        }
    }

    getWeekday() {
        const result = []

        if (document.getElementById("kiosk-schedule-weekday-sunday").checked)
            result.push("0")             
        if (document.getElementById("kiosk-schedule-weekday-monday").checked)
            result.push("1")
        if (document.getElementById("kiosk-schedule-weekday-tuesday").checked)
            result.push("2")
        if (document.getElementById("kiosk-schedule-weekday-wednesday").checked)
            result.push("3")
        if (document.getElementById("kiosk-schedule-weekday-thursday").checked)
            result.push("4")
        if (document.getElementById("kiosk-schedule-weekday-friday").checked)
            result.push("5")
        if (document.getElementById("kiosk-schedule-weekday-saturday").checked)
            result.push("6")                
    
    
        if (result.length === 7)
            return "*";
        if (result.length === 0)
            return "*";
    
        return result.join(",");
    }

    getItem(name) {
        if (document.getElementById(`kiosk-schedule-${name}-all`).checked)
            return "*";
        
        return document.getElementById(`kiosk-schedule-${name}-list`).value;
    }

    setItem(name, value) {
        if (value === "*") {
            document.getElementById(`kiosk-schedule-${name}-all`).checked = true;
            document.getElementById(`kiosk-schedule-${name}-list`).value = "";
            return;
        }
        
        document.getElementById(`kiosk-schedule-${name}-some`).checked = true;
        document.getElementById(`kiosk-schedule-${name}-list`).value = value;    
    }

    setHour(hour) {
        this.setItem("hour", hour);
    }

    setMinute(minute) {
        this.setItem("minute", minute);
    }

    setDay(day) {
        this.setItem("day", day);
    }

    setMonth(month) {
        this.setItem("month", month);
    }

    getHour() {
        return this.getItem("hour");
    }

    getMinute() {
        return this.getItem("minute");
    }

    getDay() {
        return this.getItem("day");
    }

    getMonth() {
        return this.getItem("month");
    }

    getAction() {
        return document.getElementById("kiosk-schedule-action").value;
    }

    setAction(value) {
        document.getElementById("kiosk-schedule-action").value = value;
    }

}

async function getJson(url) {
    return await (await fetch(url)).json();
}

async function postJson(url, data) {
    data = JSON.stringify(data);

    const response = await fetch(url, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: data
    });

    // We reload in case the authentication failed.
    if (response.status === 401)
        location.reload();

    return response;
}

async function postFormData(url, data) {
    const response = await fetch(url, {
        method: 'POST',
        body: data
    });

    // We reload in case the authentication failed.
    if (response.status === 401)
        location.reload();

    return response;
}

async function delay(ms) {
    return new Promise((resolve)=> {
        setTimeout(() => { resolve() }, ms)
    });
}

async function animatedBtnProgressHandler(id, callback) {
    const spinner = document.createElement('div');
    spinner.className = "spinner-border spinner-border-sm mx-1";
    spinner.setAttribute('role', 'status');

    const button = document.getElementById(id)
    button.disabled = true;
    button.prepend(spinner)

    try {
        await callback();
    } finally {
        button.querySelector(".spinner-border").remove()
        button.disabled = false;
    }
}

async function addProgressEventHandler(id, callback) {
    
    const elm = document.getElementById(id);

    if (elm === null)
        throw new Error(`No element with id ${id} found`);

    elm.addEventListener("click", () => {
        animatedBtnProgressHandler(id, callback);
    });
}

async function loadScreenshot(ms) {
    
    document.getElementById("kiosk-screenshot-loading").classList.remove("d-none");

    if (typeof(ms) !== "undefined" && ms !== null)
        await delay(ms);


    const timestamp = new Date().getTime(); 
    const random = Math.random().toString(36).substring(2, 15); 

    const img = document.getElementById("kiosk-screenshot");
    img.src = `./screen/screenshot.png?${timestamp}-${random}`; 

    img.addEventListener("load", () => {
        document.getElementById("kiosk-screenshot-loading").classList.add("d-none");
    }, { once: true });
}

async function loadScreen() {

    const screen = await getJson("/screen");

    document.getElementById("kiosk-orientation").value = screen.dimensions.orientation;
    document.getElementById("kiosk-resolution").value = `${screen.dimensions.x}x${screen.dimensions.y}`
    document.getElementById("kiosk-website").value = screen.url;
    document.getElementById("kiosk-scale").value = (screen.scale * 100);
}

async function saveScreen() {

    // Schedule a screenshot in 10 sec, chrome starts very slow...
    loadScreenshot(SEVEN_SECONDS);   

    const data = {
        url : document.getElementById("kiosk-website").value,
        orientation : document.getElementById("kiosk-orientation").value,
        scale : parseFloat(document.getElementById("kiosk-scale").value) / 100
    };

    const response = await postJson("/screen", data);

    if (!response.ok)
        throw new Error(`An error occurred while updating screen.`);

    await loadScreen();
}

async function authenticate() {
    if (await isAuthenticated()) {
        document.getElementById("kiosk-content").classList.remove("d-none")
        populate()
        return;
    }

    const passwordModal = new bootstrap.Modal(document.getElementById('kiosk-login-modal'));
    passwordModal.show();
}

async function isAuthenticated() {
    const response = await fetch("login")

    if (!response.ok)
        return false

    return (await (response.json())).authenticated;
}

async function login() {
    const password = document.getElementById('kiosk-login-password').value;

    const response = await fetch("login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({password: password})
    });

    if (!response.ok) {
        alert("Failed to login");
        return;
    }

    // Close the modal
    bootstrap.Modal.getInstance(document.getElementById('kiosk-login-modal')).hide();

    document.getElementById("kiosk-content").classList.remove("d-none")
    populate()
};

/**
 * Saves the current password.
 */
async function savePassword() {

    const password = document.getElementById('kiosk-new-password').value;
    const confirmation = document.getElementById('kiosk-new-password-confirm').value;

    if (password !== confirmation) {
        alert("Password does not match");
        return;
    }

    const response = await postJson("password", { password: password });

    if (!response.ok) {
        alert("Updating password failed")
        throw new Error(`An error occurred while updating password.`);
    }
}


async function logout() {
    await fetch("logout");
    location.reload();
}

/**
 * Generates a new password.
 */
async function generateCert() {

    const response = await postJson("cert/generate", {});

    if (!response.ok) {
        alert("Failed to generate certificate");
    }
}

async function uploadCert() {
    const data = new FormData();
    pfx = document.getElementById('kiosk-cert-pfx').files[0];

    if (typeof(pfx) === "undefined") {
        alert("No pfx file specified");
        return;
    }

    data.append('pfx', pfx);
    data.append("password", document.getElementById('kiosk-cert-password').value);

    const response = await postFormData('/cert', data);

    if (response.status === 401)
        location.reload();

    if (!response.ok)
        alert("Failed to upload certificate");
}


function convertSchedule(minute, hour, day, month, weekday, action) {
    
    let description = ""

    if (action === "off")
        description += "Turn off screen "
    else if (action === "on")
        description += "Turn on scree ";
    else if (action === "reboot")
        description += "Restart and turn on screen ";
    else 
       description = "Run unknown action "

    if (hour === "*")
        description += "every hour";
    else
        description += "on hours "+hour;

    if (minute === "*")
        description += ", every minute";
    else
        description += ", on minutes "+minute;

    if (day !== "*")
        description += ", on days "+day;

    if (month !== "*")
        description += ", on months "+month;

    if (weekday !== "*") {
        description += ", only on  "

        weekday = weekday.split(",")
        const items = [];
        for (item of weekday) {
            
            if (item == "0")
                items.push("Sundays");
            if (item == "1")
                items.push("Mondays");
            if (item == "2")
                items.push("Tuesdays");
            if (item == "3")
                items.push("Wednesdays");
            if (item == "4")
                items.push("Thursdays");
            if (item == "5")
                items.push("Fridays");
            if (item == "6")
                items.push("Saturday");
        }

        description += items.join(", ");
    }

    return description;
}


async function editSchedule(elm) {
    const dialog = new ScheduleDialog();

    dialog.setMinute(elm.querySelector(".kiosk-schedule-minute").textContent);
    dialog.setHour(elm.querySelector(".kiosk-schedule-hour").textContent);
    dialog.setDay(elm.querySelector(".kiosk-schedule-day").textContent);
    dialog.setMonth(elm.querySelector(".kiosk-schedule-month").textContent);
    dialog.setWeekday(elm.querySelector(".kiosk-schedule-weekday").textContent);
    dialog.setAction(elm.querySelector(".kiosk-schedule-action").textContent);

    if (!await dialog.show())
        return;

    const minute = dialog.getMinute()
    const hour = dialog.getHour()
    const day = dialog.getDay()
    const month = dialog.getMonth()
    const weekday = dialog.getWeekday()
    const action = dialog.getAction()

    elm.querySelector(".kiosk-schedule-minute").textContent = minute;
    elm.querySelector(".kiosk-schedule-hour").textContent = hour;
    elm.querySelector(".kiosk-schedule-day").textContent = day;
    elm.querySelector(".kiosk-schedule-month").textContent = month;
    elm.querySelector(".kiosk-schedule-weekday").textContent = weekday;
    elm.querySelector(".kiosk-schedule-action").textContent = action;

    elm.querySelector(".kiosk-schedule-description").textContent 
        = convertSchedule(minute, hour, day, month, weekday, action);
}

async function newSchedule() {
    const dialog = new ScheduleDialog();

    dialog.setMinute("0");
    dialog.setHour("2");
    dialog.setDay("*");
    dialog.setMonth("*");
    dialog.setWeekday("*");
    dialog.setAction("off");

    if (!await dialog.show())
        return;    

    addSchedule(
        dialog.getMinute(),
        dialog.getHour(),
        dialog.getDay(),
        dialog.getMonth(),
        dialog.getWeekday(),
        dialog.getAction());
}

async function addSchedule(minute, hour, day, month, weekday, action) {

    const elm = document.getElementById("kiosk-schedule-template").content.cloneNode(true);
    
    elm.querySelector(".kiosk-schedule-action").textContent = action;
    elm.querySelector(".kiosk-schedule-minute").textContent = minute;
    elm.querySelector(".kiosk-schedule-hour").textContent = hour;
    elm.querySelector(".kiosk-schedule-day").textContent = day;
    elm.querySelector(".kiosk-schedule-month").textContent = month;
    elm.querySelector(".kiosk-schedule-weekday").textContent = weekday;

    elm.querySelector(".kiosk-schedule-description").textContent 
        = convertSchedule(minute, hour, day, month, weekday, action);

    const id = "kiosk-"
        + Math.random().toString(36).substring(2, 8).toUpperCase()
        + Date.now().toString(16).toUpperCase();

    elm.firstElementChild.id = id;

    document.getElementById("kiosk-schedule").appendChild(elm);

    document.querySelector(`#${id} .kiosk-schedule-edit`).addEventListener("click", () => {
        editSchedule(document.getElementById(id));
    });
    document.querySelector(`#${id} .kiosk-schedule-delete`).addEventListener("click", () => {
        document.getElementById(id).remove();
    });
}

async function loadSchedule() {
    const schedule = await getJson("/schedule");

    for (const item of schedule) 
        addSchedule(item.minute, item.hour, item.day, item.month, item.weekday, item.action);
}

async function saveSchedule() {
    const items = document.getElementById("kiosk-schedule").children;

    const schedule = [];

    for (const item of items) {
        schedule.push({
            "minute": item.querySelector(".kiosk-schedule-minute").textContent,
            "hour": item.querySelector(".kiosk-schedule-hour").textContent,
            "day" : item.querySelector(".kiosk-schedule-day").textContent,
            "month" : item.querySelector(".kiosk-schedule-month").textContent,
            "weekday" : item.querySelector(".kiosk-schedule-weekday").textContent,
            "action" : item.querySelector(".kiosk-schedule-action").textContent });
    }

    const response = await postJson("/schedule", schedule);

    if (!response.ok)
        throw new Error("Failed to update schedule.");
}

async function awaitReboot() {

    const modal = new bootstrap.Modal('#kiosk-rebooting-modal');
    modal.show();
    
    await delay(SEVEN_SECONDS);    

    for (let i=0; i<20; i++) {        
        try {

            const response = await fetch("status");
        
            if (response.ok) {
                modal.hide();            
                return;
            }
        }
        catch (ex) {
            // Ignore error...
        }

        await delay(SEVEN_SECONDS);
    }    

    throw new Error("Failed to restart system");
}

async function reboot() {
    await fetch("/reboot");
    await awaitReboot();
}

/**
 * Loads the system specific settings
 */
async function loadSystem() {
    document.getElementById("kiosk-ssh-status").checked
         = (await getJson("ssh")).active;
    document.getElementById("kiosk-hostname").value 
        = (await getJson("hostname")).hostname;
}

async function populate() {
    loadScreenshot();
    loadScreen();
    loadSchedule();
    loadSystem();

    addProgressEventHandler("kiosk-screen-save", async() => {
        await saveScreen();
    });

    addProgressEventHandler('kiosk-screen-on', async() => {
        await fetch("/screen/on");
        await loadScreenshot();
    });

    addProgressEventHandler('kiosk-screen-off', async() => {
        await fetch("/screen/off");
        await loadScreenshot();
    });        

    document.getElementById("kiosk-screenshot").addEventListener("click", () => {
        loadScreenshot();
    });

    document.getElementById("kiosk-screenshot-reload").addEventListener("click", () => {
        loadScreenshot();
    })

    addProgressEventHandler('kiosk-password-save', async() => {
        await savePassword();        
    });

    addProgressEventHandler("kiosk-cert-generate", async () => {
        await generateCert();
    });

    addProgressEventHandler("kiosk-cert-upload", async () => {
        await uploadCert()
    });

    document.getElementById("kiosk-schedule-add").addEventListener("click", async () => {
        newSchedule();
    });

    addProgressEventHandler("kiosk-schedule-save", async() => {
        await saveSchedule();
    });

    addProgressEventHandler("kiosk-reboot", async() => {
        await reboot();
    });

    addProgressEventHandler("kiosk-ssh-save", async() => {

        if (!document.getElementById("kiosk-ssh-status").checked)
            await fetch("ssh/disable");
        else 
            await fetch("ssh/enable");

        await awaitReboot();
    });

    addProgressEventHandler("kiosk-hostname-update", async() => {
        const value = document.getElementById("kiosk-hostname").value;
        await postJson("hostname", { hostname: value});

        await awaitReboot();
    });
}


// Fetch and populate configurations when the page loads
window.onload = async function() {

    document.getElementById("kiosk-login-password").addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            document.getElementById('kiosk-login-button').click()
        }
    });

    // Wire the event listeners
    document.getElementById('kiosk-login-button').addEventListener('click', async () => {
        await login();
    });
    document.getElementById('kiosk-logout-button').addEventListener('click', async () => {
        await logout();
    });


    authenticate();
};
