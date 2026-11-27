# Contributing to TakeFerry

Run the offline tests and the rainy-door rehearsal from a clean checkout.

```sh
python3 -m unittest discover -s tests -v
python3 -m takeferry demo --output sample-run
```

For a bug, include the TakeFerry version, the operation and a synthetic shot that reproduces the problem. Replace account IDs, private media, signed links and provider receipts before opening a public issue. Security reports belong in [private vulnerability reporting](SECURITY.md).

Changes to a provider should cite its official contract and include a test that distinguishes a successful submission from a returned file and a verified native canvas node. A new drawing, clip or sound needs a source and a redistribution license. The directing skill and public documentation use English by default. Private Hermes skills stay in the writer's profile.

Contributions are distributed under the project's [Apache-2.0 license](LICENSE).
