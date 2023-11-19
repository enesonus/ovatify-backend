from typing import Tuple, List
from django.db.models import Model


def bulk_get_or_create(model: Model, data: List, unique_field: str) -> Tuple[List[Model], List[Model]]:
    # Step 1: Fetch existing records
    existing_records = model.objects.filter(**{f"{unique_field}__in": data})

    # Create a set of existing values for quick look-up
    existing_values = {getattr(record, unique_field) for record in existing_records}

    # Step 2: Determine new records
    new_records_data = [value for value in data if value not in existing_values]

    # Create new model instances
    new_records = [model(**{unique_field: value}) for value in new_records_data]

    # Step 3: Bulk create new records
    model.objects.bulk_create(new_records)

    # Step 4: Combine existing and new records
    return existing_records, new_records

