import base64
from datetime import datetime
from flask import Blueprint
from flask import redirect, url_for, render_template, request, abort
from bloghive.posts.forms import PostForm, CommentForm
from bloghive.models import Post, Comment
from bloghive import db
from flask_login import current_user, login_required

posts = Blueprint('posts', __name__)


@posts.route("/post/new", methods=['POST', 'GET'])
@login_required
def new_post():
    form = PostForm()

    if form.validate_on_submit():
        action = request.form.get('action')
        if action == 'Save Draft':
            current_user.draft_title = form.title.data
            current_user.draft_content = form.content.data
            db.session.commit()
            return redirect(url_for('main.home'))
        elif action == 'Post':
            post = Post(title=form.title.data, content=form.content.data, author=current_user,
                        date_posted=datetime.now().astimezone(), date_updated=datetime.now().astimezone())
            current_user.draft_title = None
            current_user.draft_content = None
            db.session.add(post)
            db.session.commit()
            return redirect(url_for('posts.post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = current_user.draft_title
        form.content.data = current_user.draft_content

    return render_template('create_post.html', title="New Post", form=form, button_text_1="Post",
                           button_text_2="Save Draft", role="create_post")


@posts.route("/post/<int:post_id>", methods=['POST', 'GET'])
def post(post_id):
    form = CommentForm()
    post = Post.query.get_or_404(post_id)
    if form.validate_on_submit():
        text = form.comment.data
        if text:
            comment = Comment(content=text, user_id=current_user.id, post_id=post.id,
                              date_posted=datetime.now().astimezone())
            db.session.add(comment)
            db.session.commit()
        return redirect(url_for('posts.post', post_id=post.id))
    liked, disliked = False, False
    if current_user.check_like(post):
        liked = True
    elif current_user.check_dislike(post):
        disliked = True
    db.session.commit()
    image_data = {}
    for comment in post.comments:
        image_data[comment.user.id] = base64.b64encode(comment.user.image_file).decode('utf-8')
    return render_template('post.html', title=post.title, post=post, liked=liked, disliked=disliked, form=form,
                           image_data=image_data)


@posts.route("/post/<int:post_id>/update", methods=['POST', 'GET'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.date_updated = datetime.now().astimezone()
        db.session.commit()
        return redirect(url_for('posts.post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, button_text="Update", role="update_post")


@posts.route("/post/<int:post_id>/delete/confirm")
@login_required
def delete_post_confirm(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    return render_template('delete_post_confirm.html', title='Delete Confirmation', post=post)


@posts.route("/post/<int:post_id>/delete")
@login_required
def delete(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('main.home'))


@posts.route('/like/<int:post_id>')
@login_required
def like(post_id):
    post = Post.query.filter_by(id=post_id).first()
    current_user.like_post(post)
    db.session.commit()
    return redirect(url_for('posts.post', post_id=post.id))


@posts.route('/dislike/<int:post_id>')
@login_required
def dislike(post_id):
    post = Post.query.filter_by(id=post_id).first()
    current_user.dislike_post(post)
    db.session.commit()
    return redirect(url_for('posts.post', post_id=post.id))


@posts.route("/delete_comment/<int:comment_id>")
@login_required
def delete_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()
    if comment is not None:
        post_id = comment.post.id
        db.session.delete(comment)
        db.session.commit()
    return redirect(url_for('posts.post', post_id=post_id))
