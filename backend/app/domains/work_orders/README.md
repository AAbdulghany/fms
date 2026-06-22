# Work orders domain

Split by concern (NT-CLEAN-21):

| Module | Responsibility |
|--------|----------------|
| `_common.py` | Helpers, role deps, PDF sync |
| `crud.py` | List, create, get, patch, assign |
| `requests.py` | Client request / approve / decline |
| `reports.py` | Maintenance report draft & submit |
| `collaboration.py` | History, comments, documents |
| `router.py` | Aggregates routes + test re-exports |

`api/routes/work_orders.py` re-exports all public handlers.
