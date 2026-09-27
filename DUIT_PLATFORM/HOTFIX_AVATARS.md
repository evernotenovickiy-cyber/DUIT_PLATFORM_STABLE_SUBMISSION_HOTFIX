# DUIT avatar hotfix

Fixed the verification/startup failure caused by RandomUser returning a very small response to Python download clients.

- Service photos: downloaded and cached locally.
- Demo avatars: fixed, unique, gender-matched live URLs.
- Every avatar keeps a local SVG fallback.
- Verification no longer downloads avatars.
- Media audit accepts the fixed remote gender path and still checks uniqueness and gender.
