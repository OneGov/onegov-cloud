#!/usr/bin/env python

from __future__ import annotations

import click
import shlex
import subprocess
import time
import yaml

from collections.abc import Sequence

schedule_config_file = 'maintenance-schedule.yml'


def parse_schedule_config(cfg: str) -> list[tuple[str, list[str]]]:
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
@click.option('--select', multiple=True)
@click.option('--unselect', multiple=True)
def schedule_rollout_announcements(
    dry_run: bool,
    select: Sequence[str] = (),
    unselect: Sequence[str] = (),
) -> None:
    """
    Schedule regularly by-weekly rollout announcements in a semi-automatic
    way. Read the configuration, execute the announcement
    and manually confirm with y/n for each server.

    :param dry_run: run the command without actually scheduling the
    announcements and sending out emails\n
    :param select: only schedule announcements for the specified nodes\n
    :param unselect: schedule announcements for all nodes except the
    specified ones

    Examples:\n
      python3 do/schedule-rollout-announcements.py --help\n
      python3 do/schedule-rollout-announcements.py --dry-run\n
      python3 do/schedule-rollout-announcements.py\n
      python3 do/schedule-rollout-announcements.py --select A --select B\n
      python3 do/schedule-rollout-announcements.py --unselect C --unselect D\n
    """

    try:
        with open(schedule_config_file) as f:
            schedule_config = f.read()
    except FileNotFoundError:
        click.echo(f'Error: schedule configuration file '
                   f'"{schedule_config_file}" not found.')
        return

    try:
        parsed = parse_schedule_config(schedule_config)
    except Exception as e:
        click.echo(f'Invalid schedule configuration: {e}')
        return

    if select and unselect:
        click.echo('Error: --select and --unselect options cannot be '
                   'used together.')
        return

    if select:
        selected: list[tuple[str, list[str]]] = []
        for date_string, nodes in parsed:
            selected_nodes = [n for n in nodes if n in select]
            if selected_nodes:
                selected.append((date_string, selected_nodes))
        parsed = selected

    if unselect:
        unselected: list[tuple[str, list[str]]] = []
        for date_string, nodes in parsed:
            unselected_nodes = [n for n in nodes if n not in unselect]
            if unselected_nodes:
                unselected.append((date_string, unselected_nodes))
        parsed = unselected

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
