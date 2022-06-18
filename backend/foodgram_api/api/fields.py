from base64 import b64decode
import binascii
import re

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.fields import ImageField as RestFrameworkImageField
from rest_framework.settings import api_settings


class ImageField(RestFrameworkImageField):
    def to_internal_value(self, data):
        match = re.match(
            (
                r'^data:(?P<content_type>image\/(?P<extension>[a-z]+));'
                r'base64,(?P<content>[A-Za-z0-9+\/]+.{2})$'
            ), data
        )
        if not match:
            self.fail('invalid')
        try:
            data = SimpleUploadedFile(
                name=f'image.{match.group("extension")}',
                content=b64decode(match.group('content')),
                content_type=match.group('content_type')
            )
        except binascii.Error:
            self.fail('invalid')
        return super().to_internal_value(data)

    def to_representation(self, value):
        if not value:
            return None
        use_url = getattr(self, 'use_url', api_settings.UPLOADED_FILES_USE_URL)
        if use_url:
            try:
                return value.url
            except AttributeError:
                return None
        return value.name
