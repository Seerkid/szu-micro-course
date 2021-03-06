from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.hybrid import hybrid_property
from flask.ext.babel import lazy_gettext as _

from mooc.extensions import db
from mooc.utils.helpers import enumdef
from mooc.models.master import ModelMixin


question_tags = db.Table(
    'question_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('question_tag.id')),
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'))
)


class UpDownRecord(db.Model, ModelMixin):

    __tablename__ = 'up_down_record'

    TYPE_UP = 1
    TYPE_DOWN = 0

    id = db.Column(db.Integer, primary_key=True)
    up_or_down = db.Column(db.Integer, nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    answer = db.relationship(
        'Answer', uselist=False,
        backref=db.backref('up_down_record', uselist=False))
    isdeleted = db.Column(db.Boolean, default=False)

    def __init__(self, user, up_or_down):
        self.user = user
        self.isdeleted = False
        if up_or_down in (self.TYPE_UP, self.TYPE_DOWN):
            self.up_or_down = up_or_down
        else:
            self.up_or_down = self.TYPE_UP


class Answer(db.Model, ModelMixin):

    __tablename__ = 'answer'

    STATE_VALUE = ('normal', 'hot', 'deleted')
    STATE_TEXT = (_('Normal'), _('Hot'), _('Deleted'))

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    up_count = db.Column(db.Integer, default=0)
    down_count = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    edit_time = db.Column(db.DateTime, default=datetime.utcnow)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    lecture_id = db.Column(db.Integer, db.ForeignKey('lecture.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    anonymous = db.Column(db.Boolean, default=False)
    parent_id = db.Column(db.Integer)
    up_down_record_id = db.Column(db.Integer,
                                  db.ForeignKey('up_down_record.id'))
    state = db.Column(db.Enum(*STATE_VALUE), default='normal')

    @hybrid_property
    def like_count(self):
        return self.up_count - self.down_count


class Question(db.Model, ModelMixin):

    __tablename__ = 'question'

    STATE_VALUE = ('normal', 'hot', 'deleted')
    STATE_TEXT = (_('Normal'), _('Hot'), _('Deleted'))

    WEIGHT_OF_READCOUNT = 0.2
    WEIGHT_OF_UPCOUNT = 0.3
    WEIGHT_OF_ANSWERCOUNT = 0.5

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20))
    content = db.Column(db.Text)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    edit_time = db.Column(db.DateTime, default=datetime.utcnow)
    read_count = db.Column(db.Integer, default=0)
    up_count = db.Column(db.Integer, default=0)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lecture.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    anonymous = db.Column(db.Boolean, default=False)
    answers = db.relationship('Answer', backref='question', uselist=True)
    state = db.Column(db.Enum(*STATE_VALUE), default='normal')
    tags = db.relationship('QuestionTag', secondary=question_tags,
                           backref=db.backref('questions'))

    @hybrid_property
    def answer_count(self):
        return self.answers.count()

    @answer_count.expression
    def answer_count(cls):
        return (select([func.count(Answer.id)]).
                where(Answer.question_id == cls.id).
                label('answer_count'))

    @hybrid_property
    def hotest(self):
        return (self.answers.count() * self.WEIGHT_OF_ANSWERCOUNT +
                self.up_count * self.WEIGHT_OF_UPCOUNT +
                self.read_count * self.WEIGHT_OF_READCOUNT)

    @hotest.expression
    def hotest(cls):
        ac = (select([func.count(Answer.id)]).
              where(Answer.question_id == cls.id).
              label('answers_count'))
        return func.abs(ac * cls.WEIGHT_OF_ANSWERCOUNT +
                        cls.up_count * cls.WEIGHT_OF_UPCOUNT +
                        cls.read_count * cls .WEIGHT_OF_READCOUNT)


class QuestionTag(db.Model, ModelMixin):

    __tablename__ = 'question_tag'

    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(20))

    @hybrid_property
    def count(self):
        return self.count()

    @count.expression
    def count(cls):
        return (select([func.count(question_tags.c.tag_id)]).
                where(cls.id == question_tags.c.tag_id).label('count'))
