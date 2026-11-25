def declared_only(instance) -> None:
    # A GeneralModule posts every field in FIELDS_ALL, and a field the caller
    # did not declare goes out as '' or as the argument's default - writing over
    # whatever the appliance holds (unbound_general's dns64_prefix). Arguments
    # default to None here; a None is neither compared nor posted, and
    # ApiMutableModelControllerBase::setAction leaves an unposted field alone.
    undeclared = [f for f in instance.FIELDS_ALL if instance.p.get(f) is None]

    for field in undeclared:
        instance.p.pop(field, None)

    instance.FIELDS_ALL = [f for f in instance.FIELDS_ALL if f not in undeclared]
    instance.FIELDS_CHANGE = [f for f in instance.FIELDS_CHANGE if f not in undeclared]
