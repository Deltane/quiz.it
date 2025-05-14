from flask_wtf import FlaskForm
from markupsafe import Markup 
from wtforms import StringField, FileField, TextAreaField, IntegerField, SelectField, RadioField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional

# Define WTForms for quiz setup
class QuizSetupForm(FlaskForm):
    quiz_name = StringField('Quiz Name', validators=[DataRequired()])
    upload_file = FileField('Upload File')
    ai_prompt = TextAreaField('Or ask AI')
    timer = IntegerField('Timer (minutes)', default=0, validators=[NumberRange(min=0)])
    quiz_type = SelectField('Quiz Type', choices=[
        ('', 'Select quiz type'),
        ('Multiple Choice', 'Multiple Choice'),
        ('Short Answer', 'Short Answer'),
        ('Fill in the Blank', 'Fill in the Blank')
    ], validators=[DataRequired()])
    question_count = IntegerField('Question Count', validators=[
        DataRequired(),
        NumberRange(min=1, max=50)
    ])
    # Renamed 'privacy' to 'visibility' for clarity, maps to Quiz.is_public
    visibility = RadioField('Visibility', choices=[
        ('public', 'Public'),
        ('private', 'Private')
    ], default='public', validators=[DataRequired()])
    submit = SubmitField('Generate Quiz')