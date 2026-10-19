from ansible.module_utils.basic import AnsibleModule


# os-frr 2.0 turned the 'area' of an OSPF/OSPFv3 interface and network into a
# relation to an area record (ModelRelationField, displayed by 'id'), where
# os-frr 1.x stored the dotted area ID itself. The modules keep speaking dotted
# IDs on both versions: reads map the UUID back, writes map the ID to the UUID.

def get_areas(settings: (dict, None)) -> dict:
    # settings: the whole 'ospf'/'ospf6' page; os-frr 1.x has no OSPFv3 areas
    if not isinstance(settings, dict):
        return {}

    areas = settings.get('areas', {})
    if not isinstance(areas, dict):
        return {}

    areas = areas.get('area', {})
    return areas if isinstance(areas, dict) else {}


def area_to_id(areas: dict, value: str) -> str:
    if value in areas:
        return areas[value]['id']

    return value


def area_to_uuid(module: AnsibleModule, areas: dict, area_id: str, area_module: str) -> str:
    for uuid, area in areas.items():
        if area['id'] == area_id:
            return uuid

    module.fail_json(f"Area '{area_id}' is not defined; create it with {area_module}")
    return ''
