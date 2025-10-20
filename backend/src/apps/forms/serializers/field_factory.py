from . import TextFieldSerializer
from . import SelectFieldSerializer
from . import CheckBoxFieldSerializer
from . import NumberFieldSerializer
from . import DateFieldSerializer

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
