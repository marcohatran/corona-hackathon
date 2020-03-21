const ageInp = document.getElementById('ageInp');
const workRad = document.getElementById('workRad');
const workoutRad = document.getElementById('workoutRad');
const noWork = document.getElementById('noWorkRad');
const checkboxes = document.querySelectorAll('[type=checkbox]');
const alertBox = document.getElementById('alertBox');
const resultLabel = document.getElementById('resultLabel');
const diagnoseMeBtn = document.getElementById('diagnoseMeBtn');

checkboxes.forEach(function(checkbox) {
    checkbox.addEventListener('click', function(e) {
        if (e.srcElement.checked) {
            e.srcElement.nextElementSibling.textContent = 'Yes';
        } else {
            e.srcElement.nextElementSibling.textContent = 'No';
        }
    });
});

function alertErr(msg) {
    resultLabel.classList.add('d-none');
    alertBox.classList.remove('d-none');
    alertBox.textContent = msg;
}

diagnoseMeBtn.addEventListener('click', function() {
    const age = parseFloat(ageInp.value);

    if (!age || age < 0) {
        return alertErr('Incorrect age input');
    } else if (Array.from(checkboxes).some(cb => !['fever', 'fatigue', 'cough', 'diff-breath', 'material-cough'].includes(cb.getAttribute('symptom')))) {
        return alertErr('Don\'t miss with attribute names');
    }

    const data = Array.from(checkboxes).reduce(function(accumulator, cb) {
        const symptom = cb.getAttribute('symptom');
        let tempPropVal, index;

        if (symptom == 'fever') {
            const ranges = [
                [.1, 4], [5, 9], [10, 14], [15, 19],
                [20, 24], [25, 29], [30, 34],
                [35, 39], [40, 44], [45, 49],
                [50, 54], [55, 59], [60, 64]
            ];
            
            if (age > 64) {
                index = 12;
            } else {
                for (let i = 0; i < ranges.length; i++) {
                    if (age >= ranges[i][0] && age <= ranges[i][1]) {
                        index = i;
                        break;
                    }
                } 
            }

            tempPropVal = {
                infected: cb.checked,
                index
            };
        } else if (symptom == 'fatigue') {
            if (workRad.checked) {
                index = 0;
            } else if (workoutRad.checked) {
                index = 1;
            } else {
                index = 2;
            }
            
            tempPropVal = {
                infected: cb.checked,
                index
            };
        } else {
            tempPropVal = cb.checked;
        }
        return { ...accumulator, [symptom]: tempPropVal };
    }, {});

    alertBox.classList.add('d-none');
    diagnoseSymptoms(data);
});

async function diagnoseSymptoms(data) {
    const response = await fetch('/diagnose', {
        method: 'POST',
        headers: {
            'Content-type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    
    resultLabel.textContent = `The probability that you have corona is ${(Number(await response.text()) * 100).toFixed(8)}%`;
    resultLabel.classList.remove('d-none');
}