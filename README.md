# TinyTrash update policy

This repository publishes only TinyTrash's public update configuration and schema. Do not put credentials, identifiers for users, schedules, or private application source here. Configure GitHub Pages to deploy through GitHub Actions, and require the validation job on pull requests to `main`.

The initial `version.json` disables both platforms. Before first publication, set `issued_at` to the current UTC time and `expires_at` to no more than seven days later. Run:

```sh
python3 validate.py version.json
python3 validate.py version.json --previous previous-version.json
```

The validator uses Python's standard library. It rejects unknown/missing/duplicate keys, invalid UTF-8, documents over 32 KiB, incorrect app/schema IDs, invalid values and dates, expired/future policies, and lifetimes over seven days. The schema describes structural constraints; the validator also enforces constraints JSON Schema cannot express. Changed documents require a strictly increasing revision; never lower the revision to roll back a setting. CI validates before deploying only the policy and schema.

## Publish and verify

1. Confirm the dedicated owner/repository, public visibility and Pages Actions source. Publish both OS policies disabled first.
2. After deployment, fetch `https://aniyomesan.github.io/tinytrash-version-info/version.json` anonymously over HTTPS. Verify the body, revision, app ID, expiry, both disabled values and size. Deployment success alone is insufficient.
3. Record the dated endpoint verification for the app's distribution audit. The app must ship with `UPDATE_CHECK_ENABLED=true` and the exact approved URL, independently of monetization.
4. Inspect and renew the policy at least 48 hours before expiry. Continuing enforcement requires a new revision and new valid dates. No renewal means automatic expiry.

## Later enforcement

First publish the new app version to the stores. Verify that every affected country/device/OS can obtain that minimum version/build; Android must be at 100% production rollout. Do not require a version available only in review, TestFlight/internal testing or an incompatible OS. Capture dated reachability evidence, reason, old/new minimums, owner and recovery JSON in the PR. This evidence is needed when enabling enforcement, not for an initial app build using a disabled remote policy.

## Emergency disable

Set the affected OS `enabled` to `false`, increase `revision`, renew both dates, validate and deploy. Do not simply revert an old commit or delete the endpoint. Verify the served JSON anonymously, then verify an old app unlocks with “再確認”. A lower revision is ignored by clients. Network/CDN outages can delay recovery; clients fail open when their six-hour cache or policy expiry is reached. This is not a guarantee of immediate remote recovery.
