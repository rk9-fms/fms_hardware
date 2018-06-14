'use strict';

let storage_api_ip;
let storage_api_prefix = '/api/v1/';
let connected_with_web_hw_api = false;

let web_hw_api_ip_key = 'web_hw_api_ip';
let web_hw_api_element = document.getElementById('web_hw_api');
let input_text_arr = ["ip_sec_1", "ip_sec_2", "ip_sec_3", "ip_sec_4", "ip_port"];

function update_global_storage_api_ip(ip_arr) {
    storage_api_ip = 'http://' +
    [ip_arr.slice(0, 4).join('.'), ip_arr[4]].join(':') +
    storage_api_prefix;
    // console.log('Updating storage_api_ip: ', storage_api_ip);
    return storage_api_ip;
}

function load_web_hw_api_ip() {
    let web_hw_api_ip_arr = localStorage.getItem(web_hw_api_ip_key);
    // console.log('loaded: ', web_hw_api_ip_arr)
    if (web_hw_api_ip_arr !== null) {
        web_hw_api_ip_arr = web_hw_api_ip_arr.split(',');
        input_text_arr.forEach(function(item, i, arr) {
            document.getElementById(item).value = web_hw_api_ip_arr[i];
        });
    }
}

function save_web_hw_api_ip() {
    let web_hw_api_ip_arr = [];
    input_text_arr.forEach(function(item, i, arr) {
        web_hw_api_ip_arr = web_hw_api_ip_arr.concat(document.getElementById(item).value);
    });
    if (web_hw_api_ip_arr.length === 5) {
        localStorage.setItem(web_hw_api_ip_key, web_hw_api_ip_arr)
        // console.log('saved: ', web_hw_api_ip_arr)

    }
}


// TODO: add validation, refactor, and other shit
// there is no error messages, validation, and dozens of shitcode
web_hw_api_element.addEventListener('click', () => {
    if (event.target.type === "button") {
        // console.log(event)
        const sectionId = event.target.getAttribute('data-section');
        // let xhr = new XMLHttpRequest();
        if ('web_hw_api_ip_connect' === sectionId) {
        //     var move_to_idle_api_url = storage_api_ip + 'storage/move_to/idle_position'
        //     xhr.open('POST', move_to_idle_api_url, true);
        //     xhr.send();
            let web_hw_api_ip_arr = [];
            input_text_arr.forEach(function(item, i, arr) {
                web_hw_api_ip_arr = web_hw_api_ip_arr.concat(document.getElementById(item).value);
            });
            event.target.hidden = true;
            document.getElementById('web_hw_api_ip_disconnect').hidden = false;
            document.getElementById('offline_badge').hidden = true;
            document.getElementById('online_badge').hidden = false;
            // console.log([web_hw_api_ip_arr.slice(0, 4).join('.'), web_hw_api_ip_arr[4]].join(':'))

            save_web_hw_api_ip();

            update_global_storage_api_ip(web_hw_api_ip_arr);
            // console.log('Updated ip', storage_api_ip)
            connected_with_web_hw_api = true

        } else if ('web_hw_api_ip_disconnect' === sectionId) {
            let web_hw_api_ip_arr = [];
            input_text_arr.forEach(function(item, i, arr) {
                web_hw_api_ip_arr = web_hw_api_ip_arr.concat(document.getElementById(item).value);
            });
            event.target.hidden = true;
            document.getElementById('web_hw_api_ip_connect').hidden = false;
            document.getElementById('offline_badge').hidden = false;
            document.getElementById('online_badge').hidden = true;
            // console.log([web_hw_api_ip_arr.slice(0, 4).join('.'), web_hw_api_ip_arr[4]].join(':'));

            connected_with_web_hw_api = false
        }
    }
})

