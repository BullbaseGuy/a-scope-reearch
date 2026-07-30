from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding='utf-8'))
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(f'cannot load {path}: {exc}') from exc
    if not isinstance(value, dict):
        raise ConfigError(f'{path} must contain an object')
    return value


@dataclass(frozen=True)
class Settings:
    root: Path
    account: dict[str, Any]
    providers: dict[str, Any]
    screening: dict[str, Any]
    archetypes: dict[str, Any]


def load_settings(root: Path = Path('.')) -> Settings:
    root = root.resolve()
    account = load_yaml(root / 'config/account_policy.yaml')
    providers = load_yaml(root / 'config/provider_policy.yaml')
    screening = load_yaml(root / 'config/screening.yaml')
    archetypes = load_yaml(root / 'config/archetypes.yaml')
    for name, raw in [('account', account), ('providers', providers), ('screening', screening), ('archetypes', archetypes)]:
        if raw.get('schema_version') != 1:
            raise ConfigError(f'{name} has unsupported schema_version')
    if account.get('account') != 'SATELLITE':
        raise ConfigError('only SATELLITE account is supported')
    if account.get('margin_leverage_allowed') is not False:
        raise ConfigError('margin leverage must remain disabled')
    if account.get('automatic_trading') is not False:
        raise ConfigError('automatic trading must remain disabled')
    if account.get('st_executable_allowed') is not False:
        raise ConfigError('ST/*ST must not enter the executable pool')
    if providers.get('providers', {}).get('security_master', {}).get('primary') != 'CNINFO_BULK':
        raise ConfigError('security master primary must remain CNINFO_BULK')
    return Settings(root=root, account=account, providers=providers, screening=screening, archetypes=archetypes)
