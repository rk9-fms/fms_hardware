'use strict';

let conveyor_api_prefix = '/api/v1/conveyor/';
let conveyor_api_ip = 'http://127.0.0.1:5000' + conveyor_api_prefix;


function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

let status_map = {
    1: document.getElementsByClassName('lock_1')[0].getElementsByClassName('status')[0],
    2: document.getElementsByClassName('lock_2')[0].getElementsByClassName('status')[0],
    3: document.getElementsByClassName('lock_3')[0].getElementsByClassName('status')[0],
    4: document.getElementsByClassName('lock_4')[0].getElementsByClassName('status')[0],
};

function status_update(json_resp) {
    json_resp['body']['locks_state'].forEach(function(item, i, arr) {
        console.log(i);
        let status_div = status_map[item['id']];
        console.log(status_div);
        if (item['is_busy'] === true) {
            status_div.style.backgroundColor = 'red'
        } else {
            status_div.style.backgroundColor = 'green'
        }
    })
}

async function get_status() {
    let xhr = new XMLHttpRequest();

    while (true) {

        let get_status_api_url = conveyor_api_ip + 'status';
        xhr.open('POST', get_status_api_url, true);
        xhr.onreadystatechange = function() {
            if (this.readyState === 4 && this.status === 200) {
                let json_resp = JSON.parse(this.responseText);
                status_update(json_resp);
            }
        };
        xhr.send();

        await sleep(500);
    }
}

// TODO: uncomment after realisation
// get_status();

// buttons handler part:
const conveyor = document.getElementById('conveyor');

let buttons_map = {
    'lock_1_close': {'endpoint': 'locks/close', 'params': {'ids': [1]}},
    'lock_1_open': {'endpoint': 'locks/open', 'params': {'ids': [1]}},
    'lock_1_pass_one': {'endpoint': 'locks/pass_one', 'params': {'ids': [1]}},
    'lock_2_close': {'endpoint': 'locks/close', 'params': {'ids': [2]}},
    'lock_2_open': {'endpoint': 'locks/open', 'params': {'ids': [2]}},
    'lock_2_pass_one': {'endpoint': 'locks/pass_one', 'params': {'ids': [2]}},
    'lock_3_close': {'endpoint': 'locks/close', 'params': {'ids': [3]}},
    'lock_3_open': {'endpoint': 'locks/open', 'params': {'ids': [3]}},
    'lock_3_pass_one': {'endpoint': 'locks/pass_one', 'params': {'ids': [3]}},
    'lock_4_close': {'endpoint': 'locks/close', 'params': {'ids': [4]}},
    'lock_4_open': {'endpoint': 'locks/open', 'params': {'ids': [4]}},
    'lock_4_pass_one': {'endpoint': 'locks/pass_one', 'params': {'ids': [4]}},
};

conveyor.addEventListener('click', (event) => {
    if (event.target.type === "button") {
        const sectionId = event.target.getAttribute('data-section');
        let xhr = new XMLHttpRequest();
        const button_action = buttons_map[sectionId];

        let action_url = conveyor_api_ip + button_action['endpoint'];

        xhr.open('POST', action_url, true);
        xhr.setRequestHeader('Content-type', 'application/json; charset=utf-8');
        const json = JSON.stringify(button_action['params']);
        xhr.send(json);
        console.log(action_url, json);
    }
});

get_status();