function status_update(json_resp) {
    let status = 'Status: ' + json_resp['body']['status']['name'];
    status = status ? status : 'Status: IDLE';
    document.getElementById("asrs_status").innerHTML = status;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function get_status() {
    let xhr = new XMLHttpRequest();
    // console.log('WOAAAAAAAAAAH', get_status_api_url)

    while (true) {

        if (connected_with_web_hw_api) {
            let get_status_api_url = storage_api_ip + 'storage/status';
            // console.log(get_status_api_url)
            xhr.open('POST', get_status_api_url, true);
            xhr.onreadystatechange = function() {
                if (this.readyState === 4 && this.status === 200) {
                    let json_resp = JSON.parse(this.responseText);
                    status_update(json_resp);
                }
            };
            xhr.send()

        }
        await sleep(500);
    }
}

function location_update(json_resp) {
    let location = 'Location: ' + json_resp['body']['location']['name'];
    location = location ? location : 'Location: HOME';
    document.getElementById("asrs_location").innerHTML = location
}

async function get_location() {
    let xhr = new XMLHttpRequest();

    while (true) {
        if (connected_with_web_hw_api) {
            let get_location_api_url = storage_api_ip + 'storage/location';
            xhr.open('POST', get_location_api_url, true);
            xhr.onreadystatechange = function() {
                if (this.readyState === 4 && this.status === 200) {
                    let json_resp = JSON.parse(this.responseText);
                    location_update(json_resp);
                }
            };
            xhr.send()
        }
        await sleep(500);
    }
}

function parse_queue_to_list(queue_arr) {
    var list = document.createElement('ul');
    for(let i = 0; i < queue_arr.length; i++) {
        // Create the list item:
        let item = document.createElement('li');
        // Set its contents:
        // // console.log(queue_arr[i][0], queue_arr[i][2], queue_arr[i][2].join(', '))
        item.appendChild(document.createTextNode(queue_arr[i][0] + ', args: ' + queue_arr[i][2].join(', ')));
        // Add it to the list:
        list.appendChild(item);
    }
    // Finally, return the constructed list:
    return list;
}

function queue_update(json_resp) {
    let queue_list = parse_queue_to_list(json_resp["body"]["queue"]).innerHTML;
    queue_list = queue_list ? queue_list : '<p>Empty</p>';
    document.getElementById("queue").innerHTML = queue_list;
}

async function get_queue() {
    let xhr = new XMLHttpRequest();

    while (true) {
        if (connected_with_web_hw_api) {
            let get_location_api_url = storage_api_ip + 'storage/queue';
            xhr.open('POST', get_location_api_url, true);
            xhr.onreadystatechange = function() {
                if (this.readyState === 4 && this.status === 200) {
                    let json_resp = JSON.parse(this.responseText);
                    queue_update(json_resp);
                }
            };
            xhr.send()
        }
        await sleep(500);
    }
}

function current_task_update(json_resp) {

    let current_task_resp = json_resp['body']['current_task'];
    let current_task;
    if (current_task_resp) {
        current_task = '<p>' + current_task_resp['name'] + ', args: ' +
        current_task_resp['task_args'].join(', ') + '</p>';
    } else {
        current_task = '<p>Empty</p>';
    }
    document.getElementById("current_task").innerHTML = current_task;
}

async function get_current_task() {
    let xhr = new XMLHttpRequest();


    while (true) {
        if (connected_with_web_hw_api) {
            let get_location_api_url = storage_api_ip + 'storage/current_task';
            xhr.open('POST', get_location_api_url, true);
            xhr.onreadystatechange = function() {
                if (this.readyState === 4 && this.status === 200) {
                    let json_resp = JSON.parse(this.responseText);
                    current_task_update(json_resp);
                }
            };
            xhr.send()
        }
        await sleep(500);
    }
}

const application = document.getElementById('application');

let buttons_and_urls = [];

application.addEventListener('click', () => {
    if (event.target.type === "button") {
//         // console.log(event.target);
         const sectionId = event.target.getAttribute('data-section');
         let xhr = new XMLHttpRequest();
         let json;
         if (connected_with_web_hw_api) {
             if ('move_to_idle_position' === sectionId) {
                let move_to_idle_api_url = storage_api_ip + 'storage/move_to/idle_position';
                xhr.open('POST', move_to_idle_api_url, true);
                xhr.send();
             } else if ('move_to_home' === sectionId) {
                let move_to_home_api_url = storage_api_ip + 'storage/move_to/home';
                xhr.open('POST', move_to_home_api_url, true);
                xhr.send();
             } else if ('move_to_conveyor' === sectionId) {
                let move_to_home_api_url = storage_api_ip + 'storage/move_to/conveyor';
                xhr.open('POST', move_to_home_api_url, true);
                xhr.send();
             } else if ('move_to_conveyor' === sectionId) {
                let move_to_home_api_url = storage_api_ip + 'storage/move_to/conveyor';
                xhr.open('POST', move_to_home_api_url, true);
                xhr.send();
             } else if ('pick_asrs' === sectionId) {
                let move_to_home_api_url = storage_api_ip + 'storage/pick/asrs';

                const side = Number(document.getElementById('pick_side').value);
                const row = Number(document.getElementById('pick_row').value);
                const column = Number(document.getElementById('pick_column').value);

                xhr.open('POST', move_to_home_api_url, true);
                xhr.setRequestHeader('Content-type', 'application/json; charset=utf-8');
                json = JSON.stringify({
                    side: side,
                    row: row,
                    column: column
                });

                xhr.send(json);
             } else if ('pick_conveyor' === sectionId) {
                let move_to_home_api_url = storage_api_ip + 'storage/pick/conveyor';
                xhr.open('POST', move_to_home_api_url, true);
                xhr.send();
             } else if ('place_asrs' === sectionId) {
                let move_to_home_api_url = storage_api_ip + 'storage/place/asrs';

                const side = Number(document.getElementById('place_side').value);
                const row = Number(document.getElementById('place_row').value);
                const column = Number(document.getElementById('place_column').value);

                xhr.open('POST', move_to_home_api_url, true);
                xhr.setRequestHeader('Content-type', 'application/json; charset=utf-8');
                json = JSON.stringify({
                    side: side,
                    row: row,
                    column: column
                });

                xhr.send(json);
             } else if ('place_conveyor' === sectionId) {
                let move_to_home_api_url = storage_api_ip + 'storage/place/conveyor';
                xhr.open('POST', move_to_home_api_url, true);
                xhr.send();
             }
         }
    }
});

get_status();
get_location();
get_queue();
get_current_task();
load_web_hw_api_ip();
