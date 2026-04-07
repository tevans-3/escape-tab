from dataclasses import dataclass, asdict
from flask import Flask, render_template, session, request, jsonify, abort
import random
import os
import uuid
import json

app = Flask(__name__)
app.config.from_object('config')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

PROBLEMS_PATH = os.path.join(os.path.dirname(__file__), 'amc', 'json')


@dataclass
class QuestionPrivate:
    id: str
    question: str
    options: dict | None
    answer: str


@dataclass
class QuestionPublic:
    id: str
    question: str
    options: dict | None


def to_public(q: QuestionPrivate) -> QuestionPublic:
    return QuestionPublic(id=q.id, question=q.question, options=q.options)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit_answer', methods=["POST"])
def submit_answer():
    data = request.get_json()
    client_id = data.get("client_id", "")
    answer = data.get("answer", "")
    question_num = data.get("question_num", 0)

    try:
        uuid.UUID(client_id)
    except ValueError:
        abort(400, description="Invalid client_id")

    key = 'current_question_' + client_id
    if key not in session:
        abort(400, description="No question found for client_id")

    q_private = session[key]
    if str(answer).strip().upper() == str(q_private['answer']).strip().upper():
        question_num = int(question_num) + 1
        if question_num >= 3:
            session.pop(key, None)
            return jsonify({
                "escaped": True,
                "correct": True,
                "message": "Congratulations! You have escaped!"
            })
        else:
            return jsonify({
                "escaped": False,
                "correct": True,
                "message": f"Correct! {question_num} of 3 solved.",
                "question_num": question_num
            })
    else:
        return jsonify({
            "escaped": False,
            "correct": False,
            "message": "Incorrect. Try again."
        })


def get_question_private():
    files = [f for f in os.listdir(PROBLEMS_PATH) if f.endswith('.json')]
    f_idx = random.randrange(len(files))

    filepath = os.path.join(PROBLEMS_PATH, files[f_idx])
    with open(filepath, 'r') as f:
        test_data = json.load(f)

    variants = list(test_data['variants'].keys())
    variant = random.choice(variants)
    problems = test_data['variants'][variant]

    q = random.choice(problems)

    contest = test_data.get('contest', '')
    year = test_data.get('year', '')
    q_id = f"{contest}_{year}_{variant}_{q['number']}"

    return QuestionPrivate(
        id=q_id,
        question=q['problem'],
        options=q.get('options', None),
        answer=str(q['answer'])
    )


@app.route('/question', methods=["GET"])
def get_question():
    client_id = request.args.get("client_id", "")
    try:
        uuid.UUID(client_id)
    except ValueError:
        abort(400, description="Invalid client_id")

    q_private = get_question_private()
    if q_private is None:
        return jsonify({"error": "Could not load question"}), 500

    session['current_question_' + client_id] = asdict(q_private)
    q_public = to_public(q_private)
    return jsonify({
        'problem': q_public.question,
        'options': q_public.options,
        'client_id': client_id,
        'id': q_public.id
    })


if __name__ == '__main__':
    app.run(debug=True)
