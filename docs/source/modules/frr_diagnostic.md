# FRR Diagnostic

**STATE**: stable

**TESTS**: [frr_diagnostic](https://github.com/O-X-L/ansible-opnsense/blob/latest/tests/frr_diagnostic.yml)

**API Docs**: [Plugins - Quagga](https://docs.opnsense.org/development/api/plugins/quagga.html)

**Service Docs**: [Dynamic Routing](https://docs.opnsense.org/manual/dynamic_routing.html)

**FRR Docs**: [FRRouting](https://docs.frrouting.org/) (_make sure you are looking at the current OPNsense package version!_)

## Contribution

Thanks to [@Rath](https://github.com/superstes) for developing this module!

## Sponsoring

Thanks to [@telmich](https://github.com/telmich) for sponsoring the development of this module!

----

## Prerequisites

You need to install the FRR plugin:
```
os-frr
```

You can also install it using the [package module](https://ansible-opnsense.oxl.app/modules/package.html).

----

## Definition

For basic parameters see: [Basics](https://ansible-opnsense.oxl.app/usage/2_basic.html)

### oxlorg.opnsense.frr_diagnostic

| Parameter   | Type            | Required | Default value         | Aliases | Comment                                                                                                                                                                                                                                                                                                                                  |
|:------------|:----------------|:---------|:----------------------|:--------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| target      | string          | true     | -                     | -       | What information to query. One of: 'bgpneighbors', 'bgproute4', 'bgproute6', 'bgpsummary', 'generalroute4', 'generalroute6', 'generalrunningconfig', 'ospfdatabase', 'ospfinterface', 'ospfneighbor', 'ospfoverview', 'ospfroute', 'ospfv3database', 'ospfv3interface', 'ospfv3overview', 'ospfv3route'. See [what each one answers](#what-a-target-answers) |

----

## What a target answers

The shape differs per target, because the plugin's diagnostics controller serves
two kinds of view.

**Grid searches.** Every route and neighbour-list view is a grid, and the module
requests it as one - OPNsense names those actions `search_bgproute4`,
`search_ospfroute` and so on. They answer:

```json
{"current": 1, "rowCount": 0, "rows": [], "total": 0, "subtitle": "routerId : 10.110.3.8 , localAS : 65551"}
```

`rows` is the table, and `subtitle` is the line the GUI prints above it. The grid
targets are:

`bgproute4`, `bgproute6`, `generalroute4`, `generalroute6`, `ospfneighbor`,
`ospfroute`, `ospfv3database`, `ospfv3route`

**Everything else** passes FRR's own output through: `bgpneighbors`,
`bgpsummary`, `ospfdatabase`, `ospfinterface`, `ospfoverview`,
`ospfv3interface`, `ospfv3overview` answer FRR's JSON as the daemon produced it,
and `generalrunningconfig` answers the running configuration as text.

`bgproute`, `generalroute` and `ospfv3neighbor` used to be offered and were
removed: the plugin has no controller action for any of the three, so every call
made with one answered `{"errorMessage":"Endpoint not found"}`.

----

## Examples

### oxlorg.opnsense.frr_diagnostic

```yaml
- hosts: firewalls
  connection: local
  gather_facts: false
  module_defaults:
    group/oxlorg.opnsense.all:
      firewall: 'opnsense.template.opnsense.oxl.app'
      api_credential_file: '/home/guy/.secret/opn.key'

  tasks:
    - name: Example
      oxlorg.opnsense.frr_diagnostic:
        target: 'generalroute4'
      register: frr_info

    - name: Printing
      ansible.builtin.debug:
        var: frr_info.data
```
