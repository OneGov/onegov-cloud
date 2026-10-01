from onegov.org.views.audit import audit_snapshot_diff


def test_audit_snapshot_diff_escapes_snapshot_and_labels() -> None:
    diff = audit_snapshot_diff(
        {'value': '<script>alert(1)</script>'},
        {'value': 'updated'},
        '<script>before</script>',
        '<script>after</script>',
    )

    assert '<script>' not in diff
    assert '&lt;script&gt;before&lt;/script&gt;' in diff
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in diff


def test_audit_snapshot_diff_only_shows_changed_fields() -> None:
    diff = audit_snapshot_diff(
        {
            'content': {'text': 'unchanged' * 1000},
            'meta': {'publication_date': '2026-09-28', 'removed': None},
        },
        {
            'content': {'text': 'unchanged' * 1000},
            'meta': {'publication_date': '2026-09-29', 'added': None},
        },
        'Before',
        'After',
    )

    assert 'unchanged' not in diff
    assert 'meta / publication_date' in diff
    assert '2026-09-28' in diff
    assert '2026-09-29' in diff
    assert 'meta / removed' in diff
    assert 'meta / added' in diff
    assert diff.count('<tr>') == 4
