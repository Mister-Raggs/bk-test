from enum import Enum
import mongoengine as me
from mongoengine.queryset.visitor import Q
from models.base_model import BaseModel
from common import constants, utils


class ContactNumberType(str, Enum):
    TELEPHONE_1 = "TELEPHONE_1"
    TELEPHONE_2 = "TELEPHONE_2"
    MOBILE_1 = "MOBILE_1"
    MOBILE_2 = "MOBILE_2"
    MOBILE_3 = "MOBILE_3"


class AddressCountry(str, Enum):
    US = "USA"
    CA = "Canada"


class ContactNumber(me.EmbeddedDocument):
    number = me.StringField(required=True)
    type = me.EnumField(ContactNumberType, required=True, default=ContactNumberType.MOBILE_1)


class CompanyAddress(me.EmbeddedDocument):
    street_name_line_1 = me.StringField(required=True)
    street_name_line_2 = me.StringField()
    address_city = me.StringField(required=True)
    address_country = me.EnumField(AddressCountry, required=True)
    address_state = me.StringField(required=True)
    address_zip = me.StringField(required=True)


class CompanyModel(BaseModel):
    full_name = me.StringField(required=True)
    short_name = me.StringField(required=True)
    address = me.EmbeddedDocumentField(CompanyAddress, required=True)
    contact_numbers = me.ListField(me.EmbeddedDocumentField(ContactNumber))
    is_active = me.BooleanField(required=True, default=True)
    is_deleted = me.BooleanField(required=True, default=False)

    meta = {
        "collection": "companies",
        "db_alias": constants.MONGODB_CONN_ALIAS,
        "indexes": [
            "full_name",
            "short_name",
            "address.address_city",
            "address.address_state",
            "address.address_country",
            "address.address_zip",
        ],
    }

    def __repr__(self):
        return f"{self.full_name}"

    def __str__(self):
        return (
            "CompanyModel("
            + f"_id='{str(self.pk)}'"
            + f", full_name='{self.full_name}'"
            + f", short_name='{self.short_name}'"
            + f", address='{self.address}'"
            + f", contact_numbers='{', '.join([str(elem) for elem in self.contact_numbers])}'"
            + f", is_active='{self.is_active}'"
            + f", is_deleted='{self.is_deleted}'"
            + ")"
        )


def check_company_exists_by_full_name(full_name, row_id):
    company = None
    # if row_id is present its an update request
    if utils.string_is_not_empty(row_id):
        company = CompanyModel.objects(Q(full_name=full_name) & Q(id__ne=row_id)).first()
    else:
        # its an add new request
        company = CompanyModel.objects(full_name=full_name).first()

    return True if company else False
