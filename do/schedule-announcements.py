#!/usr/bin/env python

from __future__ import annotations

import subprocess
import time
import shlex
import click
import yaml


schedule_config = """
schedule:
  - date: Next Tuesday at 12:00
    nodes:
      - loxo
      - pherusa
      - tyche
  - date: Next Tuesday at 14:00
    nodes:
      - aether
      - alecto
      - theros
      - arete
      - calais
  - date: Next Tuesday at 15:00
    nodes:
      - caicias
      - caicinus
      - caicus
      - carcinus
  - date: Next Monday +7 days at 7:00
    nodes:
      - ister
      - istrus
"""


def parse_schedule_config(cfg: str):
    """Parse and validate the YAML schedule configuration.

    Returns a list of (date, nodes) tuples. Raises ValueError on invalid
    configuration.
    """
    data = yaml.safe_load(cfg)

    if not isinstance(data, dict):
        raise TypeError('configuration must be a YAML mapping at top level')

    if 'schedule' not in data:
        raise ValueError("missing top-level 'schedule' key")

    schedule = data['schedule']
    if not isinstance(schedule, list):
        raise TypeError("'schedule' must be a list")

    out = []
    for idx, item in enumerate(schedule):
        if not isinstance(item, dict):
            raise TypeError(f'schedule item {idx} must be a mapping')

        date = item.get('date')
        nodes = item.get('nodes')

        if not isinstance(date, str):
            raise TypeError(
                f"schedule item {idx} missing or invalid 'date' string")

        if (not isinstance(nodes, list) or
                not all(isinstance(n, str) for n in nodes)):
            raise TypeError(
                f"schedule item {idx} 'nodes' must be a list of strings")

        out.append((date, nodes))

    return out


def schedule_announcement(date_string, node, dry_run):
    # Inform about the scheduling action
    click.secho(
        f"\nScheduling maintenance for {node} on {date_string} "
        f"{'(DRY-RUN)' if dry_run else ''}", fg='cyan')
    time.sleep(2)

    cmd = [
        'puppeteer', 'schedule-maintenance',
        '--node', str(node),
        '--time', str(date_string),
        '--send-mail',
    ]
    if dry_run:
        cmd.append('--dry-run')

    quoted = ' '.join(shlex.quote(str(p)) for p in cmd)
    click.secho(f'Command: {quoted}\n', fg='yellow')

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.secho(f'Error scheduling announcement for {node} '
                    f'on {date_string}: {e}\n', fg='red')


@click.command()
@click.option('--dry-run', is_flag=True, default=False)
def schedule_rollout_announcements(dry_run: bool) -> None:
    """
    Schedule regularly by-weekly rollout announcements in a semi-automatic
    way. Read the configuration, execute the announcement
    and manually confirm with y/n for each server.

    :param dry_run: run the command without actually scheduling the
    announcements and sending out emails

    Examples:
      python3 do/schedule-rollout-announcements.py --help
      python3 do/schedule-rollout-announcements.py --dry-run
      python3 do/schedule-rollout-announcements.py
    """

    try:
        parsed = parse_schedule_config(schedule_config)
    except Exception as e:
        click.echo(f'Invalid schedule configuration: {e}')
        return

    click.secho('Summary of scheduled announcements:', fg='cyan')
    for date_string, nodes in parsed:
        click.echo(f'Scheduling announcements for {date_string} on nodes: '
                   f'{', '.join(nodes)}')

    if not click.confirm('\nMake sure VPN is active or you are in the office'):
        return

    click.echo()
    for date_string, nodes in parsed:
        for node in nodes:
            schedule_announcement(date_string, node, dry_run)


if __name__ == '__main__':
    schedule_rollout_announcements()
