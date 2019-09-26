from sqlalchemy.orm import class_mapper, ColumnProperty


def model_to_json(model, parse_models, ignore_field_names=None):
    if ignore_field_names is None:
        ignore_field_names = []

    data = []
    field_names = [prop.key for prop in class_mapper(model).iterate_properties if isinstance(prop, ColumnProperty)]

    for parse_model in parse_models:
        tmp_dict = {}
        for field_name in field_names:
            if field_name not in ignore_field_names:
                tmp_dict[field_name] = getattr(parse_model, field_name) if str(getattr(parse_model, field_name)) else None
        data.append(tmp_dict)

    return data
