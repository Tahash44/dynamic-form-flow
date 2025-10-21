from .TextFieldSerializer import TextFieldSerializer
from .SelectFieldSerializer import SelectFieldSerializer
from .CheckBoxFieldSerializer import CheckBoxFieldSerializer
from .NumberFieldSerializer import NumberFieldSerializer
from .DateFieldSerializer import DateFieldSerializer


SERIALIZER_MAP = {
    'text': TextFieldSerializer,
    'select': SelectFieldSerializer,
    'checkbox': CheckBoxFieldSerializer,
    'number': NumberFieldSerializer,
    'date': DateFieldSerializer,
}

def get_serializer_class_by_type(field_type: str):
    cls = SERIALIZER_MAP.get(field_type)
    if not cls:
        raise ValueError(f"Unknown field type: {field_type}")
    return cls
