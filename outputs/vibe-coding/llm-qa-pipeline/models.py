"""Database models for TC validation results"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class FailureRecord(db.Model):
    """실패한 TC 기록 저장"""
    __tablename__ = 'failure_records'

    id = db.Column(db.Integer, primary_key=True)
    tc_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    tc_type = db.Column(db.String(50), nullable=False, index=True)
    user_input = db.Column(db.Text)
    failure_reason = db.Column(db.Text, nullable=False)
    failure_category = db.Column(db.String(20), index=True)  # format|quality|type_rule
    timestamp = db.Column(db.DateTime, default=datetime.now, index=True)
    is_resolved = db.Column(db.Boolean, default=False, index=True)
    notes = db.Column(db.Text)  # 사용자 메모

    def to_dict(self):
        """DB 객체를 dict로 변환"""
        return {
            'id': self.id,
            'tc_id': self.tc_id,
            'tc_type': self.tc_type,
            'user_input': self.user_input,
            'failure_reason': self.failure_reason,
            'failure_category': self.failure_category,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'is_resolved': self.is_resolved,
            'notes': self.notes
        }

    def __repr__(self):
        return f"<FailureRecord {self.tc_id}: {self.failure_category}>"


class ValidationSession(db.Model):
    """검증 세션 기록"""
    __tablename__ = 'validation_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    selected_types = db.Column(db.Text)  # JSON: ["짧은주제", "기획안", ...]
    n_per_type = db.Column(db.Integer, default=2)
    total_generated = db.Column(db.Integer, default=0)
    total_valid = db.Column(db.Integer, default=0)
    total_invalid = db.Column(db.Integer, default=0)
    total_duplicates = db.Column(db.Integer, default=0)
    total_failures_saved = db.Column(db.Integer, default=0)
    start_time = db.Column(db.DateTime, default=datetime.now, index=True)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='running')  # running|completed|failed
    error_message = db.Column(db.Text)

    def to_dict(self):
        """DB 객체를 dict로 변환"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'selected_types': self.selected_types,
            'n_per_type': self.n_per_type,
            'total_generated': self.total_generated,
            'total_valid': self.total_valid,
            'total_invalid': self.total_invalid,
            'total_duplicates': self.total_duplicates,
            'total_failures_saved': self.total_failures_saved,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'error_message': self.error_message
        }

    def __repr__(self):
        return f"<ValidationSession {self.session_id}: {self.status}>"
