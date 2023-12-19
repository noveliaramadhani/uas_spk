from sqlalchemy import String, Integer, Column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Milk(Base):
    __tablename__ = "tbl_pilihansusu"
    id = Column(Integer, primary_key=True)
    harga = Column(Integer)
    kalori = Column(Integer)
    protein = Column(Integer)
    lemak = Column(Integer)
    ukuran = Column(Integer)


    def __repr__(self):
        return f"Milk(id={self.id!r}, harga={self.harga!r}, kalori={self.kalori!r}, protein={self.protein!r}, lemak={self.lemak!r}, ukuran={self.ukuran!r})"