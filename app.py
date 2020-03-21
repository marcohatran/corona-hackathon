from flask import Flask, render_template, request

app = Flask(__name__)

dis_prob = .00001
sym_given_dis_prob = {
    'fever': .93,
    'fatigue': .41,
    'cough': .72,
    'diff-breath': .31,
    'material-cough': .28
}
not_dis_prob = 0.99999
sym_given_not_dis_prob = {
    'fever': [
                0.00000213,
                0.0000013,
                0.00000426,
                0.00001333333,
                0.00002666666,
                0.0000288,
                0.00004,
                0.00006666666,
                0.00008,
                0.00008666666,
                0.00009333333,
                0.00010666666,
                0.00012,
                0.0001
            ],
    'fatigue': [.69, .81, .07],
    'cough': .5,
    'diff-breath': .329,
    'material-cough': .1
}

@app.route('/')
def display_homepage():
    return render_template('index.html')

@app.route('/diagnose', methods = ['GET', 'POST'])
def diagnose_symptoms():
    data = request.get_json()

    prob_sym_given_dis = dis_prob
    prob_sym_given_not_dis = not_dis_prob

    for sym in data:
        if sym == 'fever' or sym == 'fatigue':
            if data[sym]['infected']:
                prob_sym_given_dis *= sym_given_dis_prob[sym]
                prob_sym_given_not_dis *= sym_given_not_dis_prob[sym][data[sym]['index']]
            else:
                prob_sym_given_dis *= 1 - sym_given_dis_prob[sym]
                prob_sym_given_not_dis *= 1 - sym_given_not_dis_prob[sym][data[sym]['index']]
        else:
            if data[sym]:
                prob_sym_given_dis *= sym_given_dis_prob[sym]
                prob_sym_given_not_dis *= sym_given_not_dis_prob[sym]
            else:
                prob_sym_given_dis *= 1 - sym_given_dis_prob[sym]
                prob_sym_given_not_dis *= 1 - sym_given_not_dis_prob[sym]

    return str(prob_sym_given_dis / (prob_sym_given_dis + prob_sym_given_not_dis))

if __name__ == '__main__':
    app.run(host = '0.0.0.0')