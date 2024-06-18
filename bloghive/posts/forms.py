from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()], render_kw={"placeholder": "Title"})
    content = TextAreaField('Content', validators=[DataRequired()],
                            render_kw={"placeholder": "Enter post", "class": "content_field"})
    draft_content = SubmitField('Save Draft')
    post_content = SubmitField('Post')


class CommentForm(FlaskForm):
    comment = StringField('Comment', validators=[DataRequired(), Length(max=100)],
                          render_kw={"placeholder": "Write a comment..."})
    submit = SubmitField('Post')
