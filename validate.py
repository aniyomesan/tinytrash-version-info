#!/usr/bin/env python3
"""Validate TinyTrash schema v1 and deployment freshness using the standard library."""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re

APP_ID = 'com.ursastack.tinytrash'
VERSION = r'(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})'
BUILD = r'[1-9][0-9]{0,9}'


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _keys(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError('missing or unknown keys')


def _timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z', value):
        raise ValueError('strict UTC timestamp required')
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


def validate_policy(body: str, now: datetime, *, check_freshness=True) -> list[str]:
    try:
        if len(body.encode('utf-8')) > 32768:
            raise ValueError('body exceeds 32 KiB')
        data = json.loads(body, object_pairs_hook=_object,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError('non-JSON number')))
        _keys(data, ['schema_version', 'app_id', 'revision', 'issued_at', 'expires_at', 'platforms'])
        if type(data['schema_version']) is not int or data['schema_version'] != 1:
            raise ValueError('unsupported schema')
        if data['app_id'] != APP_ID:
            raise ValueError('wrong app ID')
        if type(data['revision']) is not int or not 1 <= data['revision'] <= 2147483647:
            raise ValueError('invalid revision')
        issued, expires = _timestamp(data['issued_at']), _timestamp(data['expires_at'])
        if not issued < expires <= issued + timedelta(days=7):
            raise ValueError('invalid policy lifetime')
        if check_freshness and (issued > now + timedelta(minutes=5) or now >= expires):
            raise ValueError('expired or future policy')
        _keys(data['platforms'], ['ios', 'android'])
        for policy in data['platforms'].values():
            _keys(policy, ['enabled', 'minimum_version', 'minimum_build'])
            if type(policy['enabled']) is not bool:
                raise ValueError('enabled must be boolean')
            version, build = policy['minimum_version'], policy['minimum_build']
            if not isinstance(version, str) or not re.fullmatch(VERSION, version):
                raise ValueError('invalid minimum version')
            if not isinstance(build, str) or not re.fullmatch(BUILD, build) or int(build) > 2147483647:
                raise ValueError('invalid minimum build')
        return []
    except (ValueError, TypeError, UnicodeError, OverflowError, RecursionError) as error:
        return [str(error)]


def revision_errors(body: str, previous: str) -> list[str]:
    try:
        current = json.loads(body, object_pairs_hook=_object)
        old = json.loads(previous, object_pairs_hook=_object)
        if current != old and current['revision'] <= old['revision']:
            return ['changed document must increase revision; publish rollback as a new revision']
        return []
    except (ValueError, TypeError, KeyError) as error:
        return ['invalid revision history: ' + str(error)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('policy', type=Path)
    parser.add_argument('--previous', type=Path)
    args = parser.parse_args()
    try:
        raw = args.policy.read_bytes()
        if len(raw) > 32768:
            raise ValueError('body exceeds 32 KiB')
        body = raw.decode('utf-8')
        errors = validate_policy(body, datetime.now(timezone.utc))
        if not errors and args.previous:
            errors += revision_errors(body, args.previous.read_text(encoding='utf-8'))
    except (OSError, ValueError, UnicodeError) as error:
        errors = [str(error)]
    for error in errors:
        print('Invalid policy: ' + error)
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
