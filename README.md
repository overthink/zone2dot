# Route 53 zone to DOT

Render an AWS Route 53 zone description as [DOT](), for pretty rendering by [graphviz]().

## Usage

```bash
aws route53 list-resource-record-sets --hosted-zone-id ZONE_ID \
  | python zone2dot.py \
  | xdot
```

## Status

Works on the tiny subset of zones I've seen. If you have an interesting zone
that doesn't work well, please submit an issue with the zone JSON (anonymized,
if you care) attached.

## TODO

* tests
* lint
* prettier output

