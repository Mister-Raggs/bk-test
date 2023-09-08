import datetime
import mongoengine as me


class BaseModel(me.Document):
    date_created = me.DateTimeField(required=True, default=datetime.datetime.now)
    date_last_modified = me.DateTimeField(required=True, default=datetime.datetime.now)

    meta = {"abstract": True, "allow_inheritance": True, "db_alias": "citadel-backend"}

    """
     Override the save and other methods to auto update the date_last_modified field on every save.
    """

    def save(
        self,
        force_insert=False,
        validate=True,
        clean=True,
        write_concern=None,
        cascade=None,
        cascade_kwargs=None,
        _refs=None,
        save_condition=None,
        signal_kwargs=None,
        **kwargs,
    ):
        self.date_last_modified = datetime.datetime.now()
        super().save(
            force_insert,
            validate,
            clean,
            write_concern,
            cascade,
            cascade_kwargs,
            _refs,
            save_condition,
            signal_kwargs,
            **kwargs,
        )

    def update(self, **kwargs):
        self.date_last_modified = datetime.datetime.now()
        return super().update(**kwargs)

    def modify(self, query=None, **update):
        self.date_last_modified = datetime.datetime.now()
        return super().modify(query, **update)
