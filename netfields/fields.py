import re
from django.db import models

from netfields.managers import NET_OPERATORS, NET_TEXT_OPERATORS
from netfields.forms import NetAddressFormField, MACAddressFormField

ipv4_addr_re = re.compile("^([0-9]{1,3}.){3}[0-9]{1,3}$")


class _NetAddressField(models.Field):
    empty_strings_allowed = False

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = self.max_length
        super(_NetAddressField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            return value
        # this is a bit naive, given that the ipaddr field will actually accept
        # a bunch of different things... But we'll live with that for now.
        if not ipv4_addr_re.match(value):
            raise ValueError("invalid IPv4 address: %r" %(value, ))
        return value

    def get_prep_lookup(self, lookup_type, value):
        if not value:
            return None

        if (lookup_type in NET_OPERATORS and
                NET_OPERATORS[lookup_type] not in NET_TEXT_OPERATORS):
            return self.get_prep_value(value)

        return super(_NetAddressField, self).get_prep_lookup(
            lookup_type, value)

    def get_prep_value(self, value):
        if not value:
            return None

        return unicode(self.to_python(value))

    def get_db_prep_lookup(self, lookup_type, value, connection,
            prepared=False):
        if not value:
            return []

        if (lookup_type in NET_OPERATORS and
                NET_OPERATORS[lookup_type] not in NET_TEXT_OPERATORS):
            return [value] if prepared else [self.get_prep_value(value)]

        return super(_NetAddressField, self).get_db_prep_lookup(
            lookup_type, value, connection=connection, prepared=prepared)

    def formfield(self, **kwargs):
        defaults = {'form_class': NetAddressFormField}
        defaults.update(kwargs)
        return super(_NetAddressField, self).formfield(**defaults)


class InetAddressField(_NetAddressField):
    description = "PostgreSQL INET field"
    max_length = 39
    __metaclass__ = models.SubfieldBase

    def db_type(self, connection):
        return 'inet'


class CidrAddressField(_NetAddressField):
    description = "PostgreSQL CIDR field"
    max_length = 43
    __metaclass__ = models.SubfieldBase

    def db_type(self, connection):
        return 'cidr'


class MACAddressField(models.Field):
    description = "PostgreSQL MACADDR field"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 17
        super(MACAddressField, self).__init__(*args, **kwargs)

    def db_type(self, connection):
        return 'macaddr'

    def formfield(self, **kwargs):
        defaults = {'form_class': MACAddressFormField}
        defaults.update(kwargs)
        return super(MACAddressField, self).formfield(**defaults)
