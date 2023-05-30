from flask import Flask, render_template, request
from User_Interaction import app_gui  # import the necessary module

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def dream_form():
    if request.method == 'POST':
        dream_input = request.form['dream_input']
        dream_output = app_gui.generate_dream(dream_input)
        return render_template('results.html', dream_output=dream_output)

    return render_template('form.html')

if __name__ == '__main__':
    app.run(debug=True)
