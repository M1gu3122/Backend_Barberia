from typing import Generic, List, Optional, Type, TypeVar
from sqlalchemy.orm import Session

T = TypeVar("T")


class Repository(Generic[T]):

    def __init__(self, model: Type[T], db: Session):
        self._model = model
        self._session = db

    def create(self, obj: T) -> T:
        self._session.add(obj)
        self._session.commit()
        self._session.refresh(obj)
        return obj

    def get(self, id_: int) -> Optional[T]:
        return self._session.get(self._model, id_)

    def get_all(self) -> List[T]:
        return self._session.query(self._model).all()

    def update(self, obj: T) -> T:
        self._session.add(obj)
        self._session.commit()
        self._session.refresh(obj)
        return obj

    def delete(self, obj: T):
        self._session.delete(obj)
        self._session.commit()

    def get_by_id(self, id_: int) -> Optional[T]:
        return self._session.get(self._model, id_)

    def exists(self, id_: int) -> bool:
        return self.get_by_id(id_) is not None

