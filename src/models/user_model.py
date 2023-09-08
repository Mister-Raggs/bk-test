from enum import Enum
import mongoengine as me
from mongoengine.queryset.visitor import Q
from flask_login import UserMixin
from flask_login import LoginManager
from models.base_model import BaseModel
from models.company_model import CompanyModel
from common import constants, utils

login_manager = LoginManager()


class UserSalutationTypes(str, Enum):
    Mr = "Mr."
    Miss = "Miss."
    Mrs = "Mrs."
    Dr = "Dr."


class UserType(str, Enum):
    AARK_GLOBAL = "AARK_GLOBAL"  # AARK global user
    CLIENT = "CLIENT"  # Client user


class UserRole(str, Enum):
    ADMIN = "ADMIN"  # AARK global admin user
    NORMAL = "NORMAL"  # AARK global normal user
    CLIENT_ADMIN = "CLIENT_ADMIN"  # Client admin user
    CLIENT_NORMAL = "CLIENT_NORMAL"  # Client normal user


class UserModel(BaseModel, UserMixin):
    salutation = me.EnumField(UserSalutationTypes, required=True, default=UserSalutationTypes.Mr)
    first_name = me.StringField(required=True)
    middle_name = me.StringField()
    last_name = me.StringField(required=True)
    email = me.EmailField(required=True, unique=True)
    password = me.StringField(required=True)
    user_type = me.EnumField(UserType, required=True, default=UserType.CLIENT)
    company = me.ReferenceField(CompanyModel, required=True)
    is_active = me.BooleanField(required=True, default=True)
    is_deleted = me.BooleanField(required=True, default=False)
    roles = me.ListField(me.EnumField(UserRole, default=UserRole.CLIENT_NORMAL), required=True)

    meta = {
        "db_alias": constants.MONGODB_CONN_ALIAS,
        "collection": "users",
        "indexes": [
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "company",
        ],
    }

    def __repr__(self):
        return f"{self.email}"

    def __str__(self):
        return (
            "UserModel("
            + f"_id='{str(self.pk)}'"
            + f", email='{self.email}'"
            + f", password='masked(******)'"
            + f", user_type='{self.user_type}'"
            + f", is_active='{self.is_active}'"
            + f", is_deleted='{self.is_deleted}'"
            + f", roles='{self.roles}'"
            + ")"
        )


@login_manager.user_loader
def user_loader(id):
    return UserModel.objects(id=id).first()


@login_manager.request_loader
def request_loader(request):
    email = request.form.get("email")
    # user can login using username or email
    user = UserModel.objects(Q(email=email)).first()
    return user if user else None


def get_user_by_email(email) -> UserModel:
    user = UserModel.objects(Q(email=email)).first()
    return user if user else None


def verify_user_password(provided_password, stored_password):
    """Verify a stored password against one provided by user"""

    # TODO: hash the password and avoid plain strings

    # stored_password = stored_password.decode('ascii')
    # salt = stored_password[:64]
    # stored_password = stored_password[64:]
    # pwdhash = hashlib.pbkdf2_hmac('sha512',
    #                               provided_password.encode('utf-8'),
    #                               salt.encode('ascii'),
    #                               100000)
    # pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    # return pwdhash == stored_password
    return provided_password == stored_password


def check_user_exists_by_email(email, row_id):
    user = None
    # if row_id is present its an update request
    if utils.string_is_not_empty(row_id):
        user = UserModel.objects(Q(email=email) & Q(id__ne=row_id)).first()
    else:
        # its an add new request
        user = UserModel.objects(email=email).first()

    return True if user else False
