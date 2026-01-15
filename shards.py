# shards.py
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Optional
from config import DST_CLUSTERS_DIR, DST_BETA_CLUSTERS_DIR, DST_DEDICATED_SERVER_DIR, DST_DEDICATED_SERVER_EXE_DIR, STEAMCMD_DIR, BETA_BRANCH_NAME, PUBLIC_BRANCH_NAME

class Shard:
    def __init__(self, cluster: str, shard_name: str, is_beta: bool):
        self.cluster = cluster
        self.shard_name = shard_name
        self.is_beta = is_beta
        self.process: Optional[subprocess.Popen] = None
        self.exe = "./dontstarve_dedicated_server_nullrenderer_x64"

    @property
    def args(self):
        base = [
            self.exe,
            "-cluster", self.cluster,
            "-shard", self.shard_name,
        ]
        return base

    async def start(self):
        if self.process and self.process.poll() is None:
            return  # already running

        print("CWD:", DST_DEDICATED_SERVER_EXE_DIR)
        print("Command:", self.args)
        self.process = subprocess.Popen(
            self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,
            cwd=DST_DEDICATED_SERVER_EXE_DIR
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
        return DST_BETA_CLUSTERS_DIR if self.state["is_beta"] else DST_CLUSTERS_DIR

    async def start_world(self):
        # Update steamcmd first
        print("Updating steamcmd...")
        steamcmd_path = STEAMCMD_DIR / "steamcmd.sh"
        beta = BETA_BRANCH_NAME if self.state["is_beta"] else PUBLIC_BRANCH_NAME
        update_command = f"{steamcmd_path} +force_install_dir {DST_DEDICATED_SERVER_DIR} +login anonymous +app_update 343050 -beta {beta} +quit"
        steamcmd_update_process = await asyncio.create_subprocess_shell(update_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        stdout, stderr = await steamcmd_update_process.communicate()
        if steamcmd_update_process.returncode != 0:
            print(f"SteamCMD update failed: {stdout.decode()}")
            return 1


        cluster_dir = self._get_cluster_dir()
        if not cluster_dir.exists():
            raise FileNotFoundError(f"Cluster directory not found: {cluster_dir}")

        for shard_path in cluster_dir.iterdir():
            if shard_path.is_dir():
                shard_name = shard_path.name  # extract string name
                print(f"found shard: {shard_name}")
                key = f"{self.state['current_cluster']}:{shard_name}"
                shard_dir = shard_path

                shard = Shard(
                    cluster=self.state["current_cluster"],
                    shard_name=shard_name,
                    is_beta=self.state["is_beta"]
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
        master_key = f"{self.state['current_cluster']}:Master"
        if master_key in self.shards:
            self.shards[master_key].send_command(f'c_announce("{message}")')
        else:
            return

    def is_world_running(self) -> bool:
        return any(shard.is_running() for shard in self.shards.values())
