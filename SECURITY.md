# Security reports

Use GitHub's [private vulnerability report form](https://github.com/Tsunami1212/takeferry/security/advisories/new). Include the version, affected tool and a reproduction using sample data. Keep account tokens, OAuth sessions, private scripts and signed video URLs out of the report.

The bridge is a local stdio process. Its credentials come from the official provider clients, and its state directory contains private shot history. Configure it inside a Hermes profile that you trust with those accounts.
