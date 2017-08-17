from flask.ext.sqlalchemy import SQLAlchemy

__author__ = 'alessio.rocchi'
db = SQLAlchemy()


class Org(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    orgname = db.Column(db.String(256), unique=True)

    def __init__(self, orgname):
        self.orgname = orgname

    def __repr__(self):
        return '<id: {}, orgname: {}>'.format(self.id, self.orgname)


class Vdc(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    orgid = db.Column(db.Integer, db.ForeignKey('org.id'))
    name = db.Column(db.String(256), unique=True)
    cpu_reservation = db.Column(db.Integer, unique=False)
    memory_allocation = db.Column(db.Integer, unique=False)

    def __init__(self, orgid, name, cpu_reservation, memory_allocation):
        self.orgid = orgid
        self.name = name
        self.cpu_reservation = cpu_reservation
        self.memory_allocation = memory_allocation

    def __repr__(self):
        return '<{}: cpu_reservation: {}, memory_allocation: {}>'.format(self.name,
                                                                         self.cpu_reservation,
                                                                         self.memory_allocation)


class VirtualMachine(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    orgid = db.Column(db.Integer, db.ForeignKey('org.id'))
    name = db.Column(db.String(256), unique=True)

    def __init__(self, orgid, name):
        self.orgid = orgid
        self.name = name
