# shards.py
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Optional

class Shard:
    def __init__(self, cluster: str, shard_name: str, is_beta: bool, server_dir: Path):
        self.cluster = cluster
        self.shard_name = shard_name
        self.is_beta = is_beta
        self.server_dir = server_dir
        self.process: Optional[subprocess.Popen] = None
        self.exe = "dontstarve_dedicated_server_nullrenderer_x64"  # adjust if needed

    @property
    def args(self):
        base = [
            self.exe,
            "-cluster", self.cluster,
            "-shard", self.shard_name,
            "-persistent_storage_root", str(self.server_dir.parent.parent),
            "-conf_dir", "DoNotStarveTogether" if not self.is_beta else "DoNotStarveTogetherBetaBranch",
            "-backup_logs",
        ]
        return base

    async def start(self):
        if self.process and self.process.poll() is None:
            return  # already running

        self.process = subprocess.Popen(
            self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,
            cwd=str(self.server_dir)
        )
        print(f"Started {self.shard_name} shard for {self.cluster} (beta={self.is_beta})")

    async def stop(self, graceful=True):
        if not self.process or self.process.poll() is not None:
            return

        if graceful and self.process.stdin:
            try:
                self.process.stdin.write("c_shutdown()\n")
                self.process.stdin.flush()
                await asyncio.sleep(10)  # give players time
            except Exception:
                pass

        self.process.terminate()
        try:
            await asyncio.to_thread(self.process.wait, timeout=15)
        except subprocess.TimeoutExpired:
            self.process.kill()
            await asyncio.to_thread(self.process.wait)

        print(f"Stopped {self.shard_name} shard")

    def send_command(self, command: str):
        if self.process and self.process.stdin and self.process.poll() is None:
            try:
                self.process.stdin.write(command + "\n")
                self.process.stdin.flush()
            except BrokenPipeError:
                print("Broken pipe – shard probably dead")

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None


class ShardManager:
    def __init__(self, state: dict, server_base_dir: Path):
        self.state = state
        self.base_dir = server_base_dir
        self.shards: Dict[str, Shard] = {}  # key: "cluster:shard_name"

    def _get_cluster_dir(self):
        conf_dir = "DoNotStarveTogetherBetaBranch" if self.state["is_beta"] else "DoNotStarveTogether"
        return self.base_dir / conf_dir / self.state["current_cluster"]

    async def start_world(self):
        cluster_dir = self._get_cluster_dir()
        if not cluster_dir.exists():
            raise FileNotFoundError(f"Cluster directory not found: {cluster_dir}")

        # Usually Master + Caves
        for shard_name in ["Master", "Caves"]:
            key = f"{self.state['current_cluster']}:{shard_name}"
            shard_dir = cluster_dir / shard_name
            if not shard_dir.exists():
                continue  # e.g. single-shard world

            shard = Shard(
                cluster=self.state["current_cluster"],
                shard_name=shard_name,
                is_beta=self.state["is_beta"],
                server_dir=shard_dir,
            )
            await shard.start()
            self.shards[key] = shard

    async def stop_world(self, graceful=True):
        tasks = [shard.stop(graceful=graceful) for shard in self.shards.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        self.shards.clear()

    async def restart_world(self, graceful=True):
        await self.stop_world(graceful=graceful)
        await asyncio.sleep(5)
        await self.start_world()

    def send_announce(self, message: str):
        # Most commands only need to go to Master
        master_key = f"{self.state['current_cluster']}:Master"
        if master_key in self.shards:
            self.shards[master_key].send_command(f'c_announce("{message}")')

    def is_world_running(self) -> bool:
        return any(shard.is_running() for shard in self.shards.values())
