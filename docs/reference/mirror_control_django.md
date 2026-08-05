# mirror-control-django

The `mirror-control-django` package describes the Django control plane that sits
on top of Mirror Core.

## Public helpers

- `default_control_plane_spec()`
- `render_django_settings_fragment()`
- `ensure_django_available()`

## What the spec contains

- the Django app label;
- the Django admin site name;
- the installed apps Mirror expects;
- the metadata models the control plane needs.

## Example

```python
from mirror_control_django import default_control_plane_spec, render_django_settings_fragment

spec = default_control_plane_spec()
print(spec.model_names())
print(render_django_settings_fragment(spec))
```
