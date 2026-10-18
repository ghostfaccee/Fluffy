# Fluffy | Testing

**Before running the tests, it is recommended to launch the corresponding Docker profile.**
```
docker compose --profile test up -d
```

To run the full suite of tests, use the following commands:
```
docker compose --profile test exec testapi pytest
# or (for a detailed output)
docker compose --profile test exec testapi pytest -v
```

Tests in this project are divided into unit, integration, and e2e tests.

To run tests of a specific type, use the following commands:
```
docker compose --profile test exec testapi pytest -m unit|intgration|e2e 
```

