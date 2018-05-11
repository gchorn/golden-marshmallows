from sqlalchemy import Column, create_engine, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

engine = create_engine('sqlite:///:memory:')
Base = declarative_base()


class WizardCollege(Base):
    __tablename__ = 'wizard_college'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    alchemists = relationship('Alchemist', backref='school',
                              cascade='all, delete, delete-orphan',
                              single_parent=True)

    def __repr__(self):
        return '<WizardCollege(name={self.name!r})>'.format(self=self)


class Alchemist(Base):
    __tablename__ = 'alchemists'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    school_id = Column(Integer, ForeignKey('wizard_college.id'))
    formulae = relationship('Formula', backref='author',
                            cascade='all, delete, delete-orphan',
                            single_parent=True)

    def __repr__(self):
        return '<Alchemist(name={self.name!r})>'.format(self=self)


class Formula(Base):
    __tablename__ = 'forumulae'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author_id = Column(Integer, ForeignKey('alchemists.id'))

    def __repr__(self):
        return '<Formula(title={self.title!r})>'.format(self=self)


class CamelFormula(Base):
    __tablename__ = 'camel_formulae'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    camelAttribute = Column(String)


Base.metadata.create_all(engine)
