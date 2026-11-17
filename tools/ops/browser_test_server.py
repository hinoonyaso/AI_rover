"""Isolated browser test server; never runs a real ROS adapter.

한글: 격리된 브라우저 시험 서버이며 실제 ROS 어댑터를 실행하지 않는다.
"""
import asyncio
from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from mission_routes import router
from mission_simulator import SimulationManager
from gazebo_worker import GazeboWorker


class TestGazeboWorker(GazeboWorker):
    """Save child logs only for disposable integration tests. / 격리 통합 시험에서만 하위 실행 로그를 저장한다."""

    def tick(self):
        """Capture completed child output before the parent closes it. / 하위 실행 종료 시 로그를 닫기 전에 저장한다."""
        directory = os.environ.get('MISSION_TEST_CHILD_LOG_DIR')
        if directory and self.process is not None and self.process.poll() is not None and self.output is not None:
            path = Path(directory).resolve()
            if path.is_relative_to(Path('/tmp')):
                path.mkdir(parents=True, exist_ok=True)
                data = os.pread(self.output.fileno(), 2_000_000, 0)
                (path / f'{self.mission_id}.log').write_bytes(data)
        return super().tick()


@asynccontextmanager
async def lifespan(app):
    """Own an isolated mock database for the server lifetime. / 서버 생명주기 동안 격리 모의 DB를 소유한다."""
    app.state.mission_manager = SimulationManager(Path(os.environ['MISSION_BROWSER_TEST_DB']))
    app.state.mission_allowed_port = 18765
    gazebo = TestGazeboWorker(app.state.mission_manager, auto_start=os.environ.get('MISSION_TEST_AUTO_GAZEBO') == '1')
    async def advance():
        while True:
            await asyncio.sleep(2)
            await asyncio.to_thread(app.state.mission_manager.advance_active)
            await asyncio.to_thread(gazebo.tick)
    task = asyncio.create_task(advance())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await asyncio.to_thread(gazebo.close)
        app.state.mission_manager.close()


app = FastAPI(lifespan=lifespan)
@app.get('/api/session')
def test_session():
    """Provide a disposable operator session. / 격리 시험용 운영자 세션을 제공한다."""
    return {'role': 'operator'}

app.include_router(router)
app.mount('/', StaticFiles(directory=Path(__file__).parent / 'frontend/dist', html=True), name='dashboard')
