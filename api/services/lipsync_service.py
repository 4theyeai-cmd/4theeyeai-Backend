import subprocess
import logging
import os
import stat

logger = logging.getLogger(__name__)


class LipSyncService:
    @staticmethod
    def mp3_to_wav(mp3_path: str, wav_path: str):
        try:
            logger.info(f"Converting {mp3_path} to {wav_path}")
            subprocess.run(["ffmpeg", "-y", "-i", mp3_path, wav_path], check=True)
            logger.info(f"MP3 to WAV conversion completed: {wav_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e}")
            raise
        except FileNotFoundError:
            logger.error("FFmpeg not found. Please install FFmpeg.")
            raise

    @staticmethod
    def wav_to_lipsync_json(wav_path: str, json_path: str):
        try:
            logger.info(f"Generating lipsync for {wav_path}")
            # Resolve Rhubarb executable robustly across OSes and environments
            candidates = []
            if os.name == "nt":
                candidates.append(os.path.join("bin", "rhubarb.exe"))
                # Absolute path relative to repo root (from CWD)
                candidates.append(
                    os.path.abspath(os.path.join(os.getcwd(), "bin", "rhubarb.exe"))
                )
                # Path relative to this file directory
                candidates.append(
                    os.path.abspath(
                        os.path.join(
                            os.path.dirname(__file__), "..", "..", "bin", "rhubarb.exe"
                        )
                    )
                )
            else:
                # Linux / macOS
                candidates.append(os.path.join("./bin", "rhubarb"))
                candidates.append(os.path.join("bin", "rhubarb"))
                # Absolute path relative to current working directory
                candidates.append(
                    os.path.abspath(os.path.join(os.getcwd(), "bin", "rhubarb"))
                )
                # Absolute path relative to this file directory (api/services/ -> project root)
                candidates.append(
                    os.path.abspath(
                        os.path.join(
                            os.path.dirname(__file__), "..", "..", "bin", "rhubarb"
                        )
                    )
                )

            resolved_exec = None
            for path in candidates:
                try:
                    if os.path.isfile(path):
                        resolved_exec = path
                        break
                except Exception:
                    # Ignore path errors during probing
                    pass

            if not resolved_exec:
                logger.error(f"Rhubarb executable not found. Tried: {candidates}")
                raise FileNotFoundError(
                    "Rhubarb executable not found in candidate paths"
                )

            logger.info(f"Using Rhubarb executable: {resolved_exec}")

            # Diagnostics: current process info
            try:
                logger.info(f"CWD: {os.getcwd()}")
                logger.info(f"Absolute CWD: {os.path.abspath(os.getcwd())}")
            except Exception as env_err:
                logger.warning(f"Could not get CWD: {env_err}")

            # Log file stats for rhubarb
            try:
                st_exec = os.stat(resolved_exec)
                logger.info(
                    f"rhubarb stats -> mode: {oct(st_exec.st_mode)}, size: {st_exec.st_size}, uid: {getattr(st_exec, 'st_uid', 'n/a')}, gid: {getattr(st_exec, 'st_gid', 'n/a')}"
                )
                logger.info(
                    f"access(R_OK)={os.access(resolved_exec, os.R_OK)}, access(X_OK)={os.access(resolved_exec, os.X_OK)}"
                )
            except Exception as stat_err:
                logger.warning(f"Could not stat rhubarb: {stat_err}")

            # On POSIX, ensure the binary is executable; try to chmod +x if not
            if os.name != "nt":
                try:
                    st = os.stat(resolved_exec)
                    if not (st.st_mode & stat.S_IXUSR):
                        logger.warning(
                            f"Rhubarb not executable, attempting chmod +x: {resolved_exec}"
                        )
                        os.chmod(
                            resolved_exec,
                            st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
                        )
                        logger.info("chmod +x applied successfully")
                except PermissionError as e:
                    logger.error(f"Permission error while setting executable bit: {e}")
                except Exception as e:
                    logger.warning(f"Could not adjust executable bit: {e}")

            def _run_rhubarb(exec_path: str):
                logger.info(
                    f"Executing rhubarb: '{exec_path}' -> json: '{json_path}', wav: '{wav_path}'"
                )
                return subprocess.run(
                    [
                        exec_path,
                        "-f",
                        "json",
                        "-o",
                        json_path,
                        wav_path,
                        "-r",
                        "phonetic",
                    ],
                    check=True,
                )

            try:
                _run_rhubarb(resolved_exec)
            except PermissionError as e:
                logger.error(f"Permission denied executing Rhubarb: {e}")
                # One more attempt after forcing chmod +x
                if os.name != "nt":
                    try:
                        os.chmod(resolved_exec, 0o755)
                        logger.info("Applied chmod 755 and retrying Rhubarb execution")
                        _run_rhubarb(resolved_exec)
                    except Exception as retry_err:
                        logger.error(f"Retry failed after chmod: {retry_err}")
                        raise
                else:
                    raise
            logger.info(f"Lipsync JSON created: {json_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Rhubarb error: {e}")
            raise
        except FileNotFoundError:
            logger.error("Rhubarb not found. Please install Rhubarb.")
            raise
