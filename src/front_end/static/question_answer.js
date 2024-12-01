
function get_user_inputs() {
    var id = document.getElementsByClassName('paragraph_id')[0].innerHTML;
    var num_questions = document.getElementsByClassName('num_questions')[0].getAttribute('name');
    let UserResponse = [];
    for (var i = 1; i <= num_questions; i++) {
        UserResponse.push(getCheckedAnswer("Q" + i));
    }

    let myHeaders = new Headers({
        "Content-Type": "application/json",
    });

    fetch('/getResult', {
        method: 'POST',
        body: JSON.stringify({
            _id:id,
            response:UserResponse
        }),
        headers: myHeaders
    })
    .then((response)=>{
        if (response.ok) {
            response.text()
            .then((html_content)=>{
                var update_element = document.getElementsByClassName('question-list');
                console.log(response);
                update_element[0].innerHTML = html_content;
            })
            .catch((error)=>{
                console.error('Failed update content', error);
            });

        } else {
            throw new Error('response is not OK status');
        }
        
    });
}



function getCheckedAnswer(radioName) {
    // get checked answer in a question
    let singleChoice = {};
    var radios = document.getElementsByName(radioName);
    for (var y = 0; y < radios.length; y++)
        if (radios[y].checked) {
            singleChoice['user_answer'] = radios[y].getAttribute('value');
            singleChoice['_order'] = radioName;
            return singleChoice
        }
    // case none of options is selected
    if (Object.keys(singleChoice).length === 0) {
        singleChoice['_order'] = radioName;
        singleChoice['user_answer'] = "No choice";
        return singleChoice
    }
}

