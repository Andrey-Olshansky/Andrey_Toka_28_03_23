from sqlalchemy import create_engine, Column, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship

database_uri = "sqlite:///database.db"
engine = create_engine(database_uri, echo=True)


class Base(DeclarativeBase):
    pass


class VkUser(Base):
    __tablename__ = "vk_user"
    user_id = Column(Integer, primary_key=True)
    couples = relationship("Couple", back_populates="vk_user")


class Couple(Base):
    __tablename__ = "couple"
    id = Column(Integer, primary_key=True)
    couple_user_id = Column(Integer)
    vk_user_id = Column(Integer, ForeignKey("vk_user.user_id"))
    vk_user = relationship("VkUser", back_populates="couples")


Base.metadata.create_all(bind=engine)
engine = create_engine(database_uri, echo=False)
Session = sessionmaker(autoflush=False, bind=engine)


def save_vk_user(user_id):
    if find_vk_user_by_id(user_id) is None:
        with Session(autoflush=False, bind=engine) as db:
            vk_user = VkUser(user_id=user_id)
            db.add(vk_user)
            db.commit()


def get_users():
    with Session(autoflush=False, bind=engine) as db:
        return db.query(VkUser).all()


def find_vk_user_by_id(user_id):
    with Session(autoflush=False, bind=engine) as db:
        return db.query(VkUser).filter(VkUser.user_id == user_id).first()


def find_history_couples_id_by_user_id(user_id):
    with Session(autoflush=False, bind=engine) as db:
        user = db.query(VkUser).filter(VkUser.user_id == user_id).first()
        return [i.couple_user_id for i in user.couples]


def add_couple_in_history(user_id, couple_user_id):
    with Session(autoflush=False, bind=engine) as db:
        couple = Couple(couple_user_id=couple_user_id, vk_user_id=user_id)
        db.add(couple)
        db.commit()
