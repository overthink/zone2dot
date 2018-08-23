# Route 53 zone to DOT

Render an AWS Route 53 zone description as [DOT](), for pretty rendering by [graphviz]().

## Usage

```bash
zone2dot example.com | xdot -
```

## Requirements

* Just Python 2 if you invoke like `python zone2dot.py myzone.json`
* `awscli` and `jq` if you use the `zone2dot` wrapper script
* `xdot` or some other DOT viewer ([this](https://beta.observablehq.com/@mbostock/graph-o-matic)
  is very handy for in-browser rendering)

## Status

Works on the tiny subset of zones I've seen. If you have an interesting zone
that doesn't work well, please submit an issue with the zone JSON (anonymized,
if you care) attached.
 
## Development

* Run `make` to run the linter and make sure it's clean

## TODO

* CNAMEs need thought
* tests
* prettier output

