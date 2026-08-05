# mirror-control-django

Mirror control-plane contract package for Django.

This package describes the metadata shapes Mirror uses for a Django admin
control plane. It keeps Mirror Core free of any Django dependency while still
giving Django projects a clear, typed manifest for the models they need.

## What it gives you

- a canonical list of Mirror metadata models;
- a settings fragment for Django projects;
- a plain-Python control-plane manifest that can be tested without Django.

## What it does not do

- it does not import Django at import time;
- it does not ship a dashboard UI by itself;
- it does not replace Django admin, auth, or permissions.

Django is an optional dependency for projects that want to render the control
plane as models and admin pages.
