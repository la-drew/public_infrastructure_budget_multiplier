# Security policy

## Supported versions

The latest release on the default branch receives security updates.

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Use GitHub's **Security → Report a vulnerability** flow for the repository. Include reproduction steps, impact, and any suggested mitigation. Maintainers should acknowledge a report within seven days.

The default application binds to `127.0.0.1`. It has no authentication and is not intended to be exposed directly to the public internet. Put a production deployment behind a maintained reverse proxy, TLS, authentication where appropriate, request limits, logging, and an organizational security review.

