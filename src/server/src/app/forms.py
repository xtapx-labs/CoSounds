from django_file_form.model_admin import FileFormAdmin
from django_file_form.forms import FileFormMixin, UploadedFileField
from django.forms import ModelForm
from app.widgets import AudioUploadWidget
from app.models import Sound


class SoundForm(FileFormMixin, ModelForm):
    audio = UploadedFileField(widget=AudioUploadWidget)

    class Meta:
        model = Sound
        fields = ["audio", "title", "artist", "type"]

    readonly_fields = ["timestamp"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, s3_upload_dir="sounds", **kwargs)
