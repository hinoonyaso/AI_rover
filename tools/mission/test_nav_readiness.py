"""Check that test readiness includes both managers. / 두 관리자의 준비 완료 조건을 시험한다."""
from test_dashboard_gazebo import nav_log_ready


def test_requires_localization_and_navigation():
    """One manager alone must not declare Nav2 ready. / 한 관리자만 준비되면 Nav2 준비로 보지 않는다."""
    local = '[lifecycle_manager_localization]: Managed nodes are active'
    nav = '[lifecycle_manager_navigation]: Managed nodes are active'
    assert not nav_log_ready('')
    assert not nav_log_ready(local)
    assert not nav_log_ready(nav)
    assert not nav_log_ready(local + '\n[lifecycle_manager_navigation]: Starting')
    assert nav_log_ready(local + '\n' + nav)
