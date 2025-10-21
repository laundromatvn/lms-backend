from typing import List

from sqlalchemy.orm import Session

from app.libs.database import with_db_session_classmethod
from app.models.datapoint import Datapoint


class DatapointOperation:
    """Business logic operations for datapoint management."""

    @classmethod
    @with_db_session_classmethod
    def create(cls, db: Session, datapoint: Datapoint) -> Datapoint:
        db.add(datapoint)
        db.commit()
        return datapoint

    @classmethod
    @with_db_session_classmethod
    def create_many(cls, db: Session, datapoints: List[Datapoint]) -> List[Datapoint]   :
        db.add_all(datapoints)
        db.commit()
        return datapoints
